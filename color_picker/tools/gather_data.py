from gladier import GladierBaseClient, generate_flow_definition, GladierBaseTool
def gather_metadata(**data):

    from pathlib import Path
    import json
    GENERAL_METADATA = {
    "creators": [{"creatorName": "RPL Team"}],
    "publicationYear": "2023",
    "publisher": "Argonne National Lab",
    "resourceType": {
        "resourceType": "Dataset",
        "resourceTypeGeneral": "Dataset"
    },
    "subjects": [{"subject": "SDL"}],
    "exp_type": "color_picker"

    }

    input_path = Path(data['make_input']).expanduser()
    with open(input_path / "exp_data.txt") as f:
        datal = json.loads(f.read())
 
    datal.update(GENERAL_METADATA)
<<<<<<< HEAD
    final_data = data["pilot"]
=======
    final_data = data["publishv2"]
>>>>>>> 393575f02fa5a5c48996a5ccba843838a1963115
    final_data['metadata'] = datal
    return final_data

@generate_flow_definition
class GatherMetaData(GladierBaseTool):
    funcx_functions = [gather_metadata]
    required_input = [
        'make_input',
<<<<<<< HEAD
        'funcx_endpoint_compute',
        'pilot'
=======
        'funcx_endpoint_compute'
>>>>>>> 393575f02fa5a5c48996a5ccba843838a1963115
    ]


