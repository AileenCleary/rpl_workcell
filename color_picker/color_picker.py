#!/usr/bin/env python3

import logging
from pathlib import Path
from argparse import ArgumentParser
from typing import List, Dict, Any, Tuple
from itertools import product
from uuid import UUID
from typing import Optional

import numpy as np

from evolutionary_solver import EvolutionaryColorSolver


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-wf", "--workflow", help="Path to workflow file", type=Path, required=True
    )
    parser.add_argument(
        "--pop_size",
        default=96,
        type=int,
        help="Population size (num wells to fill per iter)",
    )
    parser.add_argument(
        "--exp_budget", default=96 * 3, type=int, help="Experiment budget"
    )
    parser.add_argument(
        "--simulate", action="store_true", help="Simulate workflow, no WEI "
    )
    parser.add_argument("--plate_max_volume", default=275.0, type=float)
    return parser.parse_args()


def convert_volumes_to_payload(volumes: List[List[float]]) -> Dict[str, Any]:
    well_rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
    well_cols = [str(elem) for elem in range(1, 13)]
    well_names = ["".join(elem) for elem in product(well_rows, well_cols)]
    assert len(volumes) <= len(well_names)
    r_vol, g_vol, b_vol = [], [], []
    dest_wells = []
    for color, well in zip(volumes, well_names):
        r, g, b = color
        r_vol.append(r)
        g_vol.append(g)
        b_vol.append(b)
        dest_wells.append(well)
    return {
        "red_volumes": r_vol,
        "green_volumes": g_vol,
        "blue_volumes": b_vol,
        "destination_wells": dest_wells,
    }


def run(
    target_color: List[float],
    wei_client: Optional["WEI"] = None,
    protocol_id: Optional[UUID] = None,
    solver: EvolutionaryColorSolver = EvolutionaryColorSolver,
    exp_budget: int = 96 * 3,
    pop_size: int = 96,
    solver_out_dim: Tuple[int, int] = (96, 3),
    plate_max_volume: float = 275.0,
    simulate: bool = False,
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
    print(
        "Starting experiment, can run at least one iteration:",
        num_exps + pop_size <= exp_budget,
    )

    cur_best_color = None
    cur_best_diff = float("inf")
    while num_exps + pop_size <= exp_budget:
        plate_volumes = solver.run_iteration(
            target_color,
            current_plate,
            out_dim=(pop_size, 3),
            pop_size=pop_size,
            return_volumes=True,
            return_max_volume=plate_max_volume,
        )

        if not simulate:
            payload = convert_volumes_to_payload(plate_volumes)
            run_info = wei_client.run_workflow(
                workflow_id=protocol_id,
                payload=payload,
            )

            # TODO: this will move to funcx
            # analize image
            img_path = run_info["run_dir"] / "results" / "final_image.jpg"
            # output should be list [pop_size, 3]
            plate_colors_ratios = get_colors_from_file(img_path)
            print(plate_colors_ratios)

            # save the plate colors as csv
            with open(run_info["run_dir"] / "results" / "plate_colors.csv", "w") as f:
                for color in plate_colors_ratios:
                    f.write("%s,%s,%s" % (color[0], color[1], color[2]))
                    f.write("\n")

        else:
            # going to convert back to ratios for now
            plate_color_ratios = [
                (np.asarray(elem) / 275).tolist() for elem in plate_volumes
            ]

        plate_best_color_ind = solver._find_best_color(plate_color_ratios, target_color)
        plate_best_color = plate_color_ratios[plate_best_color_ind]
        plate_best_diff = solver._color_diff(plate_best_color, target_color)

        if plate_best_diff < cur_best_diff:
            cur_best_diff = plate_best_diff
            cur_best_color = plate_best_color

        current_plate = plate_color_ratios
        num_exps += pop_size

        if show_visuals:
            import matplotlib.pyplot as plt

            f, axarr = plt.subplots(2, 2)
            # set figure size to 10x10
            f.set_figheight(10)
            f.set_figwidth(10)
            graph_vis = np.asarray(current_plate)
            graph_vis = graph_vis.reshape(*solver_out_dim)
            target_color = target_color
            axarr[0][0].imshow([graph_vis])
            axarr[0][0].set_title("Experiment plate")
            axarr[0][1].imshow([[target_color]])
            axarr[0][1].set_title("Target Color")
            axarr[1][1].imshow([[cur_best_color]])
            axarr[1][1].set_title("Experiment best color")
            f.suptitle("PAUSING HERE TO MOVE THE PLATE")
            plt.show()

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
        if not simulate:
            plt.savefig(run_info["run_dir"] / "results" / "final_plot.png", dpi=300)

    print("This is our best color so far")
    print(cur_best_color)


def main(args):

    # target_ratio = [101, 173, 95]
    target_ratio = [1, 93, 82]
    # Not needed for now
    # mixing_colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]

    run_args = {}
    if not args.simulate:
        # workflows/cp_workflow_singleot2.yaml
        wf_file_path = args.workflow.resolve()

        wei_client = WEI(
            wf_file_path,
            workcell_log_level=logging.DEBUG,
            workflow_log_level=logging.DEBUG,
        )
        protocol_id = list(wei_client.get_workflows().keys())[0]

        run_args = {
            "wei_client": wei_client,
            "protocol_id": protocol_id,
        }

    run_args["target_color"] = target_ratio
    run_args["solver"] = EvolutionaryColorSolver
    run_args["exp_budget"] = args.exp_budget
    run_args["pop_size"] = args.pop_size
    run_args["solver_out_dim"] = (args.pop_size, 3)
    run_args["plate_max_volume"] = args.plate_max_volume
    run_args["simulate"] = args.simulate

    run(**run_args)


if __name__ == "__main__":
    args = parse_args()
    if not args.simulate:
        from rpl_wei import WEI
        from plate_color_analysis import get_colors_from_file
    main(args)
