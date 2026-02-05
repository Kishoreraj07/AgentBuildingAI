import google.generativeai as genai
import config
import json
def citrix_json(code):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""Here is the code: {code}

Analyze the code thoroughly and identify all string values that are used as element identifiers or variable names for web elements. 
These identifiers may be:
- Assigned to variables like `var_name`, `element_id`, `locator`, etc.
- Passed as arguments to functions that interact with web elements (e.g., text_data, table_df, click_element, etc.)
- Used to identify or describe web elements being extracted or interacted with

Generate a JSON object where:
    - Each key is the string value (identifier name) found in the code that represents a web element.
    - Each value is "Not_assigned".
{{"username_input":"Not_assigned","password_input":"Not_assigned",...}}

If no such identifier is found in the code, return an empty JSON {{}}.

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

    task_info={
    "Proj_file_name": proj_name,
    "Task_file_name": task_name
    }

    with open("json_info/task_info.json", "w") as f:
        json.dump(task_info, f, indent=4)
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
    prompt = f"""
        Here is the User Requirement: {input}

        Based on the above requirement, generate the **Web Automation Code**.

        ================================================================================
        STANDARD FUNCTION IMPORTS (from datas.supporting_files)
        ================================================================================
        Instead of defining functions internally, import these standard functions:
        Here it's have files and functions like

        1. **URL Launch Function:**
        from datas.supporting_files.citrix_process.launch_url import open_url_with_selenium
        driver = open_url_with_selenium(url)
           - Always returns 'driver' variable
           - Use this driver variable for all subsequent operations

        2. **Email Fetching - Microsoft Graph API (Office 365):**
        from datas.supporting_files.citrix_process.office365_email import fetch_latest_email_graph
        code = fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                                      sender_filter=None, subject_filter=None, timeout=180)

        3. **Email Fetching - IMAP (Gmail, Yahoo, Custom Domains):**
        from datas.supporting_files.citrix_process.imap_email import fetch_latest_email_code
        code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                     folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

        4. **Excel Read from File**
            Excel Read Function Usage Based on Row Limits:

                a. Both start and end row limits:
                file_full_path = "path/to/file.xlsx"
                start_row = 5
                end_row = 100
                file_data_frame = excel_read_file(file_full_path, start_row, end_row)
                optionally, pass sheet_name argument in positional.(if included)

                b. Only start row limit (read from specific row onwards):
                file_full_path = "path/to/file.xlsx"
                start_row = 5
                file_data_frame = excel_read_file(file_full_path, start_row=start_row)
                Do not pass the end_row argument, end_row will be set to None.
                optionally, pass sheet_name argument in positional.(if included)

                c. Only end row limit (read until specific row):
                file_full_path = "path/to/file.xlsx"
                end_row = 100
                file_data_frame = excel_read_file(file_full_path, end_row=end_row)
                Do not pass the start_row argument, start_row will be set to 1.
                optionally, pass sheet_name argument in positional.(if included)

                d. sheet_name limit (read specific sheet):
                file_full_path = "path/to/file.xlsx"
                sheet_name = "Sheet1"
                file_data_frame = excel_read_file(file_full_path, sheet_name=sheet_name)
                Do not pass start_row or end_row arguments but pass sheet_name argument in positional.
                

                e. No row limits (read entire file):
                file_full_path = "path/to/file.xlsx"
                file_data_frame = excel_read_file(file_full_path)
                No need to pass start_row or end_row arguments.

                Summary: Pass only the arguments that match the user's requirements. Use positional arguments when both limits are provided, and use keyword arguments when only one limit is specified.

        5.**Message Box**
        from datas.supporting_files.citrix_process.message_box import popup_message_box
        popup_message_box(<msg to populate>)

        
        6.**Extract text from Web / Some Field**
        from datas.supporting_files.citrix_process.text_extract import text_data
        var_name = "action_name"
        description = "Full action description"
        org_path=os.cwd()
        <relevant_variable_declare_here>=text_data(var_name, description,{userid},org_path)

        7.**Element Exists**
        from datas.supporting_files.citrix_process.element_exist import element_status
        var_name = "action_name"
        description = "Full action description"
        org_path=os.cwd()
        <status returns as True or False declare variable here>=element_status(var_name, description,{userid},org_path)

        8.**Table Extract (Extract a Table from current page or image )**
        from datas.supporting_files.citrix_process.table_extract import table_df
        var_name = "action_name"
        description = "Full action description"
        org_path=os.cwd()
        table_data_df=table_df(var_name, description,{userid},org_path)

        9.**Time Delay like Wait for 10 sec or 5 sec**
        from datas.supporting_files.citrix_process.time_delay import time_delay
        time_delay(<respective seconds as int type>)

        10. **PDF Split (Page wise)**
        from datas.supporting_files.citrix_process.pdf_splitter import split_pdf
        pdf_path=<pdf file full path>
        page_limit=<limit pages per split in int type>
        dest_folder=<destination folder for splitted files to save if doesn't provide any means just keep the actual pdf file folder path>
        pdf_split(pdf_path,page_limit,dest_folder)

        11. **PDF Highlighter (for open the file and highlight or highlight the text on pdf and save)**
        from datas.supporting_files.citrix_process.pdf_highlighter import highlight_text_in_pdf
        pdf_path=<pdf file full path>
        text=<text to highlight>
        output_path=<save as seperate file means that path else same pdf path>
        highlight_text_in_pdf(pdf_path,text,output_path)

        12.**Mail Attachement Download (using Microsoft Graph API with tenant_id, client_id, client_secret)**
            from datas.supporting_files.citrix_process.ms_mail_attach_download import download_outlook_attachments
            from_mail = <from_mail_address>
            tenant = <tenant_id>
            client_id = <client_id>
            client_secret = <client_secret>
            download_path = <a full folder path from given path on the requirement>
            download_outlook_attachments(from_mail,tenant,client_id,client_secret,download_path)

        13. **Mail Send (using Microsoft Graph API with tenant_id, client_id, client_secret, attachments-optional)**
            from datas.supporting_files.citrix_process.office365_mail_send import send_mail_ms_graph
            from_mail = <from_mail_address>
            to_mail = <to_mail_address>
            tenant = <tenant_id>
            client_id = <client_id>
            client_secret = <client_secret>
            subject       = <mail subject>
            body          = <mail body>
            attachments   = <list of attachments>
            send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments)

            Rules for subject and body assigning:
                • If only `body` is provided and `subject` is empty or not provided, automatically generate a suitable subject based on the body content.
                • If only `subject` is provided and `body` is empty or not provided, automatically generate a meaningful body based on the subject.
                • If both are provided, use them as-is.
                • If attachments are provided, attach them to the email.(optional)

            Execution:
                send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments=None)

        14. **Mail Read (using Microsoft Graph API with tenant_id, client_id, client_secret)**
            from datas.supporting_files.citrix_process.office365_mail_read import read_latest_mail_ms_graph
            from_mail = <from_mail_address>
            tenant = <tenant_id>
            client_id = <client_id>
            client_secret = <client_secret>
            body = read_latest_mail_ms_graph(from_mail, tenant, client_id, client_secret)

            returns:
                - body (plain-text email body, cleaned from HTML)

        15. **OTP extraction from mail**(passing mail body directly)
            from datas.supporting_files.citrix_process.otp_mail_read import gemini_extract_otp_from_mail
            mail_body = <mail_body>
            otp = gemini_extract_otp_from_mail(mail_body)


        16. **For Execute Step**
        from datas.supporting_files.citrix_process.execute_step_code import execute_step
        import os
        cwd=os.getcwd()
        var_name = "action_name"
        description = "Full action description"
        execute_step(var_name,description,{userid},cwd)

            RULE for Execute Step:
            - The execute_step function must be called only with the arguments: var_name, description, {userid}, cwd
            - If any additional information is required, include it inside the description using a formatted string instead of passing as a extra added argument

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
        - **Never wrap email logic** in var_name / citrix_data / .run() pattern
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
            from datas.supporting_files.citrix_process.getqueue import get_task_from_queue
            api_key=<which is passed>
            records, rowid, status_val, status_res, startTime, queuename, queueemail=get_task_from_queue(api_key)
            
                Return values explanation:
                    - records      : The complete current queue item data (dict/object)
                                    Required for update queue status operation
                    - rowid        : Unique identifier for the queue item (Just for reference)
                    - status_val   : Current status of queue item (string: "inprogress" or "new")
                                    Use this for reference/logging only
                    - status_res   : Boolean flag indicating if processing should continue
                                    If True: Proceed with processing
                                    If False: Stop processing and end iteration
                    - startTime    : Timestamp when item processing started
                                    Required for update queue status operation
                    - queuename    : Name of the queue (Just for reference)
                    - queueemail   : Email associated with the queue item (Just for reference)

        RULE 3: Upload Queue
            ONLY when user explicitly mentions uploading/adding values to queue:
            from datas.supporting_files.citrix_process.update_queue import queue_upload
            api_key=<which is passed>
            queue_upload(api_key,<data_to_pushed_on_queue>)

        RULE 4: Update Queue Status
            ONLY when user explicitly mentions updating status of queue items:
            from datas.supporting_files.citrix_process.queue_update_status import queue_update
            statusupdate:<if user says as success means "success" ,if user says failed means "failed" it can either be success or failed>
            api_key=<which is passed>
            queue_update(api_key,<data_to_pushed_on_queue>, statusupdate, startTime)
                
                Parameters:
                    - api_key        : Authentication key (passed as function parameter)
                    - records        : Complete queue item data (obtained from get_task_from_queue)
                    - rowid          : Queue item unique identifier (obtained from get_task_from_queue)
                    - status_update  : Status to set, must be EXACTLY one of:
                                    * "success" - when operation completed successfully
                                    * "failed"  - when operation failed
                    - startTime      : Processing start timestamp (obtained from get_task_from_queue)

                Status determination logic:
                    - If user says "success", "completed", "done" → use "success"
                    - If user says "failed", "error", "unsuccessful" → use "failed"
                    - ONLY these two values are valid: "success" or "failed"

        ================================================================================
        CODE STRUCTURE INSTRUCTIONS FOR WEB AUTOMATION USING SELENIUM
        ================================================================================

        ================================================================================
        ACTION CLASSIFICATION AND CODE PATTERN RULES
        ================================================================================

        **RULE 1: ALL ACTIONS (Use Complete Module Pattern)**
        ALL web element interactions must use external module files with the FULL PATTERN:
        - Type actions (label, input, search field)
        - Click actions (buttons, links, checkboxes, radio buttons, icons)
        - Extract/Read actions (get text, get attribute values, scrape data)
        - Scroll actions (scroll to element, scroll page)
        - Navigation actions (browser back, forward, refresh)
        - Alert/Popup handling (accept alert, dismiss alert)
        - Dropdown selection (select from dropdown, choose option)
        - Date picker interactions (calendar selection, date range selection)
        - Multi-step complex interactions requiring state management
        - File upload/download interactions
        - Drag and drop actions
        - Hover actions
        - Any other web element interaction

        **Pattern for ALL Element Actions:**
        ```python
        var_name = "action_name"
        description = "Full action description"
        import os
        cwd=os.getcwd()
        execute_step(var_name,description,{userid},cwd)

        NOTE:
         - the execute_step function no need to call for get text or get element status like actions
        ```

        **RULE 2: DIRECT CODE IMPLEMENTATION (No Pattern Required)**
        These actions do NOT involve web elements and should be written directly as logical code:
        - Variable assignment (assign value, declare variable, set variable)
        - File operations (open file, save file, delete file, move file, copy file)
        - Directory operations (create folder, delete folder, list files)
        - Date/Time calculations (get current date, calculate date difference, format date)
        - String operations (concatenate, split, replace, format)
        - Mathematical operations (calculate, sum, average)
        - Data transformations (convert data types, parse JSON, format data)
        - Conditional logic (if-else conditions based on variables)
        - Loop iterations (for loops, while loops over data)
        - API calls (not web browser related)

        **Pattern for DIRECT CODE:**
        Simply write the Python code directly without using var_name, citrix_data, or any pattern structure.

        Example:
        ```python
        # Calculate date
        from datetime import datetime, timedelta
        today = datetime.now()
        previous_month = today - timedelta(days=30)
        ```

        **RULE 3: REFERENCE FUNCTIONS**
        If actions are related to:
        - Launching URL → Declare open_url_with_selenium() function inside aba_agent() and call it
        - Mail Read → Declare email fetching function inside aba_agent() and call it
        - Queue Upload → Declare update_queue functions inside aba_agent() and call it
        - Extract text → Declare text_data function inside aba_agent() and call it
        - Extract table → Declare table_df function inside aba_agent() and call it
        - Element exists → Declare element_status function inside aba_agent() and call it
        - Execute Step → Declare execute_step() function inside aba_agent() and use for all element actions


        ================================================================================
        CORRECT CODE PATTERN EXAMPLE (MANDATORY)
        ================================================================================
        User Requirement:
        - Launch the URL http://54.90.203.61/
        - Type username as admin
        - Type password as 1234
        - Click Sign In button
        - Type 123456 in OTP field
        - Check Verify button exists
        - If Verify button exists Click Verify button and end the if
        - Click Forms button
        - Extract text from Group Name field
        - Message box the Group Name
        - Select India from country dropdown
        - Select Tamil Nadu from state/province dropdown
        - Select Coimbatore in city dropdown
        - Click Select Skills button
        - Check Python checkbox
        - Type 2323 3232 3224 3223 in credit card field
        - Set date range from the first day of the previous month to the first day of this month
        - Click Tables button
        - Extract the table under master heading and store in to variable table_data
        - save table_data data in it to C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx
        - Read the rpamaster.xlsx Excel and store into a variable df
        - Upload the df into the queue api key is "kdkfjkefjdjfkdfk"
        - Iterate the each record on queue by one by one bt Get queue until status result is False
        - Update the queue status as success
        - End the get queue loop and message popup as process completed

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

                import sys
                import os
                
                # Import standard functions from datas.supporting_files
                from datas.supporting_files.citrix_process.launch_url import open_url_with_selenium
                from datas.supporting_files.citrix_process.office365_email import fetch_latest_email_graph 
                from datas.supporting_files.citrix_process.imap_email import fetch_latest_email_code
                from datas.supporting_files.citrix_process.execute_step_code import execute_step
                from datas.supporting_files.citrix_process.text_extract import text_data
                from datas.supporting_files.citrix_process.time_delay import time_delay
                from datas.supporting_files.citrix_process.excel_read import excel_read_file
                from datas.supporting_files.citrix_process.update_queue import queue_upload
                from datas.supporting_files.citrix_process.element_exist import element_status
                from datas.supporting_files.citrix_process.getqueue import get_task_from_queue
                from datas.supporting_files.citrix_process.queue_update_status import queue_update
                from datas.supporting_files.citrix_process.message_box import popup_message_box
                from datas.supporting_files.citrix_process.table_extract import table_df
                

                
                
                
                #current working directory
                cwd=os.getcwd()
                
                # Step 1: Launch URL using standard function
                url = "http://54.90.203.61/"
                driver = open_url_with_selenium(url)

                # Step 2: Type username as admin
                var_name = "username_field"
                description = "Type username as admin"
                execute_step(var_name,description,{userid},cwd)

                # Step 3: Type password as 1234
                var_name = "password_field"
                description = "Type password as 1234"
                execute_step(var_name,description,{userid},cwd)

                # Step 4: Click Sign In button
                var_name = "signin_button"
                description = "Click Sign In button"
                execute_step(var_name,description,{userid},cwd)

                # Step 5: Type 123456 in OTP field
                var_name = "otp_field"
                description = "Type 123456 in OTP field"
                execute_step(var_name,description,{userid},cwd)

                # Step 6: Check Verify button exists
                var_name = "verify_button_exists_status"
                description = "Check Verify button exists or not"
                verify_button_status=element_status(var_name,description,{userid},cwd)

                # Step 7: If verify button exists Click Verify button
                if verify_button_status:
                    var_name = "verify_button"
                    description = "Click Verify button"
                    execute_step(var_name,description,{userid},cwd)
                #Verify button clicks if condition ends

                # Step 8: Click Forms button
                var_name = "forms_button"
                description = "Click Forms button"
                execute_step(var_name,description,{userid},cwd)

                # Step 9: Extract the Group Name
                var_name="group_name_extract"
                description = "extract the group name from the group name field"
                group_name_extract=text_data(var_name,description,{userid},org_path)

                # Step 10: Message box the Group Name
                popup_message_box(group_name_extract)

                # Step 11: Select India from country dropdown
                var_name = "country_dropdown"
                description = "Select India from country dropdown"
                execute_step(var_name,description,{userid},cwd)

                # Step 12: Select Tamil Nadu from state/province dropdown
                var_name = "state_province_dropdown"
                description = "Select Tamil Nadu from state/province dropdown"
                execute_step(var_name,description,{userid},cwd)

                # Step 13: Select Coimbatore in city dropdown
                var_name = "city_dropdown"
                description = "Select Coimbatore in city dropdown"
                execute_step(var_name,description,{userid},cwd)

                # Step 14: Click Select Skills button
                var_name = "select_skills_button"
                description = "Click Select Skills button"
                execute_step(var_name,description,{userid},cwd)

                # Step 15: Check Python checkbox
                var_name = "python_checkbox"
                description = "Check Python checkbox"
                execute_step(var_name,description,{userid},cwd)

                # Step 16: Type credit card number
                var_name = "credit_card_field"
                description = "Type 2323 3232 3224 3223 in credit card field"
                execute_step(var_name,description,{userid},cwd)

                # Step 17: Calculate date range (DIRECT CODE)
                today = datetime.date.today()
                first_day_of_this_month = today.replace(day=1)
                last_day_of_previous_month = first_day_of_this_month - datetime.timedelta(days=1)
                first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

                start_date = first_day_of_previous_month.strftime("%m/%d/%Y")
                end_date = first_day_of_this_month.strftime("%m/%d/%Y")

                # Step 18: Set date range picker
                var_name = "date_range_picker"
                description = f"Set date range from {{start_date}} to {{end_date}}"
                execute_step(var_name,description,{userid},cwd)

                # Step 19: Click Tables button
                var_name = "tables_button"
                description = "Click Tables button"
                execute_step(var_name,description,{userid},cwd)

                # Step 20: Extract the table
                var_name = "extract_master_table"
                description = "Extract the table under master heading"
                table_data=table_df(var_name,description,{userid},cwd)

                #Step 21: Write the table_data in to the excel file
                file_path="C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
                table_data.to_excel(file_path, index=False)

                #Step 22: Read the rpamaster.xlsx file
                file_path="C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
                df=excel_read_file(file_path)

                #Step 23: Upload the df into queue
                api_key="kdkfjkefjdjfkdfk"
                queue_upload(api_key,df)

                #Step 24: Get Queue loop
                while True:
                    records, rowid, status_val, status_res, startTime, queuename, queueemail=get_task_from_queue(api_key)
                    # Loop until status result as False
                    if not status_res:
                        break
                    #Step 24: Update Queue status success
                    from datas.supporting_files.citrix_process.queue_update_status import queue_update
                    queue_upload(api_key,records,"success",startTime)
                
                #Step 26:Message popup as Process Completed outside the get queue loop
                popup_messagebox("Process Completed)

            except Exception as e:
                os.makedirs("json_info", exist_ok=True)
                with open("json_info/exception_info.json", "w") as f:
                    json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)
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
                from datas.supporting_files.citrix_process.launch_url import open_url_with_selenium
                from datas.supporting_files.citrix_process.execute_step_code import execute_step
                from datas.supporting_files.citrix_process.office365_email import fetch_latest_email_graph  # If Office 365 email needed
                from datas.supporting_files.citrix_process.imap_email import fetch_latest_email_code  # If IMAP email needed
                from datas.supporting_files.citrix_process.excel_read import excel_read_file #If Excel read needed
                from datas.supporting_files.citrix_process.message_box import popup_message_box #If Message box needed
                from datas.supporting_files.citrix_process.time_delay import time_delay #If time delay needed
                from datas.supporting_files.citrix_process.text_extract import text_data #If text extract is needed
                from datas.supporting_files.citrix_process.table_extract import table_df #If table extraction is needed
                from datas.supporting_files.citrix_process.update_queue import queue_upload #If Queue upload is required
                from datas.supporting_files.citrix_process.queue_update_status import queue_update #If Queue update status is required
                from datas.supporting_files.citrix_process.element_exist import element_status #If element exists or not is required
                from datas.supporting_files.citrix_process.pdf_splitter import split_pdf #If pdf splitter is required
                from datas.supporting_files.citrix_process.pdf_highlighter import highlight_text_in_pdf #If pdf highlighter is required
                from datas.supporting_files.citrix_process.ms_mail_attach_download import download_outlook_attachments #If Download Attachment from mail is required
                from datas.supporting_files.citrix_process.office365_mail_send import send_mail_ms_graph #If Office 365 email send is required with proper data(client_id,client_secret,tenant_id, attachment_paths)
                from datas.supporting_files.citrix_process.otp_mail_read import gemini_extract_otp_from_mail #If OTP extraction from mail is required
                from datas.supporting_files.citrix_process.office365_mail_read import read_latest_mail_ms_graph #If Office 365 email read is required with proper data(client_id,client_secret,tenant_id)
        ```

        3. **Try/Except/Finally**
        - Always use:
        ```python
            except Exception as e:
                ...
        ```

        4. **Reference Functions**
        - open_url_with_selenium(), execute_step(), email fetching functions, and queue functions must ALL be defined INSIDE aba_agent()
        - These functions should be declared at the top of the try block, before their usage


        6. **Action Classification**
        - **ELEMENT ACTIONS (External Module Pattern)**: ALL web element interactions including typing, clicks, extracts, scrolls, checkboxes, dropdowns, table extraction, date pickers, navigation, alerts, file uploads, drag/drop, hover
        - **DIRECT CODE**: Non-web operations like variable assignment, file operations, Excel operations, date calculations, string operations, conditionals, loops, API calls
        - **REFERENCE FUNCTIONS**: URL Launch, Mail Read, Queue operations - declare functions inside aba_agent() and call them

        7. **Unique Variable Names**
        - Each `var_name` must be unique across the entire project
        - For duplicate element names, use incremented names: continue_button, continue_button1, continue_button2

        8. **Output Format**
        - Output must contain **only valid Python code** (no explanations, markdown, or comments outside the code)
        - Follow the exact pattern demonstrated in the example above

        ================================================================================
        OUTPUT REQUIREMENTS
        ================================================================================
        Generate complete, executable Python code following all the rules above.
        The code must be production-ready with proper error handling and resource cleanup.
        The Final Code should contains only cmds tag about Step 1,Step 2,Step 3 ..... not additional explaining tags or any
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
    citrix_data_json=citrix_json(code_to_write)
    return code_to_write,citrix_data_json

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
# input_info=""""Open the URL https://www.worldometers.info/world-population/",
#         "Extract current world population count text",
#         "Show message popup as displays current world population",
#         "Extract the table under World Population by Country heading and store in to variable table_df",
#         "Show message popup with the total rows in the table_df",
#         "Write the table_df in to the excel world_population.xlsx excel file in the desktop location"""
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