#!/usr/bin/env python3

import logging
from pathlib import Path
from argparse import ArgumentParser
from typing import List, Dict, Any, Tuple
from itertools import product
from typing import Optional
import json
import numpy as np
import os, shutil
from rpl_wei import WEI

from tools.plate_color_analysis import get_colors_from_file
from tools.threadReturn import ThreadWithReturnValue
from evolutionary_solver import EvolutionaryColorSolver
from funcx import FuncXExecutor

curr_wells_used = []

def wei_run_flow(wf_file_path, payload):
    wei_client = WEI(wf_file_path)
    run_info = wei_client.run_workflow(payload=payload)
    print(run_info)
    return run_info

def run(
    target_color: List[float],
    wei_client: Optional["WEI"] = None,
    solver: EvolutionaryColorSolver = EvolutionaryColorSolver,
    exp_budget: int = 96 * 3,
    pop_size: int = 96,
    init_protocol = None,
    loop_protocol = None,
    final_protocol = None,
    solver_out_dim: Tuple[int, int] = (96, 3),
    plate_max_volume: float = 275.0,
    exp_label: str = "",
    exp_path: str = ""
) -> None:
    """
    Steps
    1. random init
    2. run flow with init
    2. grade population
    do
        1. update population
        2. run workflow with this payload
        3. grade population
    while num_exps < threshhold and solution not found
    """
    
    show_visuals = True 
    num_exps = 0
    current_plate = None
    plate_n=1
    plate_total = int(exp_budget/96)
    current_iter = 0 
    cur_best_color = None
    cur_best_diff = float("inf")
    runs_list = []
    new_plate=True
    payload={}
    img_path = None
    #home = Path(os.path.expanduser('~'))
    #print(home)
    print(exp_path)
    exp_path =  Path(exp_path)
    #exp_path = home/exp_path
    print(exp_path)
    exp_label = Path(exp_label)
    exp_folder = exp_path / exp_label
    
    if not (os.path.isdir(exp_path)):
        os.makedirs(exp_path)
        print("makingdir")
    if not (os.path.isdir(exp_folder)):
        os.mkdir(exp_folder)
    if not (os.path.isdir(exp_folder/"results")):
        os.mkdir(exp_folder/"results") 

    def publish_iter():
        #gather some shit and transfer it to the exp
        pass

    while num_exps + pop_size <= exp_budget:
        
        print(
            "Starting experiment, can run at least one iteration:",
            num_exps + pop_size <= exp_budget,
        )

        print('Starting iteration ' + str(current_iter))
        publish_iter()

        #grab new plate if experiment starting or current plate is full
        if new_plate or current_iter==0:
            print('Grabbing New Plate')
            iter_thread=ThreadWithReturnValue(target=wei_run_flow,kwargs={'wf_file_path':init_protocol,'payload':payload})
            iter_thread.run()
            
            if current_iter > 0:
               filename = "plate_"+ str(plate_n)
               shutil.copy2(run_info["run_dir"]/ "results"/"final_image.jpg",  (exp_folder/"results"/filename))
               print("incrementing plate n!!!!")
               plate_n = plate_n + 1
            curr_wells_used = []
            new_plate = False

        # Calculate volumes and current wells for creating the OT2 protocol
        ## FUNCX
        plate_volumes = solver.run_iteration( 
            target_color,
            current_plate,
            out_dim=(pop_size, 3),
            pop_size=pop_size,
            return_volumes=True,
            return_max_volume=plate_max_volume,
        )
        target_plate = [
                (np.asarray(elem) / 275).tolist() for elem in plate_volumes
            ]
        payload = convert_volumes_to_payload(plate_volumes)
        
        #resets OT2 resources (or not)
        if current_iter == 0: 
            payload['use_existing_resources'] = False # This assumes the whole plate was reset and all tips are new
        else: 
            payload['use_existing_resources'] = True 
        
        iter_thread=ThreadWithReturnValue(target=wei_run_flow,kwargs={'wf_file_path': loop_protocol, 'payload':payload})
        iter_thread.run()
        run_info = iter_thread._return
        run_path =  run_info["run_dir"].parts[-1]
        if not (os.path.isdir(exp_folder / run_path)):
            os.mkdir(exp_folder / run_path)
        
        runs_list.append(run_info)
        

        used_wells = current_iter*pop_size 
        if used_wells + pop_size > 96: #if we have used all wells or not enough for next iter (thrash plate, start from scratch)
            print('Thrasing Used Plate')
            
            iter_thread=ThreadWithReturnValue(target=wei_run_flow,kwargs={'wf_file_path':final_protocol,'payload':payload})
            iter_thread.run()
            new_plate = True

        # analize image
        # output should be list [pop_size, 3]   
        fname = "final_image.jpg" #image"+str(ot2_iter) +".jpg"
        img_path = run_info["run_dir"]/ "results" / fname
        #plate_colors_ratios = get_colors_from_file(img_path)[1] ##FUNCX
        ##To be transplanted
       

        ep = '299edea0-db9a-4693-84ba-babfa655b1be' # local

        fx = FuncXExecutor(endpoint_id=ep)
        fxresult = fx.submit(get_colors_from_file, img_path,endpoint_id=ep)
        plate_colors_ratios = fxresult.result()[1]
        print(plate_colors_ratios)
        
        # Swap BGR to RGB
        plate_colors_ratios = {a:b[::-1] for a,b in plate_colors_ratios.items()}  
        
        current_plate = []
        wells_used = []
        for well in payload["destination_wells"]:
            color = plate_colors_ratios[well]
            wells_used.append(well)
            current_plate.append(color)
        
        
        ## save those and the initial colors, etc
        plate_best_color_ind, plate_diffs = solver._find_best_color(current_plate, target_color)
        plate_best_color = current_plate[plate_best_color_ind]
        plate_best_diff = solver._color_diff(plate_best_color, target_color)

        #Find best colors
        if plate_best_diff < cur_best_diff:
            cur_best_diff = plate_best_diff
            cur_best_color = plate_best_color


        publish_iter() #again


        ##update numbers (seems redundant)
        
        current_iter += 1
        num_exps += pop_size

        ##Plot review
        if show_visuals:
            import matplotlib.pyplot as plt
            plt.ion()
            f, axarr = plt.subplots(2, 2)
            # set figure size to 10x10
            f.set_figheight(10)
            f.set_figwidth(10)
            graph_vis = np.asarray(target_plate)
            graph_vis = graph_vis.reshape(*solver_out_dim)
            plate_vis = np.asarray(current_plate)
            plate_vis = plate_vis.reshape(*solver_out_dim)
            target_color = target_color
            axarr[0][0].imshow([graph_vis])
            axarr[0][0].set_title("Experiment plate")
            axarr[1][0].imshow([plate_vis])
            axarr[1][0].set_title("Real plate")
            axarr[0][1].imshow([[target_color]])
            axarr[0][1].set_title("Target Color")
            axarr[1][1].imshow([[cur_best_color]])
            axarr[1][1].set_title("Experiment best color")
            f.suptitle("PAUSING HERE TO MOVE THE PLATE")
            f.canvas.draw()
            f.canvas.flush_events()
            plt.pause(0.001)
            # plt.imsave(run_info["run_dir"] / "results" / "experiment_summary.jpg")

        report={
            "plate_N": plate_n,
            "target_color": target_color,
            "wells": wells_used,
            "tried_values": target_plate,
            "exp_volumes": plate_volumes,
            "results": list(map(lambda x: x.tolist(), current_plate)),
            "differences": plate_diffs.tolist(),
            "best_on_plate": plate_best_color.tolist(),
            "pos_on_plate": plate_best_color_ind.tolist(),
            "best_so_far": cur_best_color.tolist()
            
            
        }
        #Save experiment data=
        with open(exp_folder/run_path/ "exp_data.txt", "w") as f:
            report_js = json.dumps(report, indent=4)
            f.write(report_js)
        for filename in os.listdir(run_info["run_dir"]/ "results"):
            shutil.copy2(run_info["run_dir"]/ "results"/filename,  (exp_folder/run_path/filename))
    #Trash plate after experiment
    iter_thread=ThreadWithReturnValue(target=wei_run_flow,kwargs={'wf_file_path':final_protocol,'payload':payload})
    iter_thread.run()
    shutil.copy2(run_info["run_dir"]/ "results"/"final_image.jpg",  (exp_folder/"results"/"final_image.jpg"))
    if show_visuals:
        import matplotlib.pyplot as plt

        f, axarr = plt.subplots(1, 2)
        # set figure size to 10x10
        f.set_figheight(10)
        f.set_figwidth(10)
        axarr[0].imshow([[cur_best_color]])
        axarr[0].set_title("Experiment best color, diff: " + str(cur_best_diff))
        axarr[1].imshow([[target_color]])
        axarr[1].set_title("Target Color")

        plt.show()
        plt.savefig(exp_folder/"results" / "final_plot.png", dpi=300)
    
    report = {"target_color" : target_color, "best_color" :cur_best_color.tolist(), "best_diff": cur_best_diff, "total_iterations": current_iter, "pop_size": pop_size, "exp_budget": exp_budget, "total_plates": plate_n}
    with open(exp_folder/"results"/ "exp_data.txt", "w") as f:
            report_js = json.dumps(report, indent=4)
            f.write(report_js)
    print("This is our best color so far")
    print(cur_best_color)
    print("Runs on this experiment")
    print(runs_list)

