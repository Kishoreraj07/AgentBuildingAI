import requests
import json
import pandas as pd
MAIN_URL = "https://droidal.ai"
def queue_upload(queueapi, outputvariable):
    try:
        if isinstance(outputvariable, list) and all(isinstance(x, dict) for x in outputvariable):
            outputvariable = pd.DataFrame(outputvariable)
        else:
            outputvariable = outputvariable
        all_keys = list(outputvariable.keys())
        #result_list = [{key: str(value)} for key, values in outputvariable.items() for value in values]
        
        outputvariable = [{key: str(values[i]) for key, values in outputvariable.items()} for i in range(len(outputvariable[all_keys[0]]))]
        
        BASE_URL = "https://droidal.ai"
        import requests
        payload = {
        "apikey": queueapi,
        "data": {
            "tasks":outputvariable
        }
        }

        resp = requests.post(f"{BASE_URL}/app/agentsapp/tasks/create/", json=payload)
        print("Create Task:", resp.status_code, resp.json())
    except:
        import traceback
        traceback.print_exc()