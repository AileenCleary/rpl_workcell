from gladier import GladierBaseClient, generate_flow_definition, GladierBaseTool
from gather_data import GatherMetaData
from pathlib import Path
@generate_flow_definition(modifiers={'publish_gather_metadata': {'payload': '$.GatherMetadata.details.result[0]'}})
class PublishRun(GladierBaseClient):
    globus_group = 'dda56f31-53d1-11ed-bd8b-0db7472df7d6'
    gladier_tools = [
        GatherMetaData,
        'gladier_tools.publish.Publishv2'
    ]

def publish_iter(folder_path, dest_path):
        #gather some shit and transfer it to the exp\
        print(str(folder_path.expanduser()))
        print(str(dest_path ))    
        flow_input = {
            'input': {
                'make_input': str(folder_path.expanduser()),
                'funcx_endpoint_compute':'95038e17-339b-4462-9c9f-a8473809af25',
                'funcx_endpoint_non_compute':'95038e17-339b-4462-9c9f-a8473809af25',

                
                'publish': {
                    'dataset': str(folder_path.expanduser()),
                    'index': 'aefcecc6-e554-4f8c-a25b-147f23091944',
                    'project': 'reports',
                    'source_globus_endpoint': 'eeabbb24-b47d-11ed-a504-1f2a3a60e896',
                    'source_collection_basepath': '\mnt\c\Users\tgins\rpl_workcell\color_picker\demo_data',
                    'metadata': {},
                    'destination':str(dest_path)
                }
                }
            }


        # Create the Client
        publishFlow = PublishRun()
        label = 'testPublishTobias'
        # Run the flow
        flow = publishFlow.run_flow(flow_input=flow_input,label=label)
        # Track progress
        # action_id = flow['action_id']
        # publishFlow.progress(action_id)
     
        
