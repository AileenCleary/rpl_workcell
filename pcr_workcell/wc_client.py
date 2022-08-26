from pathlib import Path
from argparse import ArgumentParser

from rpl_wei.wei_client_base import WEI
import logging

def print_callback(step):
    print(step)

##
from wei_executor.weiExecutorNode import weiExecNode
def wei_service_callback(step):
    wei_execution_node = weiExecNode()
    rclpy.init() # without this line the weiExecNode does not get started

    #get all info
    #get info from workcell
    #substitute things from wc_dictionary
    #send_wei_command(service,action_handler,actions_vars)
##

def main(args):
    wei = WEI(
        args.workcell,
        args.workflow,
        workcell_log_level=logging.DEBUG,
        workflow_log_level=logging.DEBUG,
    )

    # get the workflow id (currently defaulting to first one available)
    wf_id = list(wei.get_workflows().keys())[0]

    wei.run_workflow(wf_id, step_execution_callback=wei_service_callback)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-wc", "--workcell", help="Path to workcell file", type=Path)
    parser.add_argument("-wf", "--workflow", help="Path to workflow file", type=Path, required=True)
    parser.add_argument("-v", "--verbose", help="Extended printing options", action="store_true")

    args = parser.parse_args()
    main(args)
