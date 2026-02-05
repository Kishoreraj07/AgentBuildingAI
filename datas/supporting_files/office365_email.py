import requests
import time
import re
from bs4 import BeautifulSoup

def get_graph_access_token(tenant_id, client_id, client_secret):
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Graph Token Error:", response.text)
        return None

def fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                            sender_filter=None, subject_filter=None, timeout=180):
    token = get_graph_access_token(tenant_id, client_id, client_secret)
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
    params = {
        "$top": 15,
        "$orderby": "receivedDateTime desc",
        "$select": "subject,body,from,receivedDateTime"
    }
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            time.sleep(10)
            continue
        for msg in r.json().get("value", []):
            subject = (msg.get("subject") or "").lower()
            sender = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
            body_content = msg.get("body", {}).get("content", "")  # Full HTML or text

            # Extract clean text from HTML body
            if msg.get("body", {}).get("contentType") == "html":
                soup = BeautifulSoup(body_content, "html.parser")
                # Remove script/style + get visible text
                for script in soup(["script", "style"]):
                    script.decompose()
                clean_text = soup.get_text(separator=" ").lower()
            else:
                clean_text = body_content.lower()

            full_text = f"{subject} {clean_text}"

            # Apply filters ONLY if explicitly provided
            if sender_filter is not None and sender_filter.lower() not in sender:
                continue
            if subject_filter is not None and subject_filter.lower() not in subject:
                continue

            code_match = re.search(r'\\b\\d{4,10}\\b', full_text)
            if code_match:
                return code_match.group()

        time.sleep(8)
    return None
