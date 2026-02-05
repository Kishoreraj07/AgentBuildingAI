def get_task_from_queue(api_key):
    import requests
    import time
    import ast
    BASE_URL = "https://droidal.ai/app/agentsapp"
    startTime = int(round(time.time()))
    resp = requests.get(f"{BASE_URL}/tasks/pending/", params={"apikey": api_key})
    result = resp.json()

    # Handle no records
    if "status" in result and result["status"] == "no records":
        return "norecords", "norecords", "norecords", False, startTime, "", ""

    # Handle valid record
    try:
        records = ast.literal_eval(str(result.get("data", {}))) if isinstance(result.get("data"), dict) else result.get("data")
        rowid = result.get("id")
        status_val = result.get("status")
        queuename = result.get("apikey", "")
        queueemail = result.get("usermailid", "")
        return records, rowid, status_val, True, startTime, queuename, queueemail
    except Exception as e:
        return "norecords", "norecords", "norecords", False, startTime, "", ""

