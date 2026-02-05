import google.generativeai as genai
import config
import json
def xpath_json(code):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the code : {code}

Analyze the code thoroughly and identify all variables that are used as element identifiers for web elements (e.g., username_input, password_input etc.), 
even if they are assigned dynamically or imported from other modules.

Generate a JSON object where:
    - Each key is the variable name found in the code that represents a web element.
    - Each value is "Not_assigned".
{{"username_input":"Not_assigned","password_input":"Not_assigned",....}}

If no such variable is found in the code, return an empty JSON {{}}.

Return only the JSON. Do not add any explanations, text, or extra output."""

    response = chat.send_message(prompt)
    res_txt=response.text
    if '`' in res_txt:
        res=res_txt.strip("`")
        res_txt=res
    if '\n' in res_txt:
        res=res_txt.strip("\n")
        res_txt=res
    if 'json' in res_txt:
        res=res_txt.strip("json")
        res_txt=res
    if 'python' in res_txt:
        res=res_txt.strip("python")
        res_txt=res
    if '```' in res_txt:
        res=res_txt.strip("```")
        res_txt=res
    res=res_txt
    if type(res)==str:
        if res.startswith("{") and res.endswith("}"):
            res=json.loads(res)
        else:
            try:
                res=json.loads(res)
            except:
                pass
    return res

def gemini_response(input,proj_name,task_name,userid):
    if type(input)==list:
        requirement=""
        for i in input:
            requirement+=f"{i}\n"
        input=requirement
    if type(input)==str:
        requirement=""
        for index, i in enumerate(input.split("\n")):
            requirement+=f"step {index+1} : {i}, "
        input=requirement
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()

    launching_code="""
            def open_url_with_selenium(url):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    chrome_options.add_argument("--start-maximized")

    # Create driver
    driver = webdriver.Chrome(options=chrome_options)

    # Open the passed URL
    driver.get(url)

    return driver
            """
    
    office365_email_code="""import requests
        import time
        import re
        from bs4 import BeautifulSoup

        def get_graph_access_token(tenant_id, client_id, client_secret):
            url = f"https://login.microsoftonline.com/{{tenant_id}}/oauth2/v2.0/token"
            payload = {{
                "client_id": client_id,
                "scope": "https://graph.microsoft.com/.default",
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }}
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
            headers = {{"Authorization": f"Bearer {{token}}"}}
            url = f"https://graph.microsoft.com/v1.0/users/{{user_email}}/messages"
            params = {{
                "$top": 15,
                "$orderby": "receivedDateTime desc",
                "$select": "subject,body,from,receivedDateTime"
            }}
            start = time.time()
            while time.time() - start < timeout:
                r = requests.get(url, headers=headers, params=params)
                if r.status_code != 200:
                    time.sleep(10)
                    continue
                for msg in r.json().get("value", []):
                    subject = (msg.get("subject") or "").lower()
                    sender = msg.get("from", {{}}).get("emailAddress", {{}}).get("address", "").lower()
                    body_content = msg.get("body", {{}}).get("content", "")  # Full HTML or text

                    # Extract clean text from HTML body
                    if msg.get("body", {{}}).get("contentType") == "html":
                        soup = BeautifulSoup(body_content, "html.parser")
                        # Remove script/style + get visible text
                        for script in soup(["script", "style"]):
                            script.decompose()
                        clean_text = soup.get_text(separator=" ").lower()
                    else:
                        clean_text = body_content.lower()

                    full_text = f"{{subject}} {{clean_text}}"

                    # Apply filters ONLY if explicitly provided
                    if sender_filter is not None and sender_filter.lower() not in sender:
                        continue
                    if subject_filter is not None and subject_filter.lower() not in subject:
                        continue

                    code_match = re.search(r'\\b\\d{{4,10}}\\b', full_text)
                    if code_match:
                        return code_match.group()

                time.sleep(8)
            return None
