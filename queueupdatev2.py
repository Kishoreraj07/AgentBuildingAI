import requests
import json
from config import MAIN_URL

def queueupdate(queueapi,outputvariable):
        #print(outputvariable.keys()[1])
    all_keys = list(outputvariable.keys())
    #result_list = [{key: str(value)} for key, values in outputvariable.items() for value in values]
    
    outputvariable = [{key: str(values[i]) for key, values in outputvariable.items()} for i in range(len(outputvariable[all_keys[0]]))]
    
    
    import requests
    payload = {
    "apikey": queueapi,
    "data": {
        "tasks":outputvariable
    }
    }

    resp = requests.post(f"{MAIN_URL}/app/agentsapp/tasks/create/", json=payload)
    print("Create Task:", resp.status_code, resp.json())