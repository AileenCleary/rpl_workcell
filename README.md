# Background on Workcells, Carts, Modules, and Workflows

**Note**: I use the term Cart (formerly, "module"), as the word "module" is used for something different in the code.

In RPL we define standardized hardware and software configurations for robotic equipment and control software in order to simplify the assembly, modification, and scaling of experimental systems:
* A **cart** is a cart with zero or more modules 
* A **module** is an hardware component with a name, type, position, etc. (e.g., Pealer, Sealer, OT2 liquid handling robot, plate handler, plate mover, camera)
* A **workcell**, as show on the left of the image, is formed from multiple (8 in the photo on the left) carts that typically hold multiple modules (12 in the example, as described below).
* Multiple workcells and other components can be linked via mobile robots

![Screenshot of a comment on a GitHub issue showing an image, added in the Markdown, of an Octocat smiling and raising a tentacle.](assets/AD_Fig.jpg)

An RPL "workflow" is a program to cause one or more actions to be performed on equipment within a workcell. It comprises two components:
* The **workcell definition** defines the XXXXs that comprise a workcell, and associated static infrastructure that are to be used by the workflow
* The **workflow definition** defines the sequence of actions that are to be executed in order on the nodes.

## Workcell definition

This is specified by a YAML file that defines the nodes and associated static infrastructure that are to be used by the workflow. E.g., see [this example](https://github.com/AD-SDL/rpl_workcell/blob/main/pcr_workcell/pcr_workcell.yaml). The file comprises two sections, *config* and *modules*:

* The **config** section defines various variables that may be used elsewhere in the workcell. For example, here is the config from the example just listed.

```
  ros_namespace: rpl_workcell                                 # ???
  funcx_local_ep: "299edea0-db9a-4693-84ba-babfa655b1be"      # UUID used for local computations
  globus_local_ep: ""                                         # 
  globus_search_index: "aefcecc6-e554-4f8c-a25b-147f23091944" # UUID for the Globus Search instance
  globus_portal_ep: "bb8d048a-2cad-4029-a9c7-671ec5d1f84d"    # ???
  globus_group: "dda56f31-53d1-11ed-bd8b-0db7472df7d6"        # ???
```

* The **modules** section lists the *modules* that are included in the workcell. For example, in the example just listed, there are 12 in total: 
  * a [pf400 sample handler](https://preciseautomation.com/SampleHandler.html) (**pf400**) and two associated cameras, **pf400_camera_right** and **pf400_camera_left**; 
  * a [SciClops plate stacker](https://hudsonrobotics.com/microplate-handling-2/platecrane-sciclops-3/) (**sciclops**)
  * a XX (**sealer**) and a XX (**peeler**), with an associated camera, **sp_module_camera**
  * three OpenTrons OT2 liquid handlers, **ot2_pcr_alpha**, **ot2_pcr_beta**, and **ot2_cp_gamma**;
  * a [Biometra thermal cycler](https://www.analytik-jena.com/products/life-science/pcr-qpcr-thermal-cycler/thermal-cycler-pcr/biometra-trio-series/) (**biometra**)
  * a XXX (**camera_module**)
           
* Here is an example module specification:

```
  - name: sealer                     # A name used for the module in the workflow: its "alias"
    type: wei_ros_node               # Indicates that module uses ROS2
    model: sealer                    # ??
    config:
      ros_node: "/std_ns/SealerNode" # ??
    positions:                       # One or more spatial locations, with name 
      default: [205.128, -2.814, 264.373, 365.863, 79.144, 411.553]
```

**NOTE**: Raf says "Each node defines its own protocols (ROS2, EPICS, TCP/IP, etc) and the variables necessary to interact with it (IP, PORT, NAME, ETC)" -- does any of that come up here? Is it the "type" that indicates ROS2?


## Workflow definition

This is specified by a YAML file that defines the sequence of actions that will be executed in order on the hardware. E.g., see [this example](https://github.com/AD-SDL/rpl_workcell/blob/main/pcr_workcell/workflows/ot2_test.yaml), shown also in the following, and comprising four sections:
* **metadata**: Descriptive metadata for the workflow
* **workcell**: The location of the workcell that the workflow is designed for
* **modules**: A list of the modules included in the workcell--just one here.
* **flowdef**: A list of steps, each with a name, module, command, and arguments.

```
metadata:
  name: PCR - Workflow
  author: Casey Stone, Rafael Vescovi
  info: Initial PCR workflow for RPL workcell
  version: 0.1

workcell: /home/rpl/wei_ws/demo/rpl_workcell/pcr_workcell/pcr_workcell.yaml

modules:
  - name: ot2_pcr_alpha

flowdef:
  - name: Mix OT2 reactions
    module: ot2_pcr_alpha
    command: run_protocol
    args:
      config_path: /home/rpl/wei_ws/demo/rpl_workcell/pcr_workcell/protocol_files/ot2_pcr_config.yaml
```

This workflow uses just one of the 12 modules defines in the 

**NOTE**: Raf writes as follows.  This is not clear to me, as I do not see any of the words that he lists  (step name, robot, action name, vars) in the example:

This file uses the "alias" defined for each robot above and a funcx style message:
Step Name: Name on the workflow
Robot: Target Robot
Action name: Action to be executed on the robot
Vars: variable dictionary for that particular action
