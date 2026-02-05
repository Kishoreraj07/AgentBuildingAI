import google.generativeai as genai
import config
import json
import re

def normalize_var_name_lines(code_to_write: str) -> str:
    """
    Normalizes var_name assignments:
    - Converts f-strings like f"payment_checkbox_{i}" → "payment_checkbox"
    - Preserves indentation
    - Handles `var_name=` and `var_name =`
    """

    pattern = re.compile(
        r'''
        ^(?P<indent>\s*)                 # indentation
        var_name\s*=\s*                  # var_name =
        f?"                              # optional f"
        (?P<value>[^"{]*?)               # base text before {
        (_?\{[^}]+\})?                   # optional {_...}
        "                                # closing quote
        ''',
        re.MULTILINE | re.VERBOSE
    )

    def replacer(match):
        indent = match.group("indent")
        value = match.group("value").rstrip("_")  # remove trailing _
        return f'{indent}var_name = "{value}"'

    return pattern.sub(replacer, code_to_write)

def xpath_json(code):
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
    
    # prompt = f"""
    #     Here is the User Requirement: {input}

    #     Based on the above requirement, generate the **Web Automation Code**.

    #     ================================================================================
    #     SELENIUM-SPECIFIC FUNCTION IMPORTS (Use ONLY for Web Actions)
    #     ================================================================================
    #     The following functions should ONLY be used for Selenium web browser interactions.
    #     DO NOT use these for file operations, PDF operations, or other non-web tasks.

    #     1. **URL Launch (ONLY when explicitly asked to launch/open a URL):**
    #     from datas.supporting_files.launch_url import open_url_with_selenium
    #     driver = open_url_with_selenium(url)

    #     2. **Web Element Interactions (Click, Type, Hover, Wait, Dropdown):**

    #     For ANY web element interaction including Click, Type, Hover, Element Wait, Dropdown Selection, Dropdown Click, or Scroll operations, you MUST use the following standardized format:
    #     ```python
    #     from datas.supporting_files.execute_step_code import execute_step

    #     var_name = "action_name"
    #     description = "Full action description"
    #     cwd = os.getcwd()

    #     execute_step(driver, var_name, description, {{userid}}, cwd)
    #     ```

    #     **CRITICAL RULES:**
    #     1. ALWAYS use the execute_step function for web interactions - NO exceptions
    #     2. NEVER implement interactions directly (e.g., ActionChains, find_element, click(), send_keys())
    #     3. This applies to ALL interaction types:
    #     - Clicking elements
    #     - Typing/entering text
    #     - Hovering over elements
    #     - Waiting for elements
    #     - Dropdown selections
    #     - Scrolling to elements
    #     - Any other DOM interactions

    #     **INCORRECT - Do NOT use:**
    #     ```python
    #     # ❌ WRONG - Direct implementation
    #     element = driver.find_element(By.XPATH, "//div[@id='menu']")
    #     actions = ActionChains(driver)
    #     actions.move_to_element(element).perform()
    #     ```

    #     **CORRECT - Always use:**
    #     ```python
    #     # ✓ RIGHT - Using execute_step
    #     from datas.supporting_files.execute_step_code import execute_step

    #     var_name = "hover_menu"
    #     description = "Hover over the menu element"
    #     cwd = os.getcwd()

    #     execute_step(driver, var_name, description, {{userid}}, cwd)
    #     ```

    #     **Parameters:**
    #     - `var_name`: Descriptive identifier for the action (e.g., "click_submit", "type_username")
    #     - `description`: Clear, detailed description of what action to perform
    #     - `{{userid}}`: User identifier placeholder (keep as-is)
    #     - `cwd`: Current working directory obtained via os.getcwd()

    #     This standardized approach ensures consistency, maintainability, and proper error handling across all web automation tasks.

    #     3. **Text Extract from Web (ONLY for extracting text from web elements):**
    #     from datas.supporting_files.text_extract import text_data
    #     var_name = "action_name"
    #     description = "Full action description"
    #     cwd = os.getcwd()
    #     extracted_text = text_data(driver, var_name, description, {userid}, cwd)

    #     4. **Element Exists Check (ONLY for checking if web element exists):**
    #     from datas.supporting_files.element_exist import element_status
    #     var_name = "action_name"
    #     description = "Full action description"
    #     cwd = os.getcwd()
    #     exists_status = element_status(driver, var_name, description, {userid}, cwd)

    #     5. **Table Extract from Web (ONLY for extracting tables from web pages):**
    #     from datas.supporting_files.table_extract import table_df
    #     var_name = "action_name"
    #     description = "Full action description"
    #     cwd = os.getcwd()
    #     table_data = table_df(driver, var_name, description, {userid}, cwd)

    #     6. **Switch or Change the driver to the specific window (change the window handle to specific number)**
    #     from datas.supporting_files.window_handle import switch_to_window
    #     window_index=<window index number from user action as int type convert based on input of window index from user action as 3rd window as 2nd index>
    #     switch_to_window(driver,window_index)

    #     7. **Zoom in or Zoom out the driver/browser based on percentage**:
    #     from datas.supporting_files.browser_zoom import set_zoom
    #     percentage=<int type as number eg: 75 as for 75 %>
    #     set_zoom(driver,percentage)

    #     8. **Keyboard Button Actions**:

    #         **For Web/Selenium Actions (within browser context)**:
    #         Use Selenium's Keys when interacting with web elements:
            
    #         - Enter key:
    #         ```python
    #             driver.switch_to.active_element.send_keys(Keys.ENTER)
    #         ```
            
    #         - Tab key:
    #         ```python
    #             driver.switch_to.active_element.send_keys(Keys.TAB)
    #         ```

    #         **For Desktop/System-Level Actions (outside browser context)**:
    #         Use PyAutoGUI when the key press is not part of the web automation flow:
            
    #         - Enter key:
    #         ```python
    #             import pyautogui
    #             pyautogui.press('enter')
    #         ```
            
    #         - Tab key:
    #         ```python
    #             import pyautogui
    #             pyautogui.press('tab')
    #         ```

    #         **When to use which approach**:
    #         - Use Selenium Keys for actions within the browser (form submissions, navigation within web pages)
    #         - Use PyAutoGUI for system-level actions or when interacting with elements outside the browser context


    #         NOTE:
    #         This action cannot be in commended line like below
    #         #driver.switch_to.active_element.send_keys(Keys.ENTER)

    #     ================================================================================
    #     NON-SELENIUM FUNCTION IMPORTS (Use for specific operations)
    #     ================================================================================

    #     1. **Email Fetching - IMAP (Gmail, Yahoo, Custom Domains):**
    #     from datas.supporting_files.imap_email import fetch_latest_email_code
    #     code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
    #                                     folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

    #     2. Excel Read Function Usage Based on Row Limits:

    #         a. Both start and end row limits:
    #         file_full_path = "path/to/file.xlsx"
    #         start_row = 5
    #         end_row = 100
    #         file_data_frame = excel_read_file(file_full_path, start_row, end_row)
    #         optionally, pass sheet_name argument in positional.(if included)

    #         b. Only start row limit (read from specific row onwards):
    #         file_full_path = "path/to/file.xlsx"
    #         start_row = 5
    #         file_data_frame = excel_read_file(file_full_path, start_row=start_row)
    #         Do not pass the end_row argument, end_row will be set to None.
    #         optionally, pass sheet_name argument in positional.(if included)

    #         c. Only end row limit (read until specific row):
    #         file_full_path = "path/to/file.xlsx"
    #         end_row = 100
    #         file_data_frame = excel_read_file(file_full_path, end_row=end_row)
    #         Do not pass the start_row argument, start_row will be set to 1.
    #         optionally, pass sheet_name argument in positional.(if included)

    #         d. sheet_name limit (read specific sheet):
    #         file_full_path = "path/to/file.xlsx"
    #         sheet_name = "Sheet1"
    #         file_data_frame = excel_read_file(file_full_path, sheet_name=sheet_name)
    #         Do not pass start_row or end_row arguments but pass sheet_name argument in positional.
            

    #         e. No row limits (read entire file):
    #         file_full_path = "path/to/file.xlsx"
    #         file_data_frame = excel_read_file(file_full_path)
    #         No need to pass start_row or end_row arguments.

    #         Summary: Pass only the arguments that match the user's requirements. Use positional arguments when both limits are provided, and use keyword arguments when only one limit is specified.

    #     3. **Message Box:**
    #     from datas.supporting_files.message_box import popup_message_box
    #     popup_message_box(<message_to_display>)

    #     4. **Time Delay:**
    #         from datas.supporting_files.time_delay import time_delay
    #         time_delay(<seconds_as_int>)

    #     5. **PDF Split:**
    #         from datas.supporting_files.pdf_splitter import split_pdf
    #         pdf_file_path = <pdf_file_full_path>
    #         page_limit = <pages_per_split_as_int>
    #         destination_folder = <destination_folder_path>
    #         pdf_split(pdf_file_path, page_limit, destination_folder)

    #     6. **PDF Highlighter:**
    #         from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
    #         pdf_path = <pdf_file_full_path>
    #         text = <text_to_highlight>
    #         output_path = <output_path>
    #         highlight_text_in_pdf(pdf_path, text, output_path)

    #     7. **Extract Table from PDF:**
    #         from datas.supporting_files.pdf_xl import pdf_to_table_extract
    #         description = "Full action description"
    #         pdf_file = <Full pdf file path>
    #         table_df = pdf_to_table_extract(pdf_file,description)

    #     8. **Mail Send (using Microsoft Graph API with tenant_id, client_id, client_secret, attachments-optional)**
    #         from datas.supporting_files.office365_mail_send import send_mail_ms_graph
    #         from_mail = <from_mail_address>
    #         to_mail = <to_mail_address>
    #         tenant = <tenant_id>
    #         client_id = <client_id>
    #         client_secret = <client_secret>
    #         subject       = <mail subject>
    #         body          = <mail body>
    #         attachments   = <list of attachments>
    #         send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments)

    #         Rules for subject and body assigning:
    #             • If only `body` is provided and `subject` is empty or not provided, automatically generate a suitable subject based on the body content.
    #             • If only `subject` is provided and `body` is empty or not provided, automatically generate a meaningful body based on the subject.
    #             • If both are provided, use them as-is.
    #             • If attachments are provided, attach them to the email.(optional)

    #         Execution:
    #             send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments=None)

    #     9. **Mail Read (using Microsoft Graph API with tenant_id, client_id, client_secret)**
    #         from datas.supporting_files.office365_mail_read import read_latest_mail_ms_graph
    #         from_mail = <from_mail_address>
    #         tenant = <tenant_id>
    #         client_id = <client_id>
    #         client_secret = <client_secret>
    #         body = read_latest_mail_ms_graph(from_mail, tenant, client_id, client_secret)

    #         returns:
    #             - body (plain-text email body, cleaned from HTML)

    #     10. **OTP extraction from mail**(passing mail body directly)
    #         from datas.supporting_files.otp_mail_read import gemini_extract_otp_from_mail
    #         mail_body = <mail_body>
    #         otp = gemini_extract_otp_from_mail(mail_body)

    #     11. **Mail Attachement Download (using Microsoft Graph API with tenant_id, client_id, client_secret)**
    #         from datas.supporting_files.ms_mail_attach_download import download_outlook_attachments
    #         from_mail = <from_mail_address>
    #         tenant = <tenant_id>
    #         client_id = <client_id>
    #         client_secret = <client_secret>
    #         download_path = <a full folder path from given path on the requirement>
    #         download_outlook_attachments(from_mail,tenant,client_id,client_secret,download_path)

    #     12. **OCR Text Extract (Extract text from image)**
    #         from datas.supporting_files.ocr_text_extract import text_extract
    #         img_file_path = <Full image path from user action>
    #         description = <User Action from requirement>
    #         ocr_text=text_extract(img_file_path,description)
        

            
    #     ================================================================================
    #     CRITICAL USAGE RULES
    #     ================================================================================
    #     1. **Selenium Functions (1-5)**: Use ONLY for web browser actions
    #     - DO NOT use execute_step, text_data, table_df, element_status for PDF files
    #     - DO NOT use these for file system operations (copy, move, rename, delete)
    #     - These are strictly for web elements in browser

    #     2. **Direct Logic Required For:**
    #     - File operations (copy, move, rename, delete files/folders)
    #     - PDF reading (use PyPDF2, pdfplumber directly)
    #     - Image operations
    #     - Data transformations
    #     - String manipulations
    #     - Date/time calculations
    #     - Conditional logic
    #     - Loops over data

    #     3. **URL Launch Rule:**
    #     - ONLY use open_url_with_selenium when user explicitly says to launch/open a URL
    #     - If no URL launch is mentioned, DO NOT include it

    #     ================================================================================
    #     EMAIL FETCHING RULES
    #     ================================================================================
    #     - Use **Microsoft Graph API** when user mentions: Office 365, Outlook, Microsoft email, tenant, client ID, Azure AD
    #     - Use **IMAP** for Gmail, Yahoo, custom domains, or when email/password is provided
    #     - **Never wrap email logic** in var_name / json_xpath / .run() pattern
    #     - Write email fetching **directly inside aba_agent()** as native code
    #     - Extract **4-8 digit codes automatically** using regex
    #     - Always wait up to 180 seconds (configurable)
    #     - Credentials must come from user requirement — never hardcode unless explicitly provided
    #     - For Graph API: Use **client credentials flow** (no user login)
    #     - For Gmail: Must use **App Password** (not regular password)

    #     ================================================================================
    #     QUEUE HANDLING RULES
    #     ================================================================================
    #     CRITICAL: Queue operations should ONLY be used when explicitly mentioned in user requirements.
    #     DO NOT assume or add queue operations unless the user specifically requests them.

    #     RULE 1: Queue Detection
    #         Use queue operations ONLY when user requirement contains keywords like:
    #         - "queue", "get from queue", "retrieve from queue", "upload to queue"
    #         - "update queue status", "queue item", "queue data"

    #         If any of these keywords are present, import queue modules with:
    #             import sys, os
    #             sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
    #         If none of these are mentioned, DO NOT include any queue-related code.

    #     RULE 2: Get Queue (Retrieve from Queue)
    #         ONLY when user explicitly mentions retrieving/getting values from queue:
    #         from datas.supporting_files.getqueue import get_task_from_queue
    #         api_key=<which is passed>
    #         records, rowid, status_val, status_res, startTime, queuename, queueemail=get_task_from_queue(api_key)
            
    #             Return values explanation:
    #                 - records      : The complete current queue item data (dict/object)
    #                                 Required for update queue status operation
    #                 - rowid        : Unique identifier for the queue item (Just for reference)
    #                 - status_val   : Current status of queue item (string: "inprogress" or "new")
    #                                 Use this for reference/logging only
    #                 - status_res   : Boolean flag indicating if processing should continue
    #                                 If True: Proceed with processing
    #                                 If False: Stop processing and end iteration
    #                 - startTime    : Timestamp when item processing started
    #                                 Required for update queue status operation
    #                 - queuename    : Name of the queue (Just for reference)
    #                 - queueemail   : Email associated with the queue item (Just for reference)

    #     RULE 3: Upload Queue
    #         ONLY when user explicitly mentions uploading/adding values to queue:
    #         from datas.supporting_files.update_queue import queue_upload
    #         api_key=<which is passed>
    #         queue_upload(api_key,<data_to_pushed_on_queue>)

    #     RULE 4: Update Queue Status
    #         ONLY when user explicitly mentions updating status of queue items:
    #         from datas.supporting_files.queue_update_status import queue_update
    #         statusupdate:<if user says as success means "success" ,if user says failed means "failed" it can either be success or failed>
    #         api_key=<which is passed>
    #         queue_update(api_key,<data_to_pushed_on_queue>, statusupdate, startTime)
                
    #             Parameters:
    #                 - api_key        : Authentication key (passed as function parameter)
    #                 - records        : Complete queue item data (obtained from get_task_from_queue)
    #                 - rowid          : Queue item unique identifier (obtained from get_task_from_queue)
    #                 - status_update  : Status to set, must be EXACTLY one of:
    #                                 * "success" - when operation completed successfully
    #                                 * "failed"  - when operation failed
    #                 - startTime      : Processing start timestamp (obtained from get_task_from_queue)

    #             Status determination logic:
    #                 - If user says "success", "completed", "done" → use "success"
    #                 - If user says "failed", "error", "unsuccessful" → use "failed"
    #                 - ONLY these two values are valid: "success" or "failed"

    #     ================================================================================
    #     CODE STRUCTURE INSTRUCTIONS FOR WEB AUTOMATION USING SELENIUM
    #     ================================================================================

    #     ================================================================================
    #     ACTION CLASSIFICATION AND CODE PATTERN RULES
    #     ================================================================================

    #     **RULE 1: ALL XPATH ACTIONS (Use Complete Module Pattern)**
    #     ALL web element interactions must use external module files with the FULL PATTERN:
    #     - Type actions (label, input, search field)
    #     - Click actions (buttons, links, checkboxes, radio buttons, icons)
    #     - Extract/Read actions (get text, get attribute values, scrape data)
    #     - Scroll actions (scroll to element, scroll page)
    #     - Navigation actions (browser back, forward, refresh)
    #     - Alert/Popup handling (accept alert, dismiss alert)
    #     - Dropdown selection (select from dropdown, choose option)
    #     - Date picker interactions (calendar selection, date range selection)
    #     - Multi-step complex interactions requiring state management
    #     - File upload/download interactions
    #     - Drag and drop actions
    #     - Hover actions
    #     - Any other web element interaction

    #     **Pattern for ALL XPATH Actions:**
    #     ```python
    #     var_name = "action_name"
    #     description = "Full action description"
    #     import os
    #     cwd=os.getcwd()
    #     execute_step(driver,var_name,description,{userid},cwd)

    #     NOTE:
    #      - the execute_step function no need to call for get text or get element status like actions
    #     ```

    #     **RULE 2: DIRECT CODE IMPLEMENTATION (No Pattern Required)**
    #     These actions do NOT involve web elements and should be written directly as logical code:
    #     - Variable assignment (assign value, declare variable, set variable)
    #     - File operations (open file, save file, delete file, move file, copy file)
    #     - Directory operations (create folder, delete folder, list files)
    #     - Date/Time calculations (get current date, calculate date difference, format date)
    #     - String operations (concatenate, split, replace, format)
    #     - Mathematical operations (calculate, sum, average)
    #     - Data transformations (convert data types, parse JSON, format data)
    #     - Conditional logic (if-else conditions based on variables)
    #     - Loop iterations (for loops, while loops over data)
    #     - API calls (not web browser related)

    #     **Pattern for DIRECT CODE:**
    #     Simply write the Python code directly without using var_name, json_xpath, or any pattern structure.

    #     Example:
    #     ```python
    #     # Calculate date
    #     from datetime import datetime, timedelta
    #     today = datetime.now()
    #     previous_month = today - timedelta(days=30)
    #     ```

    #     **RULE 3: REFERENCE FUNCTIONS**
    #     If actions are related to:
    #     - Launching URL → Declare open_url_with_selenium() function inside aba_agent() and call it
    #     - Mail Read → Declare email fetching function inside aba_agent() and call it
    #     - Queue Upload → Declare update_queue functions inside aba_agent() and call it
    #     - Extract text → Declare text_data function inside aba_agent() and call it
    #     - Extract table → Declare table_df function inside aba_agent() and call it
    #     - Element exists → Declare element_status function inside aba_agent() and call it
    #     - Execute Step → Declare execute_step() function inside aba_agent() and use for all XPath actions


    #     ================================================================================
    #     CORRECT CODE PATTERN EXAMPLE (MANDATORY)
    #     ================================================================================
    #     User Requirement:
    #     - Launch the URL http://54.90.203.61/
    #     - Type username as admin
    #     - Type password as 1234
    #     - Click Sign In button
    #     - Type 123456 in OTP field
    #     - Check Verify button exists
    #     - If Verify button exists Click Verify button and end the if
    #     - Click Forms button
    #     - Extract text from Group Name field
    #     - Message box the Group Name
    #     - Select India from country dropdown
    #     - Select Tamil Nadu from state/province dropdown
    #     - Select Coimbatore in city dropdown
    #     - Click Select Skills button
    #     - Check Python checkbox
    #     - Type 2323 3232 3224 3223 in credit card field
    #     - Set date range from the first day of the previous month to the first day of this month
    #     - Click Tables button
    #     - Extract the table under master heading and store in to variable table_data
    #     - save table_data data in it to C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx
    #     - Read the rpamaster.xlsx Excel and store into a variable df
    #     - Upload the df into the queue api key is "kdkfjkefjdjfkdfk"
    #     - Iterate the each record on queue by one by one bt Get queue until status result is False
    #     - Update the queue status as success
    #     - End the get queue loop and message popup as process completed

    #     **CORRECT OUTPUT:**
    #     ```python
    #     def aba_agent():
    #         try:
    #             import sys, os
    #             import requests
    #             import time
    #             import json
    #             import traceback
    #             import datetime
    #             import pandas as pd
    #             from selenium import webdriver
    #             from selenium.webdriver.chrome.service import Service
    #             from selenium.webdriver.chrome.options import Options
    #             from selenium.webdriver.common.by import By

    #             import sys
    #             import os
                
    #             # Import standard functions from datas.supporting_files
    #             from datas.supporting_files.launch_url import open_url_with_selenium
    #             from datas.supporting_files.office365_email import fetch_latest_email_graph 
    #             from datas.supporting_files.imap_email import fetch_latest_email_code
    #             from datas.supporting_files.execute_step_code import execute_step
    #             from datas.supporting_files.text_extract import text_data
    #             from datas.supporting_files.time_delay import time_delay
    #             from datas.supporting_files.excel_read import excel_read_file
    #             from datas.supporting_files.update_queue import queue_upload
    #             from datas.supporting_files.element_exist import element_status
    #             from datas.supporting_files.getqueue import get_task_from_queue
    #             from datas.supporting_files.queue_update_status import queue_update
    #             from datas.supporting_files.message_box import popup_message_box
    #             from datas.supporting_files.table_extract import table_df

                
                
                
    #             #current working directory
    #             cwd=os.getcwd()
                
    #             # Step 1: Launch URL using standard function
    #             url = "http://54.90.203.61/"
    #             driver = open_url_with_selenium(url)

    #             # Step 2: Type username as admin
    #             var_name = "username_field"
    #             description = "Type username as admin"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 3: Type password as 1234
    #             var_name = "password_field"
    #             description = "Type password as 1234"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 4: Click Sign In button
    #             var_name = "signin_button"
    #             description = "Click Sign In button"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 5: Type 123456 in OTP field
    #             var_name = "otp_field"
    #             description = "Type 123456 in OTP field"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 6: Check Verify button exists
    #             var_name = "verify_button_exists_status"
    #             description = "Check Verify button exists or not"
    #             verify_button_status=element_status(driver,var_name,description,{userid},cwd)

    #             # Step 7: If verify button exists Click Verify button
    #             if verify_button_status:
    #                 var_name = "verify_button"
    #                 description = "Click Verify button"
    #                 execute_step(driver,var_name,description,{userid},cwd)
    #             #Verify button clicks if condition ends

    #             # Step 8: Click Forms button
    #             var_name = "forms_button"
    #             description = "Click Forms button"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 9: Extract the Group Name
    #             var_name="group_name_extract"
    #             description = "extract the group name from the group name field"
    #             group_name_extract=text_data(driver,var_name,description,{userid},org_path)

    #             # Step 10: Message box the Group Name
    #             popup_message_box(group_name_extract)

    #             # Step 11: Select India from country dropdown
    #             var_name = "country_dropdown"
    #             description = "Select India from country dropdown"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 12: Select Tamil Nadu from state/province dropdown
    #             var_name = "state_province_dropdown"
    #             description = "Select Tamil Nadu from state/province dropdown"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 13: Select Coimbatore in city dropdown
    #             var_name = "city_dropdown"
    #             description = "Select Coimbatore in city dropdown"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 14: Click Select Skills button
    #             var_name = "select_skills_button"
    #             description = "Click Select Skills button"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 15: Check Python checkbox
    #             var_name = "python_checkbox"
    #             description = "Check Python checkbox"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 16: Type credit card number
    #             var_name = "credit_card_field"
    #             description = "Type 2323 3232 3224 3223 in credit card field"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 17: Calculate date range (DIRECT CODE)
    #             today = datetime.date.today()
    #             first_day_of_this_month = today.replace(day=1)
    #             last_day_of_previous_month = first_day_of_this_month - datetime.timedelta(days=1)
    #             first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

    #             start_date = first_day_of_previous_month.strftime("%m/%d/%Y")
    #             end_date = first_day_of_this_month.strftime("%m/%d/%Y")

    #             # Step 18: Set date range picker
    #             var_name = "date_range_picker"
    #             description = f"Set date range from {{start_date}} to {{end_date}}"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 19: Click Tables button
    #             var_name = "tables_button"
    #             description = "Click Tables button"
    #             execute_step(driver,var_name,description,{userid},cwd)

    #             # Step 20: Extract the table
    #             var_name = "extract_master_table"
    #             description = "Extract the table under master heading"
    #             table_data=table_df(driver,var_name,description,{userid},cwd)

    #             #Step 21: Write the table_data in to the excel file
    #             file_path="C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
    #             table_data.to_excel(file_path, index=False)

    #             #Step 22: Read the rpamaster.xlsx file
    #             file_path="C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
    #             df=excel_read_file(file_path)

    #             #Step 23: Upload the df into queue
    #             api_key="kdkfjkefjdjfkdfk"
    #             queue_upload(api_key,df)

    #             #Step 24: Get Queue loop
    #             while True:
    #                 records, rowid, status_val, status_res, startTime, queuename, queueemail=get_task_from_queue(api_key)
    #                 # Loop until status result as False
    #                 if not status_res:
    #                     break
    #                 #Step 24: Update Queue status success
    #                 from datas.supporting_files.queue_update_status import queue_update
    #                 queue_upload(api_key,records,"success",startTime)
                
    #             #Step 26:Message popup as Process Completed outside the get queue loop
    #             popup_messagebox("Process Completed)

    #         except Exception as e:
    #             os.makedirs("json_info", exist_ok=True)
    #             with open("json_info/exception_info.json", "w") as f:
    #                 json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)
    #         finally:
    #             if 'driver' in locals():
    #                 driver.quit()
    #     ```

    #     ================================================================================
    #     MANDATORY RULES
    #     ================================================================================
    #     1. **Function Definition**
    #     - Wrap all code in a single function: `def aba_agent():`
    #     - Function takes **no arguments**
    #     - Do **not** call the function inside the code

    #     2. **Import Statements**
    #     - ALL imports must be placed inside the aba_agent() function block, not at the top of the file
    #     - Always import standard functions from datas.supporting_files at the beginning of try block:
    #     - If a scenario is not covered by the available imports, generate the required logic dynamically in real time inside the agent code instead of adding new modules or files in supporting_files (strictly follow the rule)
    #     ```python
    #             from datas.supporting_files.launch_url import open_url_with_selenium #If web url launch asks
    #             from datas.supporting_files.execute_step_code import execute_step # If web actions like click or type or hover or element wait or Dropdown selection or dropdown click needed
    #             from datas.supporting_files.imap_email import fetch_latest_email_code  # If IMAP email needed  # If IMAP email needed (import only when tenant id, client id, client secret not given and all credentials are given)
    #             from datas.supporting_files.excel_read import excel_read_file #If Excel read needed
    #             from datas.supporting_files.message_box import popup_message_box #If Message box needed
    #             from datas.supporting_files.time_delay import time_delay #If time delay needed
    #             from datas.supporting_files.text_extract import text_data #If text extract is needed
    #             from datas.supporting_files.table_extract import table_df #If web table extraction is needed
    #             from datas.supporting_files.update_queue import queue_upload #If Queue upload is required
    #             from datas.supporting_files.queue_update_status import queue_update #If Queue update status is required
    #             from datas.supporting_files.element_exist import element_status #If web element exists or not is required
    #             from datas.supporting_files.pdf_splitter import split_pdf #If pdf splitter is required
    #             from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf #If pdf highlighter is required
    #             from datas.supporting_files.pdf_xl import pdf_to_table_extract #If table extract from PDF is required
    #             from datas.supporting_files.office365_mail_send import send_mail_ms_graph #If Office 365 email send is required with proper data(client_id,client_secret,tenant_id, attachment_paths)
    #             from datas.supporting_files.office365_mail_read import read_latest_mail_ms_graph #If Office 365 email read is required with proper data(client_id,client_secret,tenant_id)
    #             from datas.supporting_files.otp_mail_read import gemini_extract_otp_from_mail #If OTP extraction from mail is required
    #             from datas.supporting_files.ms_mail_attach_download import download_outlook_attachments #If Download attachement from mail required
    #             from datas.supporting_files.ocr_text_extract import text_extract #If Ocr text extract required
    #             from datas.supporting_files.window_handle import switch_to_window #If window handle change is required
    #             from datas.supporting_files.browser_zoom import set_zoom #If zoom in or zoom out on browser is required
    #     ```

    #     3. **Try/Except/Finally**
    #     - Always use:
    #     ```python
    #         except Exception as e:
    #             ...
    #         finally:
    #             if 'driver' in locals():
    #                 driver.quit()
    #     ```

    #     4. **Reference Functions**
    #     - open_url_with_selenium(), execute_step(), email fetching functions, and queue functions must ALL be defined INSIDE aba_agent()
    #     - These functions should be declared at the top of the try block, before their usage

    #     5. **Driver Variable**
    #     - open_url_with_selenium() always returns 'driver' variable
    #     - Use this returned driver for all subsequent operations
    #     - Pass driver to execute_step() and all module .run() calls

    #     6. **Action Classification**
    #     - **XPATH ACTIONS (External Module Pattern)**: ALL web element interactions including typing, clicks, extracts, scrolls, checkboxes, dropdowns, table extraction, date pickers, navigation, alerts, file uploads, drag/drop, hover
    #     - **DIRECT CODE**: Non-web operations like variable assignment, file operations, Excel operations, date calculations, string operations, conditionals, loops, API calls
    #     - **REFERENCE FUNCTIONS**: URL Launch, Mail Read, Queue operations - declare functions inside aba_agent() and call them

    #     7. **Unique Variable Names**
    #     - Each `var_name` must be unique across the entire project
    #     - For duplicate element names, use incremented names: continue_button, continue_button1, continue_button2

    #     8. **Output Format**
    #     - Output must contain **only valid Python code** (no explanations, markdown, or comments outside the code)
    #     - Follow the exact pattern demonstrated in the example above

    #     ================================================================================
    #     OUTPUT REQUIREMENTS
    #     ================================================================================
    #     Generate complete, executable Python code following all the rules above.
    #     The code must be production-ready with proper error handling and resource cleanup.
    #     The Final Code should contains only cmds tag about Step 1,Step 2,Step 3 ..... not additional explaining tags or any
    #     """
    
    prompt = f"""
        Here is the User Requirement: {input}

        Based on the above requirement, generate the **Web Automation Code**.

        ================================================================================
        SELENIUM-SPECIFIC FUNCTION IMPORTS (Use ONLY for Web Actions)
        ================================================================================
        The following functions should ONLY be used for Selenium web browser interactions.
        DO NOT use these for file operations, PDF operations, or other non-web tasks.

        1. **URL Launch (ONLY when explicitly asked to launch/open a URL):**
        from datas.supporting_files.launch_url import open_url_with_selenium
        driver = open_url_with_selenium(url)

        2. **Web Element Interactions (Click, Type, Hover, Wait, Dropdown):**

        For ANY web element interaction including Click, Type, Hover, Element Wait, Dropdown Selection, Dropdown Click, or Scroll operations,Scroll + click, you MUST use the following standardized format:
        
        **For NON-TYPING actions (Click, Hover, Wait, Dropdown, Scroll):**
        ```python
        from datas.supporting_files.execute_step_code import execute_step

        var_name = "action_name"
        description = "Full action description"
        cwd = os.getcwd()

        execute_step(driver, var_name, description, {{userid}}, cwd)
        ```

        **For TYPING actions (Type/Enter text into fields):**
        ```python
        from datas.supporting_files.execute_step_code import execute_step

        var_name = "action_name"
        description = "Full action description"
        type_input = "text to be typed"
        cwd = os.getcwd()

        execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
        ```

        **CRITICAL RULES:**
        1. ALWAYS use the execute_step function for web interactions - NO exceptions
        2. NEVER implement interactions directly (e.g., ActionChains, find_element, click(), send_keys())
        3. For TYPING actions, you MUST:
           - Define type_input variable with the text to be entered
           - Pass type_input as a keyword parameter to execute_step
        4. For NON-TYPING actions (clicks, hovers, etc.):
           - Do NOT include type_input parameter
           - Use the standard execute_step call without type_input
        5. This applies to ALL interaction types:
        - Clicking elements (NO type_input)
        - Typing/entering text (REQUIRES type_input)
        - Hovering over elements (NO type_input)
        - Waiting for elements (NO type_input)
        - Dropdown selections (NO type_input)
        - Scrolling to elements (NO type_input)
        - Any other DOM interactions

        **INCORRECT - Do NOT use:**
        ```python
        # ❌ WRONG - Direct implementation
        element = driver.find_element(By.XPATH, "//input[@id='username']")
        element.send_keys("admin")
        ```

        **CORRECT - Always use:**
        ```python
        # ✓ RIGHT - Using execute_step with type_input for typing
        from datas.supporting_files.execute_step_code import execute_step

        var_name = "username_field"
        description = "Type username as admin"
        type_input = "admin"
        cwd = os.getcwd()

        execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
        ```

        **CORRECT - For non-typing actions:**
        ```python
        # ✓ RIGHT - Using execute_step WITHOUT type_input for clicking
        from datas.supporting_files.execute_step_code import execute_step

        var_name = "submit_button"
        description = "Click submit button"
        cwd = os.getcwd()

        execute_step(driver, var_name, description, {{userid}}, cwd)
        ```

        **Scroll and Click combined** (NO type_input) - Use single action with description "Scroll to element and click"
        var_name = "submit_button"
        description = "Scroll to the submit button and clicks"
        cwd = os.getcwd()

        execute_step(driver, var_name, description, {{userid}}, cwd)

        **Parameters:**
        - `var_name`: Descriptive identifier for the action (e.g., "click_submit", "type_username")
        - `description`: Clear, detailed description of what action to perform
        - `{{userid}}`: User identifier placeholder (keep as-is)
        - `cwd`: Current working directory obtained via os.getcwd()
        - `type_input`: (ONLY for typing actions) The text/value to be entered into the field

        This standardized approach ensures consistency, maintainability, and proper error handling across all web automation tasks.

        3. **Text Extract from Web (ONLY for extracting text from web elements):**
        from datas.supporting_files.text_extract import text_data
        var_name = "action_name"
        description = "Full action description"
        cwd = os.getcwd()
        extracted_text = text_data(driver, var_name, description, {userid}, cwd)

        4. **Element Exists Check (ONLY for checking if web element exists):**
        from datas.supporting_files.element_exist import element_status
        var_name = "action_name"
        description = "Full action description"
        cwd = os.getcwd()
        exists_status = element_status(driver, var_name, description, {userid}, cwd)

        5. **Table Extract from Web (ONLY for extracting tables from web pages):**
        from datas.supporting_files.table_extract import table_df
        var_name = "action_name"
        description = "Full action description"
        cwd = os.getcwd()
        table_data = table_df(driver, var_name, description, {userid}, cwd)

        6. **Switch or Change the driver to the specific window (change the window handle to specific number)**
        from datas.supporting_files.window_handle import switch_to_window
        window_index=<window index number from user action as int type convert based on input of window index from user action as 3rd window as 2nd index>
        switch_to_window(driver,window_index)

        7. **Zoom in or Zoom out the driver/browser based on percentage**:
        from datas.supporting_files.browser_zoom import set_zoom
        percentage=<int type as number eg: 75 as for 75 %>
        set_zoom(driver,percentage)

        8. **Maximize the Current window/browser**
        from datas.supporting_files.maximize_window import max_window
        max_window(driver)

        9. **Keyboard Button Actions**:

            **For Web/Selenium Actions (within browser context)**:
            Use Selenium's Keys when interacting with web elements:
            
            - Enter key:
            ```python
                driver.switch_to.active_element.send_keys(Keys.ENTER)
            ```
            
            - Tab key:
            ```python
                driver.switch_to.active_element.send_keys(Keys.TAB)
            ```

            **For Desktop/System-Level Actions (outside browser context)**:
            Use PyAutoGUI when the key press is not part of the web automation flow:
            
            - Enter key:
            ```python
                import pyautogui
                pyautogui.press('enter')
            ```
            
            - Tab key:
            ```python
                import pyautogui
                pyautogui.press('tab')
            ```

            **When to use which approach**:
            - Use Selenium Keys for actions within the browser (form submissions, navigation within web pages)
            - Use PyAutoGUI for system-level actions or when interacting with elements outside the browser context


            NOTE:
            This action cannot be in commended line like below
            #driver.switch_to.active_element.send_keys(Keys.ENTER)

        ================================================================================
        NON-SELENIUM FUNCTION IMPORTS (Use for specific operations)
        ================================================================================

        1. **Email Fetching - IMAP (Gmail, Yahoo, Custom Domains):**
        from datas.supporting_files.imap_email import fetch_latest_email_code
        code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                        folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

        2. **Excel Read Function Usage Based on Row Limits:**

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

        3. **Excel Write (Write the dataframe in to excel file)**:
            data_df=<respective dataframe which need to write>
            excel_file_path=<full excel file path where need to write>
            from datas.supporting_files.excel_write import write_df_to_file
            write_df_to_file(data_df,excel_file_path)

        4. **Message Box:**
            from datas.supporting_files.message_box import popup_message_box
            popup_message_box(<message_to_display>)

        5. **Time Delay:**
            from datas.supporting_files.time_delay import time_delay
            time_delay(<seconds_as_int>)

        6. **PDF Split:**
            from datas.supporting_files.pdf_splitter import split_pdf
            pdf_file_path = <pdf_file_full_path>
            page_limit = <pages_per_split_as_int>
            destination_folder = <destination_folder_path>
            pdf_split(pdf_file_path, page_limit, destination_folder)

        7. **PDF Highlighter:**
            from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
            pdf_path = <pdf_file_full_path>
            text = <text_to_highlight>
            output_path = <output_path>
            highlight_text_in_pdf(pdf_path, text, output_path)

        8. **Extract Table from PDF:**
            from datas.supporting_files.pdf_xl import pdf_to_table_extract
            description = "Full action description"
            pdf_file = <Full pdf file path>
            table_df = pdf_to_table_extract(pdf_file,description)

        9. **Mail Send (using Microsoft Graph API with tenant_id, client_id, client_secret, attachments-optional)**
            from datas.supporting_files.office365_mail_send import send_mail_ms_graph
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

        10. **Mail Read (using Microsoft Graph API with tenant_id, client_id, client_secret)**
            from datas.supporting_files.office365_mail_read import read_latest_mail_ms_graph
            from_mail = <from_mail_address>
            tenant = <tenant_id>
            client_id = <client_id>
            client_secret = <client_secret>
            body = read_latest_mail_ms_graph(from_mail, tenant, client_id, client_secret)

            returns:
                - body (plain-text email body, cleaned from HTML)

        11. **OTP extraction from mail**(passing mail body directly)
            from datas.supporting_files.otp_mail_read import gemini_extract_otp_from_mail
            mail_body = <mail_body>
            otp = gemini_extract_otp_from_mail(mail_body)

        12. **Mail Attachement Download (using Microsoft Graph API with tenant_id, client_id, client_secret)**
            from datas.supporting_files.ms_mail_attach_download import download_outlook_attachments
            from_mail = <from_mail_address>
            tenant = <tenant_id>
            client_id = <client_id>
            client_secret = <client_secret>
            download_path = <a full folder path from given path on the requirement>
            download_outlook_attachments(from_mail,tenant,client_id,client_secret,download_path)

        13. **OCR Text Extract (Extract text from image)**
            from datas.supporting_files.ocr_text_extract import text_extract
            img_file_path = <Full image path from user action>
            description = <User Action from requirement>
            ocr_text=text_extract(img_file_path,description)
        

            
        ================================================================================
        CRITICAL USAGE RULES
        ================================================================================
        1. **Selenium Functions (1-5)**: Use ONLY for web browser actions
        - DO NOT use execute_step, text_data, table_df, element_status for PDF files
        - DO NOT use these for file system operations (copy, move, rename, delete)
        - These are strictly for web elements in browser

        2. **Direct Logic Required For:**
        - File operations (copy, move, rename, delete files/folders)
        - PDF reading (use PyPDF2, pdfplumber directly)
        - Image operations
        - Data transformations
        - String manipulations
        - Date/time calculations
        - Conditional logic
        - Loops over data

        3. **URL Launch Rule:**
        - ONLY use open_url_with_selenium when user explicitly says to launch/open a URL
        - If no URL launch is mentioned, DO NOT include it

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
            from datas.supporting_files.getqueue import get_task_from_queue
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
            from datas.supporting_files.update_queue import queue_upload
            api_key=<which is passed>
            queue_upload(api_key,<data_to_pushed_on_queue>)

        RULE 4: Update Queue Status
            ONLY when user explicitly mentions updating status of queue items:
            from datas.supporting_files.queue_update_status import queue_update
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

        **RULE 1: ALL XPATH ACTIONS (Use Complete Module Pattern)**
        ALL web element interactions must use external module files with the FULL PATTERN:
        - Type actions (label, input, search field) - REQUIRES type_input parameter
        - Click actions (buttons, links, checkboxes, radio buttons, icons) - NO type_input
        - Extract/Read actions (get text, get attribute values, scrape data) - NO type_input
        - Scroll actions (scroll to element, scroll page) - NO type_input
        - Navigation actions (browser back, forward, refresh) - NO type_input
        - Alert/Popup handling (accept alert, dismiss alert) - NO type_input
        - Dropdown selection (select from dropdown, choose option) - NO type_input
        - Date picker interactions (calendar selection, date range selection) - NO type_input
        - Multi-step complex interactions requiring state management
        - File upload/download interactions - NO type_input
        - Drag and drop actions - NO type_input
        - Hover actions - NO type_input
        - Any other web element interaction

        **Pattern for TYPING XPATH Actions:**
        ```python
        var_name = "action_name"
        description = "Full action description"
        type_input = "text to type"
        import os
        cwd=os.getcwd()
        execute_step(driver, var_name, description, {userid}, cwd, type_input=type_input)
        ```

        **Pattern for NON-TYPING XPATH Actions:**
        ```python
        var_name = "action_name"
        description = "Full action description"
        import os
        cwd=os.getcwd()
        execute_step(driver, var_name, description, {userid}, cwd)

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
        Simply write the Python code directly without using var_name, json_xpath, or any pattern structure.

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
        - Execute Step → Declare execute_step() function inside aba_agent() and use for all XPath actions

        **RULE 4: VARIABLE NAMING var_name rules**
        - Each var_name must be unique across the entire code
        - For duplicate element names, use increments: button1, button2, button3
        - Check existing var_names before adding new ones
        - **CRITICAL: var_name must ALWAYS be a plain string, NEVER a formatted string**
        - **For actions inside loops (for/while)**: Use the SAME var_name without any formatting or increment
        - ❌ WRONG: `var_name = f"pay_info_{i}"` or `var_name = f"item_{index}"`
        - ✓ CORRECT: `var_name = "pay_info"` (use same name for all loop iterations)
        - **Reason**: The flow is maintained by dynamic XPath internally, so the same var_name can be reused in loops
        - **Examples**:
        ```python
        # ✓ CORRECT - Same var_name in loop
        for i in range(5):
            var_name = "click_item"
            description = "Click on item in list"
            execute_step(driver, var_name, description, {{userid}}, cwd)
        
        # ❌ WRONG - Formatted var_name in loop
        for i in range(5):
            var_name = f"click_item_{i}"  # DON'T DO THIS
            description = "Click on item in list"
            execute_step(driver, var_name, description, {{userid}}, cwd)
        ```

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
                from datas.supporting_files.launch_url import open_url_with_selenium
                from datas.supporting_files.office365_email import fetch_latest_email_graph 
                from datas.supporting_files.imap_email import fetch_latest_email_code
                from datas.supporting_files.execute_step_code import execute_step
                from datas.supporting_files.text_extract import text_data
                from datas.supporting_files.time_delay import time_delay
                from datas.supporting_files.excel_read import excel_read_file
                from datas.supporting_files.update_queue import queue_upload
                from datas.supporting_files.element_exist import element_status
                from datas.supporting_files.getqueue import get_task_from_queue
                from datas.supporting_files.queue_update_status import queue_update
                from datas.supporting_files.message_box import popup_message_box
                from datas.supporting_files.table_extract import table_df

                
                
                
                #current working directory
                cwd=os.getcwd()
                
                # Step 1: Launch URL using standard function
                url = "http://54.90.203.61/"
                driver = open_url_with_selenium(url)

                # Step 2: Type username as admin
                var_name = "username_field"
                description = "Type username as admin"
                type_input = "admin"
                execute_step(driver, var_name, description, {userid}, cwd, type_input=type_input)

                # Step 3: Type password as 1234
                var_name = "password_field"
                description = "Type password as 1234"
                type_input = "1234"
                execute_step(driver, var_name, description, {userid}, cwd, type_input=type_input)

                # Step 4: Click Sign In button
                var_name = "signin_button"
                description = "Click Sign In button"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 5: Type 123456 in OTP field
                var_name = "otp_field"
                description = "Type 123456 in OTP field"
                type_input = "123456"
                execute_step(driver, var_name, description, {userid}, cwd, type_input=type_input)

                # Step 6: Check Verify button exists
                var_name = "verify_button_exists_status"
                description = "Check Verify button exists or not"
                verify_button_status = element_status(driver, var_name, description, {userid}, cwd)

                # Step 7: If verify button exists Click Verify button
                if verify_button_status:
                    var_name = "verify_button"
                    description = "Click Verify button"
                    execute_step(driver, var_name, description, {userid}, cwd)
                #Verify button clicks if condition ends

                # Step 8: Click Forms button
                var_name = "forms_button"
                description = "Click Forms button"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 9: Extract the Group Name
                var_name = "group_name_extract"
                description = "extract the group name from the group name field"
                group_name_extract = text_data(driver, var_name, description, {userid}, cwd)

                # Step 10: Message box the Group Name
                popup_message_box(group_name_extract)

                # Step 11: Select India from country dropdown
                var_name = "country_dropdown"
                description = "Select India from country dropdown"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 12: Select Tamil Nadu from state/province dropdown
                var_name = "state_province_dropdown"
                description = "Select Tamil Nadu from state/province dropdown"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 13: Select Coimbatore in city dropdown
                var_name = "city_dropdown"
                description = "Select Coimbatore in city dropdown"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 14: Click Select Skills button
                var_name = "select_skills_button"
                description = "Click Select Skills button"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 15: Check Python checkbox
                var_name = "python_checkbox"
                description = "Check Python checkbox"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 16: Type credit card number
                var_name = "credit_card_field"
                description = "Type 2323 3232 3224 3223 in credit card field"
                type_input = "2323 3232 3224 3223"
                execute_step(driver, var_name, description, {userid}, cwd, type_input=type_input)

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
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 19: Click Tables button
                var_name = "tables_button"
                description = "Click Tables button"
                execute_step(driver, var_name, description, {userid}, cwd)

                # Step 20: Extract the table
                var_name = "extract_master_table"
                description = "Extract the table under master heading"
                table_data = table_df(driver, var_name, description, {userid}, cwd)

                #Step 21: Write the table_data in to the excel file
                file_path = "C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
                table_data.to_excel(file_path, index=False)

                #Step 22: Read the rpamaster.xlsx file
                file_path = "C:\\\\Users\\\\Administrator\\\\Documents\\\\aba\\\\rpamaster.xlsx"
                df = excel_read_file(file_path)

                #Step 23: Upload the df into queue
                api_key = "kdkfjkefjdjfkdfk"
                queue_upload(api_key, df)

                #Step 24: Get Queue loop
                while True:
                    records, rowid, status_val, status_res, startTime, queuename, queueemail=get_task_from_queue(api_key)
                    # Loop until status result as False
                    if not status_res:
                        break
                    #Step 24: Update Queue status success
                    from datas.supporting_files.queue_update_status import queue_update
                    queue_upload(api_key,records,"success",startTime)
                
                #Step 26:Message popup as Process Completed outside the get queue loop
                popup_messagebox("Process Completed)

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
        - If a scenario is not covered by the available imports, generate the required logic dynamically in real time inside the agent code instead of adding new modules or files in supporting_files (strictly follow the rule)
        ```python
                from datas.supporting_files.launch_url import open_url_with_selenium #If web url launch asks
                from datas.supporting_files.execute_step_code import execute_step # If web actions like click or type or hover or element wait or Dropdown selection or dropdown click needed
                from datas.supporting_files.imap_email import fetch_latest_email_code  # If IMAP email needed  # If IMAP email needed (import only when tenant id, client id, client secret not given and all credentials are given)
                from datas.supporting_files.excel_read import excel_read_file #If Excel read needed
                from datas.supporting_files.excel_write import write_df_to_file #If excel write is needed
                from datas.supporting_files.message_box import popup_message_box #If Message box needed
                from datas.supporting_files.time_delay import time_delay #If time delay needed
                from datas.supporting_files.text_extract import text_data #If text extract is needed
                from datas.supporting_files.table_extract import table_df #If web table extraction is needed
                from datas.supporting_files.update_queue import queue_upload #If Queue upload is required
                from datas.supporting_files.queue_update_status import queue_update #If Queue update status is required
                from datas.supporting_files.element_exist import element_status #If web element exists or not is required
                from datas.supporting_files.pdf_splitter import split_pdf #If pdf splitter is required
                from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf #If pdf highlighter is required
                from datas.supporting_files.pdf_xl import pdf_to_table_extract #If table extract from PDF is required
                from datas.supporting_files.office365_mail_send import send_mail_ms_graph #If Office 365 email send is required with proper data(client_id,client_secret,tenant_id, attachment_paths)
                from datas.supporting_files.office365_mail_read import read_latest_mail_ms_graph #If Office 365 email read is required with proper data(client_id,client_secret,tenant_id)
                from datas.supporting_files.otp_mail_read import gemini_extract_otp_from_mail #If OTP extraction from mail is required
                from datas.supporting_files.ms_mail_attach_download import download_outlook_attachments #If Download attachement from mail required
                from datas.supporting_files.ocr_text_extract import text_extract #If Ocr text extract required
                from datas.supporting_files.window_handle import switch_to_window #If window handle change is required
                from datas.supporting_files.browser_zoom import set_zoom #If zoom in or zoom out on browser is required
                from datas.supporting_files.maximize_window import max_window #If window maximize on browser is required
        ```

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

        8. **Output Format**
        - Output must contain **only valid Python code** (no explanations, markdown, or comments outside the code)
        - Follow the exact pattern demonstrated in the example above

        9. **No Assumptions - Complete Code Generation**
        - Generate actual executable code for EVERY action mentioned in user requirement
        - NEVER use assumption comments like "# Assuming...", "# Already done...", "# Skipping..."
        - NEVER skip code for any action (window switch, maximize, conditionals, loops, etc.)
        - Every "Step X" must have corresponding working code below it
        - User verification depends on all actions being present in code
        - If requirement says "do X", code MUST contain logic to do X
        ================================================================================
        🚨 CRITICAL: NO ASSUMPTIONS RULE - GENERATE CODE FOR EVERY ACTION
        ================================================================================
        **ABSOLUTE REQUIREMENT**: Every single action mentioned in the user requirement MUST have corresponding executable code generated. NEVER skip or assume any action.

        **FORBIDDEN BEHAVIORS:**
        ❌ NEVER add comments like "# Assuming window is already at index 1"
        ❌ NEVER skip code generation with "# Assuming browser is already maximized"
        ❌ NEVER bypass conditions with "# Assuming rows > 0, so skipping if check"
        ❌ NEVER use placeholder comments instead of actual code
        ❌ NEVER make assumptions about the current state

        **MANDATORY BEHAVIORS:**
        ✅ ALWAYS generate the actual executable code for EVERY action
        ✅ ALWAYS include window switching code when mentioned
        ✅ ALWAYS include maximize code when mentioned
        ✅ ALWAYS include conditional logic (if/else) when mentioned
        ✅ ALWAYS implement loops when mentioned
        ✅ Every action = Corresponding working code

        **EXAMPLES OF VIOLATIONS AND CORRECTIONS:**

        **❌ VIOLATION 1 - Window Switch:**
        ```python
        # Step 5: Switch to window 1
        # Assuming window is already at index 1, skipping...
        ```

        **✅ CORRECT:**
        ```python
        # Step 5: Switch to window 1
        from datas.supporting_files.window_handle import switch_to_window
        window_index = 1
        switch_to_window(driver, window_index)
        ```

        **❌ VIOLATION 2 - Maximize Window:**
        ```python
        # Step 2: Maximize the window
        # Browser already maximized on launch, no action needed
        ```

        **✅ CORRECT:**
        ```python
        # Step 2: Maximize the window
        from datas.supporting_files.maximize_window import max_window
        max_window(driver)
        ```

        **❌ VIOLATION 3 - Conditional Logic:**
        ```python
        # Step 10: If rows > 0, click Submit button
        # Assuming rows is always > 0
        var_name = "submit_button"
        description = "Click Submit button"
        execute_step(driver, var_name, description, {userid}, cwd)
        ```

        **✅ CORRECT:**
        ```python
        # Step 10: If rows > 0, click Submit button
        if len(table_data) > 0:
            var_name = "submit_button"
            description = "Click Submit button"
            execute_step(driver, var_name, description, {userid}, cwd)
        ```

        **❌ VIOLATION 4 - Scroll and Click:**
        ```python
        # Step 7: Scroll to button and click
        # Element probably visible, just clicking
        var_name = "checkout_button"
        description = "Click checkout button"
        execute_step(driver, var_name, description, {userid}, cwd)
        ```

        **✅ CORRECT:**
        ```python
        # Step 7: Scroll to button and click
        var_name = "checkout_button"
        description = "Scroll to checkout button and click"
        execute_step(driver, var_name, description, {userid}, cwd)
        ```

        **❌ VIOLATION 5 - Loop Iteration:**
        ```python
        # Step 15: For each row in table, extract data
        # Assuming single row, processing only first
        var_name = "extract_row"
        description = "Extract row data"
        row_data = text_data(driver, var_name, description, {userid}, cwd)
        ```

        **✅ CORRECT:**
        ```python
        # Step 15: For each row in table, extract data
        for index in range(len(table_data)):
            var_name = "extract_row"
            description = "Extract row data"
            row_data = text_data(driver, var_name, description, {userid}, cwd)
        ```

        **VERIFICATION CHECKLIST:**
        Before finalizing code, verify:
        □ Does every action in user requirement have corresponding code?
        □ Are there any assumption comments instead of code?
        □ Ensure all actions have the required modules imported correctly at top of the code
        □ Are all if/else conditions properly implemented?
        □ Are all loops properly implemented?
        □ Are all window switches coded?
        □ Are all browser actions coded?
        □ Is every "Step X" comment followed by actual executable code?
        □ No Syntax or Line indent error occurs

        **WHY THIS IS CRITICAL:**
        - Every action is verified by the user during execution
        - Skipped actions will cause verification failures
        - Assumptions break the automation flow
        - Users expect 1:1 mapping between requirement and code
        - Missing code = Failed automation = User dissatisfaction

        **ENFORCEMENT:**
        If you generate code with assumption comments or skip any action mentioned in the requirement, it is a SEVERE VIOLATION of these instructions. Every single action must translate to working, executable code.

        ================================================================================
        ================================================================================
        OUTPUT REQUIREMENTS
        ================================================================================
        Generate complete, executable Python code following all the rules above.
        The code must be no syntax error or any line indent error occurs.It should be direct executable error without syntax errors
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
    code_to_write=normalize_var_name_lines(code_to_write)
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
    ** If NO supporting_file is found for current requirement, Generate real-time for the senario ** [Real-time code generation RULE]
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