"""

    imap_email_code="""import imaplib
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

                        full_text = f"{{subject}} {{body_text}}".lower()

                        # Apply filters ONLY if explicitly provided
                        if sender_filter is not None and sender_filter.lower() not in from_header:
                            continue
                        if subject_filter is not None and subject_filter.lower() not in subject:
                            continue

                        code_match = re.search(r'\\b\\d{{4,10}}\\b', full_text)
                        if code_match:
                            mail.logout()
                            return code_match.group()

                    time.sleep(6)

                mail.logout()
            except Exception as e:
                print("IMAP Error:", e)
            return None"""
    
    code_execute_step=f"""def execute_step(driver, var_name, description,json_xpath):
        var_name=var_name
        current_xpath = json_xpath.get(var_name)
        file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
        if current_xpath == "Not_assigned":
            raw_xpath = main(description, driver)
            # Verify status
            is_valid, current_xpath = element_status(var_name, raw_xpath, driver)
            # Update JSON
            json_xpath[var_name] = current_xpath

            with open(JSON_PATH, "w") as f:
                json.dump(json_xpath, f, indent=4)
 
        # 2. Code Generation & Execute
        if not os.path.exists(file_path):
            current_xpath = main(description, driver)
            gemini_code_correction.code_correction(description, current_xpath, file_path, var_name, driver, {userid})
            module_path = f"{proj_name}.{task_name}.var_name"
            module = importlib.import_module(module_path)
            module.run(driver)
        else:
            module_path = f"{proj_name}.{task_name}.var_name"
            module = importlib.import_module(module_path)
            module.run(driver)"""
    
    prompt = f"""
        Here is the User Requirement: {input}

        Based on the above requirement, generate the **Web Automation Code**.

        ================================================================================
        STANDARD FUNCTION IMPORTS (from datas.supporting_files)
        ================================================================================

        **CRITICAL: Path Setup Required**
        Before importing from datas.supporting_files, add the AgentFlow directory to sys.path:
        ```python
                import sys
                import os
                sys.path.append(r"D:\\AgentFlow")
        ```

        Then import standard functions:
        
        Instead of defining functions internally, import these standard functions:

        1. **URL Launch Function:**
        from datas.supporting_files.launch_url import open_url_with_selenium
        driver = open_url_with_selenium(url)
           - Always returns 'driver' variable
           - Use this driver variable for all subsequent operations

        2. **Email Fetching - Microsoft Graph API (Office 365):**
        from datas.supporting_files.office365_email import fetch_latest_email_graph
        code = fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                                      sender_filter=None, subject_filter=None, timeout=180)

        3. **Email Fetching - IMAP (Gmail, Yahoo, Custom Domains):**
        from datas.supporting_files.imap_email import fetch_latest_email_code
        code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                     folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

        4. Execute Step Code: {code_execute_step}

        ================================================================================
        CRITICAL EMAIL FILTERING RULE
        ================================================================================
        - sender_filter and subject_filter must be optional (default=None)
        - MUST check `if sender_filter is not None` before applying the filter
        - Same for subject_filter
        - If user does NOT specify sender/subject → set to None → skip filtering
        - If user specifies → pass the exact string → apply filtering
        - Never hardcode or assume filters unless explicitly mentioned in requirement

        ================================================================================
        EMAIL FETCHING RULES
        ================================================================================
        - Use **Microsoft Graph API** when user mentions: Office 365, Outlook, Microsoft email, tenant, client ID, Azure AD
        - Use **IMAP** for Gmail, Yahoo, custom domains, or when email/password is provided
        - **Never wrap email logic** in var_name / json_xpath / .run() pattern
        - Write email fetching **directly inside aba_agent()** as native code
        - Extract **4-8 digit codes automatically** using regex
        - Always wait up to 180 seconds (configurable)
        - Credentials must come from user requirement — never hardcode unless explicitly provided
        - For Graph API: Use **client credentials flow** (no user login)
        - For Gmail: Must use **App Password** (not regular password)

        ================================================================================
        QUEUE HANDLING RULES
        ================================================================================
        CRITICAL: Queue operations should ONLY be used when explicitly mentioned in user requirements.
        DO NOT assume or add queue operations unless the user specifically requests them.

        RULE 1: Queue Detection
            Use queue operations ONLY when user requirement contains keywords like:
            - "queue", "get from queue", "retrieve from queue", "upload to queue"
            - "update queue status", "queue item", "queue data"

            If any of these keywords are present, import queue modules with:
                import sys, os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            If none of these are mentioned, DO NOT include any queue-related code.

        RULE 2: Get Queue (Retrieve from Queue)
            ONLY when user explicitly mentions retrieving/getting values from queue:
            
            def get_task_from_queue(api_key):
                import requests
                import time
                import ast
                MAIN_URL = "https://droidal.ai"
                BASE_URL = f"{{MAIN_URL}}/app/agentsapp"
                startTime = int(round(time.time()))
                resp = requests.get(f"{{BASE_URL}}/tasks/pending/", params={{"apikey": api_key}})
                result = resp.json()

                if "status" in result and result["status"] == "no records":
                    return "norecords", "norecords", "norecords", False, startTime, "", ""

                try:
                    records = ast.literal_eval(str(result.get("data", {{}}))) if isinstance(result.get("data"), dict) else result.get("data")
                    rowid = result.get("id")
                    status_val = result.get("status")
                    queuename = result.get("apikey", "")
                    queueemail = result.get("usermailid", "")
                    return records, rowid, status_val, True, startTime, queuename, queueemail
                except Exception as e:
                    return "norecords", "norecords", "norecords", False, startTime, "", ""

        RULE 3: Upload Queue (Add to Queue)
            ONLY when user explicitly mentions uploading/adding values to queue:
            
            def queueupdate(queueapi, outputvariable):
                import requests
                import json
                MAIN_URL = "https://droidal.ai"
                all_keys = list(outputvariable.keys())
                outputvariable = [{{key: str(values[i]) for key, values in outputvariable.items()}} for i in range(len(outputvariable[all_keys[0]]))]
                
                payload = {{
                    "apikey": queueapi,
                    "data": {{
                        "tasks": outputvariable
                    }}
                }}

                resp = requests.post(f"{{MAIN_URL}}/app/agentsapp/tasks/create/", json=payload)
                print("Create Task:", resp.status_code, resp.json())
            
            Note: If uploading queue from excel data, read excel using pandas and pass the DataFrame directly to queueupdate without converting to dict.

        RULE 4: Update Queue Status
            ONLY when user explicitly mentions updating status of queue items:
            
            def queue_update(api_key, task_id, statusupdate, queuename="", queueemail="", clientname="", remark="", desc_data="", startTime=None):
                import requests
                import time
                MAIN_URL = "https://droidal.ai"
                BASE_URL = f"{{MAIN_URL}}/app/agentsapp"
                if not startTime:
                    startTime = int(round(time.time()))

                try:
                    startTime = int(startTime)
                except Exception:
                    startTime = int(round(time.time()))
                endTime = int(round(time.time()))
                time_dur = endTime - startTime

                payload = {{
                    "apikey": api_key,
                    "status": statusupdate
                }}
                resp = requests.put(f"{{BASE_URL}}/tasks/{{task_id}}/update-status/", json=payload)
                print("Django API Update:", resp.status_code, resp.json())

        ================================================================================
        CODE STRUCTURE INSTRUCTIONS FOR WEB AUTOMATION USING SELENIUM
        ================================================================================

        ================================================================================
        ACTION CLASSIFICATION AND CODE PATTERN RULES
        ================================================================================

        **RULE 1: ALL XPATH ACTIONS (Use Complete Module Pattern)**
        ALL web element interactions must use external module files with the FULL PATTERN:
        - Type actions (label, input, search field)
        - Click actions (buttons, links, checkboxes, radio buttons, icons)
        - Extract/Read actions (get text, get attribute values, scrape data)
        - Scroll actions (scroll to element, scroll page)
        - Navigation actions (browser back, forward, refresh)
        - Alert/Popup handling (accept alert, dismiss alert)
        - Dropdown selection (select from dropdown, choose option)
        - Table extraction from web pages (scrape table, extract table to Excel)
        - Date picker interactions (calendar selection, date range selection)
        - Multi-step complex interactions requiring state management
        - File upload/download interactions
        - Drag and drop actions
        - Hover actions
        - Any other web element interaction

        **Pattern for ALL XPATH Actions:**
        ```python
        var_name = "action_name"
        description = "Full action description"
        execute_step(driver, var_name, description, json_xpath)
        ```

        **CRITICAL**: Inside execute_step function:
        - Dynamic import `from {proj_name}.{task_name} import {{var_name}}` must be placed IMMEDIATELY before the .run(driver) call
        - Always pass only ONE argument to .run() which is driver
        - Do NOT pass additional arguments

        **RULE 2: DIRECT CODE IMPLEMENTATION (No Pattern Required)**
        These actions do NOT involve web elements and should be written directly as logical code:
        - Variable assignment (assign value, declare variable, set variable)
        - File operations (open file, save file, delete file, move file, copy file)
        - Excel/CSV operations (read Excel, write Excel, filter Excel data, create DataFrame)
        - Directory operations (create folder, delete folder, list files)
        - Date/Time calculations (get current date, calculate date difference, format date)
        - String operations (concatenate, split, replace, format)
        - Mathematical operations (calculate, sum, average)
        - Data transformations (convert data types, parse JSON, format data)
        - Conditional logic (if-else conditions based on variables)
        - Loop iterations (for loops, while loops over data)
        - API calls (not web browser related)

        **Pattern for DIRECT CODE:**
        Simply write the Python code directly without using var_name, json_xpath, or any pattern structure.

        Example:
        ```python
        # Read Excel file
        import pandas as pd
        excel_file_path = r"C:\\Users\\Administrator\\Documents\\data.xlsx"
        df_excel = pd.read_excel(excel_file_path)

        # Filter data
        filtered_df = df_excel[df_excel['Status'] == 'Active']

        # Calculate date
        from datetime import datetime, timedelta
        today = datetime.now()
        previous_month = today - timedelta(days=30)
        ```

        **RULE 3: REFERENCE FUNCTIONS**
        If actions are related to:
        - Launching URL → Declare open_url_with_selenium() function inside aba_agent() and call it
        - Mail Read → Declare email fetching function inside aba_agent() and call it
        - Queue operations → Declare queue functions inside aba_agent() and call it
        - Execute Step → Declare execute_step() function inside aba_agent() and use for all XPath actions

        ================================================================================
        CORRECT CODE PATTERN EXAMPLE (MANDATORY)
        ================================================================================
        User Requirement:
        - Launch the URL http://54.90.203.61/
        - Type username as admin
        - Type password as 1234
        - Click Sign In button
        - Type 123456 in OTP field
        - Click Verify button
        - Click Forms button
        - Select India from country dropdown
        - Select Tamil Nadu from state/province dropdown
        - Select Coimbatore in city dropdown
        - Click Select Skills button
        - Check Python checkbox
        - Type 2323 3232 3224 3223 in credit card field
        - Set date range from the first day of the previous month to the first day of this month
        - Click Tables button
        - Extract the table under master heading and save it to C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx

        **CORRECT OUTPUT:**
        ```python
        def aba_agent():
            try:
                import sys, os
                import requests
                import time
                import json
                import traceback
                import datetime
                import pandas as pd
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.common.by import By
                from xpath_find import main
                from element_confirmation import element_status
                from verify_xpath import mod_xpath
                import gemini_code_correction

                import sys
                import os
                sys.path.append(r"D:\\AgentFlow")
                
                # Import standard functions from datas.supporting_files
                from datas.supporting_files.launch_url import open_url_with_selenium
                from datas.supporting_files.office365_email import fetch_latest_email_graph 
                from datas.supporting_files.imap_email import fetch_latest_email_code

                def execute_step(driver, var_name, description,json_xpath):
                    var_name=var_name
                    current_xpath = json_xpath.get(var_name)
                    file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
                    if current_xpath == "Not_assigned":
                        raw_xpath = main(description, driver)
                        # Verify status
                        is_valid, current_xpath = element_status(var_name, raw_xpath, driver)
                        # Update JSON
                        json_xpath[var_name] = current_xpath

                        with open(JSON_PATH, "w") as f:
                            json.dump(json_xpath, f, indent=4)
            
                    # 2. Code Generation & Execute
                    if not os.path.exists(file_path):
                        current_xpath = main(description, driver)
                        gemini_code_correction.code_correction(description, current_xpath, file_path, var_name, driver, {userid})
                        module_path = f"{proj_name}.{task_name}.var_name"
                        module = importlib.import_module(module_path)
                        module.run(driver)
                    else:
                        module_path = f"{proj_name}.{task_name}.var_name"
                        module = importlib.import_module(module_path)
                        module.run(driver)

                # Initialize JSON
                json_xpath = {{}}
                if os.path.exists("json_info/json_xpath.json"):
                    with open("json_info/json_xpath.json", "r") as f:
                        json_xpath = json.load(f)
                else:
                    os.makedirs("json_info", exist_ok=True)
                
                # Step 1: Launch URL using standard function
                url = "http://54.90.203.61/"
                driver = open_url_with_selenium(url)

                # Step 2: Type username as admin
                var_name = "username_field"
                description = "Type username as admin"
                execute_step(driver, var_name, description, json_xpath)

                # Step 3: Type password as 1234
                var_name = "password_field"
                description = "Type password as 1234"
                execute_step(driver, var_name, description, json_xpath)

                # Step 4: Click Sign In button
                var_name = "signin_button"
                description = "Click Sign In button"
                execute_step(driver, var_name, description, json_xpath)

                # Step 5: Type 123456 in OTP field
                var_name = "otp_field"
                description = "Type 123456 in OTP field"
                execute_step(driver, var_name, description, json_xpath)

                # Step 6: Click Verify button
                var_name = "verify_button"
                description = "Click Verify button"
                execute_step(driver, var_name, description, json_xpath)

                # Step 7: Click Forms button
                var_name = "forms_button"
                description = "Click Forms button"
                execute_step(driver, var_name, description, json_xpath)

                # Step 8: Select India from country dropdown
                var_name = "country_dropdown"
                description = "Select India from country dropdown"
                execute_step(driver, var_name, description, json_xpath)

                # Step 9: Select Tamil Nadu from state/province dropdown
                var_name = "state_province_dropdown"
                description = "Select Tamil Nadu from state/province dropdown"
                execute_step(driver, var_name, description, json_xpath)

                # Step 10: Select Coimbatore in city dropdown
                var_name = "city_dropdown"
                description = "Select Coimbatore in city dropdown"
                execute_step(driver, var_name, description, json_xpath)

                # Step 11: Click Select Skills button
                var_name = "select_skills_button"
                description = "Click Select Skills button"
                execute_step(driver, var_name, description, json_xpath)

                # Step 12: Check Python checkbox
                var_name = "python_checkbox"
                description = "Check Python checkbox"
                execute_step(driver, var_name, description, json_xpath)

                # Step 13: Type credit card number
                var_name = "credit_card_field"
                description = "Type 2323 3232 3224 3223 in credit card field"
                execute_step(driver, var_name, description, json_xpath)

                # Step 14: Calculate date range (DIRECT CODE)
                today = datetime.date.today()
                first_day_of_this_month = today.replace(day=1)
                last_day_of_previous_month = first_day_of_this_month - datetime.timedelta(days=1)
                first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

                start_date = first_day_of_previous_month.strftime("%m/%d/%Y")
                end_date = first_day_of_this_month.strftime("%m/%d/%Y")

                # Step 15: Set date range picker
                var_name = "date_range_picker"
                description = f"Set date range from {{start_date}} to {{end_date}}"
                execute_step(driver, var_name, description, json_xpath)

                # Step 16: Click Tables button
                var_name = "tables_button"
                description = "Click Tables button"
                execute_step(driver, var_name, description, json_xpath)

                # Step 17: Extract the table
                var_name = "extract_master_table"
                description = "Extract the table under master heading and save it to C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
                execute_step(driver, var_name, description, json_xpath)

            except Exception as e:
                os.makedirs("json_info", exist_ok=True)
                with open("json_info/exception_info.json", "w") as f:
                    json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)
            finally:
                if 'driver' in locals():
                    driver.quit()
        ```

        ================================================================================
        MANDATORY RULES
        ================================================================================
        1. **Function Definition**
        - Wrap all code in a single function: `def aba_agent():`
        - Function takes **no arguments**
        - Do **not** call the function inside the code

        2. **Import Statements**
        - ALL imports must be placed inside the aba_agent() function block, not at the top of the file
        - Always import standard functions from datas.supporting_files at the beginning of try block:
        ```python
                from datas.supporting_files.launch_url import open_url_with_selenium
                from datas.supporting_files.execute_step_code import execute_step
                from datas.supporting_files.office365_email import fetch_latest_email_graph  # If Office 365 email needed
                from datas.supporting_files.imap_email import fetch_latest_email_code  # If IMAP email needed
        ```
        - Dynamic imports `from {{proj_name}}.{{task_name}} import {{var_name}}` are handled inside execute_step function

        3. **Try/Except/Finally**
        - Always use:
        ```python
            except Exception as e:
                ...
            finally:
                if 'driver' in locals():
                    driver.quit()
        ```

        4. **Reference Functions**
        - open_url_with_selenium(), execute_step(), email fetching functions, and queue functions must ALL be defined INSIDE aba_agent()
        - These functions should be declared at the top of the try block, before their usage

        5. **Driver Variable**
        - open_url_with_selenium() always returns 'driver' variable
        - Use this returned driver for all subsequent operations
        - Pass driver to execute_step() and all module .run() calls

        6. **Action Classification**
        - **XPATH ACTIONS (External Module Pattern)**: ALL web element interactions including typing, clicks, extracts, scrolls, checkboxes, dropdowns, table extraction, date pickers, navigation, alerts, file uploads, drag/drop, hover
        - **DIRECT CODE**: Non-web operations like variable assignment, file operations, Excel operations, date calculations, string operations, conditionals, loops, API calls
        - **REFERENCE FUNCTIONS**: URL Launch, Mail Read, Queue operations - declare functions inside aba_agent() and call them

        7. **Unique Variable Names**
        - Each `var_name` must be unique across the entire project
        - For duplicate element names, use incremented names: continue_button, continue_button1, continue_button2

        8. **Required External Imports**
        - main, element_status, mod_xpath must be imported from external files at the top of try block:
        ```python
            from xpath_find import main
            from element_confirmation import element_status
            from verify_xpath import mod_xpath
            import gemini_code_correction
        ```

        9. **Output Format**
        - Output must contain **only valid Python code** (no explanations, markdown, or comments outside the code)
        - Follow the exact pattern demonstrated in the example above

        ================================================================================
        OUTPUT REQUIREMENTS
        ================================================================================
        Generate complete, executable Python code following all the rules above.
        The code must be production-ready with proper error handling and resource cleanup.
        """
    
    response = chat.send_message(prompt)
    code_to_write = response.text

    # Remove markdown code block markers
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()

    missing_imports = get_missing_imports(code_to_write)
    code_to_write = add_missing_imports_to_code(code_to_write, missing_imports)

    print(f"# Missing Imports Added : {missing_imports}")
    xpath_json_data=xpath_json(code_to_write)
    return code_to_write,xpath_json_data

def get_missing_imports(code_to_write):
    """
    Identifies only the missing import statements without modifying the code
    """
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    
    validation_prompt = f"""
    You are a Python import analyzer. Analyze the following code and identify ONLY the missing import statements.
    
    CODE TO ANALYZE:
