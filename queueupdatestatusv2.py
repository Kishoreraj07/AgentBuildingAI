import requests
import time
from config import MAIN_URL

def queue_update(api_key,task_id, statusupdate, queuename="", queueemail="", clientname="", remark="", desc_data="", startTime=None):
    BASE_URL = f"{MAIN_URL}/app/agentsapp"
    if not startTime:
        startTime = int(round(time.time()))

    try:
        startTime = int(startTime)
    except Exception:
        startTime = int(round(time.time()))
    endTime = int(round(time.time()))
    time_dur = endTime - startTime

    # --- Step 1: Update task in Django API ---
    payload = {
        "apikey": api_key,
        "status": statusupdate
    }
    resp = requests.put(f"{BASE_URL}/tasks/{task_id}/update-status/", json=payload)
    print("Django API Update:", resp.status_code, resp.json())