def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--pop_size",
        default=4,
        type=int,
        help="Population size (num wells to fill per iter)",
    )
    parser.add_argument(
        "--exp_budget", default=8, type=int, help="Experiment budget"
    )
    parser.add_argument(
        "--target","-t", default="[101, 148, 30]", help="Color Target"
    )
    parser.add_argument("--plate_max_volume", default=275.0, type=float)
    return parser.parse_args()


if __name__ == "__main__":

    #parser
    args = parse_args()

    #target color
    target_ratio = eval(args.target)

    #workflows used
    wf_dir = Path('/home/rpl/workspace/rpl_workcell/color_picker/workflows')
    wf_get_plate = wf_dir / 'cp_wf_newplate.yaml'
    wf_trash_plate = wf_dir / 'cp_wf_trashplate.yaml'
    wf_mix_colors = wf_dir / 'cp_wf_mixcolor.yaml'

    exp_label = 'feb24416'
    exp_path = '/home/rpl/experiments'

    run_args = {}
    run_args["target_color"] = target_ratio
    run_args["init_protocol"] = wf_get_plate
    run_args["loop_protocol"] = wf_mix_colors
    run_args["final_protocol"] = wf_trash_plate
    run_args["solver"] = EvolutionaryColorSolver
    run_args["exp_budget"] = args.exp_budget
    run_args["pop_size"] = args.pop_size
    run_args["solver_out_dim"] = (args.pop_size, 3)
    run_args["plate_max_volume"] = args.plate_max_volume
    run_args["exp_label"] = exp_label
    run_args["exp_path"] = exp_path
    run(**run_args)
