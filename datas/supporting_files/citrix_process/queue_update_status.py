# def queue_update(api_key, task_id, statusupdate, queuename="", queueemail="", clientname="", remark="", desc_data="", startTime=None):
def queue_update(api_key,statusupdate,startTime=None):
    import os,json
    Task_file="task_info.json"
    with open(Task_file, "r", encoding="utf-8") as f:
        task_info = json.load(f)
    task_name=task_info["Task_file_name"]
    task_id=task_name.split("_")[-1]
    import requests
    import time
    BASE_URL = "https://droidal.ai/app/agentsapp"
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

    # --- Step 2: Call external GET endpoint (like your old logic) ---
    try:
        get_url = f"https://cloud.droidal.com/queuerecordsupdatestatus/{task_id}/{statusupdate}"
        print("Calling:", get_url)
        requests.get(get_url, timeout=10, verify=False)
    except Exception as e:
        print("External GET failed:", e)

    # --- Step 3: Push to external POST endpoint (audit / tracking) ---
    post_url = "https://droidmetrix.droidal.com/update_queue_trans/"
    payload_post = {
        'queuename': queuename,
        'statustype': str(statusupdate),
        'queueemailid': str(queueemail).lower(),
        'clientname': clientname,
        'remark': remark,
        'content_desc': desc_data,
        'duration': time_dur
    }
    try:
        r = requests.post(post_url, data=payload_post, files=[], verify=True)
        print("External POST:", r.status_code, r.text)
    except Exception as e:
        print("External POST failed:", e)