```python
{code_to_write}
```
    
    INSTRUCTIONS:
    1. Scan through the code and identify all modules/functions being used
    2. Check which imports are already present in the code
    3. Identify ONLY the missing imports that are needed but not imported
    4. Return ONLY the missing import statements, one per line
    5. DO NOT include imports that are already present in the code
    6. DO NOT return the entire code
    7. DO NOT add explanations
    8. Check for standard Python modules like: re, datetime, time, os, sys, json, traceback, shutil, math, random, etc.
    9. Check for third-party modules like: requests, pandas, numpy, BeautifulSoup (bs4), etc.
    
    Common modules to check:
    - re (for regex operations like re.search, re.match, re.findall)
    - datetime (for date operations)
    - time (for time operations like time.sleep, time.time)
    - os (for file operations)
    - sys (for system operations)
    - json (for JSON operations)
    - traceback (for exception handling)
    - shutil (for file copy/move operations)
    - imaplib (for email operations)
    - email (for email parsing)
    - pandas (for DataFrame operations)
    - requests (for HTTP requests)
    - BeautifulSoup from bs4 (for HTML parsing)
    
    RESPONSE FORMAT:
    Return ONLY the missing import statements like this:
    import re
    import datetime
    from bs4 import BeautifulSoup
    
    If no imports are missing, return exactly: NO_MISSING_IMPORTS
    
    Return nothing else - no explanations, no markdown, no code blocks.
    """
    
    response = chat.send_message(validation_prompt)
    missing_imports = response.text.strip()
    
    # Clean up any markdown formatting
    if missing_imports.startswith("```"):
        lines = missing_imports.split("\n")
        missing_imports = "\n".join(lines[1:-1])
    
    missing_imports = missing_imports.strip()
    if missing_imports.endswith("```"):
        missing_imports = missing_imports[:-3].strip()
    
    return missing_imports

def add_missing_imports_to_code(code_to_write, missing_imports):
    """
    Adds missing imports to the existing code without modifying anything else.
    Also moves any imports outside the function inside it (before try block).
    """
    if missing_imports == "NO_MISSING_IMPORTS" or not missing_imports:
        return code_to_write
    
    lines = code_to_write.split("\n")
    
    # Step 1: Collect imports that are outside the function (to move inside)
    outside_imports = []
    lines_to_keep = []
    inside_function = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if we're entering the function
        if "def aba_agent():" in line:
            inside_function = True
            lines_to_keep.append(line)
            continue
        
        # If outside function and it's an import (not comment), collect it
        if not inside_function:
            if (stripped.startswith("import ") or stripped.startswith("from ")) and not stripped.startswith("#"):
                outside_imports.append(stripped)
                continue  # Skip adding this line, we'll move it inside
        
        # Keep all other lines as-is
        lines_to_keep.append(line)
    
    # Step 2: Find where to insert imports (after def, before try)
    insert_position = -1
    last_import_position = -1
    found_function = False
    found_try = False
    
    for i, line in enumerate(lines_to_keep):
        stripped = line.strip()
        
        # Find function definition
        if "def aba_agent():" in line:
            found_function = True
            continue
        
        if found_function and not found_try:
            # Look for existing imports before try:
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_position = i
            elif stripped == "try:":
                found_try = True
                # Insert before try:
                if last_import_position != -1:
                    insert_position = last_import_position + 1
                else:
                    insert_position = i
                break
    
    # Fallback: insert right after function definition if no try: found
    if insert_position == -1:
        for i, line in enumerate(lines_to_keep):
            if "def aba_agent():" in line:
                insert_position = i + 1
                break
    
    # Step 3: Collect all existing imports inside the function to check for duplicates
    existing_imports = set()
    for i, line in enumerate(lines_to_keep):
        stripped = line.strip()
        if i > insert_position - 10 and i < insert_position + 10:  # Check around insert position
            if stripped.startswith("import ") or stripped.startswith("from "):
                existing_imports.add(stripped)
    
    # Step 4: Prepare imports to add (outside imports + missing imports)
    imports_to_add = []
    
    # Add outside imports (if not already present)
    for imp in outside_imports:
        if imp not in existing_imports:
            imports_to_add.append(imp)
    
    # Add missing imports (if not already present)
    if missing_imports and missing_imports != "NO_MISSING_IMPORTS":
        missing_import_lines = missing_imports.split("\n")
        for imp in missing_import_lines:
            imp_stripped = imp.strip()
            if imp_stripped and imp_stripped not in existing_imports:
                imports_to_add.append(imp_stripped)
    
    # Step 5: Insert all new imports with proper indentation (4 spaces - inside function, outside try)
    if imports_to_add:
        indented_imports = ["    " + imp for imp in imports_to_add]
        
        # Insert the imports in reverse order to maintain position
        for imp in reversed(indented_imports):
            lines_to_keep.insert(insert_position, imp)
    
    return "\n".join(lines_to_keep)

def analyze_dependencies(code):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    
    analysis_prompt = f"""# ROLE
