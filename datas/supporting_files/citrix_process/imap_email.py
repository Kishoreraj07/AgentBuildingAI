import imaplib
import email
from email.header import decode_header
import re
import time
from bs4 import BeautifulSoup

def fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                            folder="INBOX", sender_filter=None, subject_filter=None, timeout=180):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_id, email_pass)
        mail.select(folder)
        start_time = time.time()

        while time.time() - start_time < timeout:
            status, data = mail.search(None, "ALL")
            mail_ids = data[0]
            id_list = mail_ids.split()
            latest_ids = id_list[-20:]  # Check last 20 emails

            for msg_id in reversed(latest_ids):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode Subject
                subject_raw = decode_header(msg.get("Subject", ""))[0]
                subject = subject_raw[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(subject_raw[1] or "utf-8", errors="ignore")
                subject = subject.lower()

                # Sender
                from_header = msg.get("From", "").lower()

                # Extract body (text/plain or text/html)
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" in content_disposition:
                            continue
                        if content_type == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body_text = payload.decode(errors="ignore")
                                break
                        elif content_type == "text/html" and not body_text:
                            payload = part.get_payload(decode=True)
                            if payload:
                                html = payload.decode(errors="ignore")
                                soup = BeautifulSoup(html, "html.parser")
                                for script in soup(["script", "style"]):
                                    script.decompose()
                                body_text = soup.get_text(separator=" ")
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        if msg.get_content_type() == "text/html":
                            soup = BeautifulSoup(payload.decode(errors="ignore"), "html.parser")
                            for script in soup(["script", "style"]):
                                script.decompose()
                            body_text = soup.get_text(separator=" ")
                        else:
                            body_text = payload.decode(errors="ignore")

                full_text = f"{subject} {body_text}".lower()

                # Apply filters ONLY if explicitly provided
                if sender_filter is not None and sender_filter.lower() not in from_header:
                    continue
                if subject_filter is not None and subject_filter.lower() not in subject:
                    continue

                code_match = re.search(r'\\b\\d{4,10}\\b', full_text)
                if code_match:
                    mail.logout()
                    return code_match.group()

            time.sleep(6)

        mail.logout()
    except Exception as e:
        print("IMAP Error:", e)
    return None