You are a Python dependency analysis expert specializing in identifying required packages and generating requirements.txt files.

# CONTEXT
Analyze the following Python code:
{code}

# TASK
Analyze all import statements in the provided code and generate a requirements.txt file content.

# RULES
1. **Comprehensive Analysis**: Identify all import statements in the code (import X, from X import Y).

2. **Standard Library Exclusion**: Exclude Python standard library modules (e.g., os, sys, time, datetime, json, traceback, re, math, random, etc.) as they don't require pip installation.

3. **Local Module Exclusion**: Exclude local/custom modules that are part of the project:
   - Imports from files in the same project directory
   - Common patterns: single word imports without dots that are not known packages
   - Examples to exclude: xpath_find, element_confirmation, verify_xpath, config, utils, helpers

4. **Package Name Mapping**: Map import names to their correct pip package names when they differ:
   - "import cv2" → "opencv-python"
   - "from PIL import Image" → "Pillow"
   - "import sklearn" → "scikit-learn"
   - "from bs4 import BeautifulSoup" → "beautifulsoup4"
   - "import fitz" → "pymupdf"

5. **Third-Party Package Recognition**: Only include well-known third-party packages available on PyPI:
   - Examples: selenium, requests, pandas, numpy, flask, django, etc.

6. **Deduplicate**: If the same package is imported multiple times or in different ways, list it only once.

7. **Version Agnostic**: Do not specify version numbers unless critical for compatibility.

8. **One Package Per Line**: List each package on a separate line as per requirements.txt format.

9. **Verify Authenticity**: Only include packages that actually exist on PyPI. Do not guess or make up package names.

# OUTPUT FORMAT
Provide only the requirements.txt file content with one package per line:

package1
package2
package3

If no external packages are required, respond with:
# No external packages required. All imports are from Python standard library or local modules."""
    
    response = chat.send_message(analysis_prompt)
    requirements_content = response.text
    
    # Clean up if response contains markdown code blocks
    if requirements_content.startswith("```"):
        requirements_content = "\n".join(requirements_content.strip().split("\n")[1:-1])
    
    return requirements_content
# input_info="lauch the https://droidal.ai/login type username as kishore type password as 2610 click login button then extract text from filter agent search input field if text found print that then select the autopay option from benefits dropdown then click the information button then extract the info table and write the data in to data.xlsx file on desktop location"
# proj_name="proj_11"
# task_name="task_11"
# userid="4"
# code_run,xpath_json_data=gemini_response(input_info,proj_name,task_name,userid)
# file_path="backup.py"
# json_file="json_info/json_xpath.json"
# with open(file_path, "w", encoding="utf-8") as f:
#     f.write(code_run)
# with open(json_file, "w", encoding="utf-8") as f:
#     json.dump(xpath_json_data, f, ensure_ascii=False, indent=4)