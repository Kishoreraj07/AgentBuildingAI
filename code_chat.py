import google.generativeai as genai
import config
import pandas as pd
import os
import re,json

def error_fix(code_data,error_data):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt=f"""You have the following code:
{code_data}

When executing this code, the following error occurred:
{error_data}

CRITICAL: Fix ONLY the line(s) causing the error. Do NOT modify, remove, or add any other code. The main code flow, logic, and functionality MUST remain exactly the same. Only fix what is broken.

Return ONLY a JSON response in this exact format:
{{"code": "<corrected code>"}}

Requirements:
- Return only the JSON object, no explanations
- No markdown formatting or code blocks
- No additional text before or after the JSON
- Preserve all original code structure and logic
- Change ONLY what is necessary to fix the error"""
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
    return res["code"]
    
    
def file_path_found(exception):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt =f"""Here is the Exception Detail that occurred in a .py file: {exception}

Analyze the text to determine whether it is a valid Python traceback or exception message.

Rules for processing:
1. If the text clearly resembles a Python traceback (e.g., starts with or contains 'Traceback (most recent call last):'),
   then:
   - Extract all file paths ending with '.py' from the traceback.
   - Exclude any file paths belonging to system or library directories (such as those containing 'Python', 'site-packages', or 'lib').
   - Return the last remaining .py file path as the final result (this indicates the actual file where the error occurred).
2. If the text does NOT contain a recognizable traceback pattern or is a general message, instruction, or unrelated text,
   return an empty JSON object {{}}.

Return the result strictly in JSON format, like:
{{"file_path": "<found .py file path>"}}

If no valid .py file path is found or the input is not an exception message, return:
{{}}

Do not include any explanation, reasoning, or text outside the JSON response."""




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

def response_msg(input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""You are a Chatbot Agent.  
    Here is the User Query: {input}  

    Generate a direct and positive response to the user’s query and Respond like the task has been successfully completed
    Do not include additional explanations or extra text—just provide the response in clear, natural human language."""

    response = chat.send_message(prompt)
    return response.text
def convert_xlsx_to_text(xlsx_path):
    """Convert Excel to a plain text table for Gemini"""
    df = pd.read_excel(xlsx_path)
    return df.to_string(index=False)

def chat_request(code, input, filepaths, chat_history=None):
    """
    Process code modification request with chat history support
    
    Args:
        code: Current code to be modified
        input: User query/instruction
        filepaths: List of associated file paths
        chat_history: List of previous messages to maintain conversation context (default: None/empty)
    
    Returns:
        Tuple: (modified_code, response_message, updated_chat_history)
    """
    # Initialize chat history if not provided
    if chat_history is None:
        chat_history = []
    
    exception_file=file_path_found(input)
    try:
        if "gemini_code_correction.py" in exception_file["file_path"]:
            exception_file={}
    except:
        pass
    exception_found=False
    exception_same=False
    if len(exception_file)>0 and "file_path" in exception_file:
        exception_file_path=exception_file["file_path"]
        exception_found=True
    if exception_found and "execute_code.py" in exception_file_path:
        exception_same=True
    org_code=code
    exception_code=""
    if exception_found:
        try:
            with open(exception_file_path, "r", encoding="utf-8") as f:
                exception_code = f.read()
            main_code=exception_code
        except:
            exception_found=False
            main_code=org_code
    else:
        main_code=org_code
    
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    # Start chat with existing history for context
    chat = model.start_chat(history=chat_history)

    modified_prompt = f"""
You are an expert Python code modification assistant for web automation with Selenium.

User Query: {input}

The user wants to modify the following existing code based on their request:

Existing Code:
{main_code}

Associated files and their full paths: {filepaths}

================================================================================
CRITICAL INSTRUCTION - READ CAREFULLY
================================================================================
You MUST return the COMPLETE, ENTIRE modified code.
NEVER return only the modified section or partial code.
NEVER remove existing steps unless explicitly asked by the user.
ALWAYS return the full aba_agent() function with ALL existing code plus modifications.

**IMPORTANT: Keep ALL existing steps intact unless user specifically requests deletion.**

================================================================================
CRITICAL OUTPUT FORMAT REQUIREMENTS
================================================================================

**ABSOLUTE RULE - NO EXCEPTIONS:**

1. **RETURN ONLY EXECUTABLE PYTHON CODE** - Nothing else
2. **NO MARKDOWN FORMATTING** - Never use ```python, ```, or any markdown syntax
3. **NO EXPLANATIONS** - Do not add any text before, after, or within the code
4. **NO COMMENTS outside the code** - Only include standard Python comments that are part of the code itself
5. **NO INTRODUCTORY TEXT** - Do not write "Here's the modified code:" or similar phrases
6. **NO SUMMARY TEXT** - Do not explain what you changed after the code
7. **NO EXTRA WHITESPACE** - Do not add unnecessary blank lines before or after the code
8. **START IMMEDIATELY** - Your response must begin directly with the Python code

**The response will be written directly to a file and executed. Any non-Python text will cause execution errors.**

**CORRECT OUTPUT FORMAT:**
```
def aba_agent():
    try:
        import os
        from datas.supporting_files.launch_url import open_url_with_selenium
        ...
        [rest of the code]
```

**INCORRECT OUTPUT FORMAT:**
```
Here's the modified code with the changes you requested:

```python
def aba_agent():
    ...
```

I've added the new step after step 3 and renumbered the subsequent steps.
```

**The ENTIRE response must be valid Python code that can be directly written to a .py file and executed.**

================================================================================
STANDARD FUNCTION IMPORTS & PATTERNS (Use for Web Automation)
================================================================================

**SELENIUM FUNCTIONS (Use ONLY for web browser actions):**

1. **URL Launch:**
   from datas.supporting_files.launch_url import open_url_with_selenium
   driver = open_url_with_selenium(url)

2. **Web Element Interactions (Click, Type, Hover, Wait, Dropdown):**

    For ANY web element interaction including Click, Type, Hover, Element Wait, Dropdown Selection, Dropdown Click, or Scroll operations, you MUST use the following standardized format:
    
    **CRITICAL: execute_step CANNOT handle window switching operations. For window operations, use switch_to_window function (see section 6 below).**
    
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
       - Scroll + Click (NO type_input)
       - Any other DOM interactions (NO type_input)
    6. **WINDOW SWITCHING IS NOT SUPPORTED** - execute_step CANNOT handle window switching, tab switching, or window handle changes. Use switch_to_window function instead (see section 6).

    **KEYBOARD ACTIONS WITHIN EXECUTE_STEP:**
    If the user requests keyboard actions like pressing Enter, Tab, or any other keys within the web automation context, simply include the instruction in the description parameter. The execute_step function will handle it based on the description.
    
    Example for pressing Enter after typing:
    ```python
    var_name = "search_field"
    description = "Type 'selenium automation' and press Enter"
    type_input = "selenium automation"
    cwd = os.getcwd()
    execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
    ```
    
    Example for pressing Tab to navigate:
    ```python
    var_name = "tab_navigation"
    description = "Press Tab key to move to next field"
    cwd = os.getcwd()
    execute_step(driver, var_name, description, {{userid}}, cwd)
    ```

    **INCORRECT - Do NOT use:**
    ```python
    # ❌ WRONG - Direct implementation
    element = driver.find_element(By.XPATH, "//input[@id='username']")
    element.send_keys("admin")
    ```

    **CORRECT - For typing actions:**
    ```python
    # ✓ RIGHT - Using execute_step with type_input
    from datas.supporting_files.execute_step_code import execute_step

    var_name = "username_field"
    description = "Type username as admin"
    type_input = "admin"
    cwd = os.getcwd()

    execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
    ```

    **CORRECT - For non-typing actions:**
    ```python
    # ✓ RIGHT - Using execute_step WITHOUT type_input
    from datas.supporting_files.execute_step_code import execute_step

    var_name = "submit_button"
    description = "Click submit button"
    cwd = os.getcwd()

    execute_step(driver, var_name, description, {{userid}}, cwd)
    ```

    **Scroll and Click combined** (NO type_input) - Use single action with description "Scroll to element and click"
    ```python
    var_name = "submit_button"
    description = "Scroll to the submit button and clicks"
    cwd = os.getcwd()

    execute_step(driver, var_name, description, {{userid}}, cwd)
    ```

    **Parameters for execute_step:**
    - `driver`: Selenium WebDriver instance
    - `var_name`: Descriptive identifier for the action (e.g., "click_submit", "type_username")
    - `description`: Clear, detailed description of what action to perform (include keyboard actions like "press Enter" here if needed)
    - `{{userid}}`: User identifier placeholder (keep as-is)
    - `cwd`: Current working directory obtained via os.getcwd()
    - `type_input`: (ONLY for typing actions) The text/value to be entered into the field

    **CRITICAL NOTE:**
    The execute_step function ONLY accepts these arguments: driver, var_name, description, {{userid}}, cwd, type_input=type_input
    
    Do NOT pass any other arguments like:
    - press_enter
    - press_tab
    - window_handle
    - wait_time
    - or any other custom parameters
    
    For keyboard actions, include instructions in the description parameter.
    For window switching, use switch_to_window function (see section 6).

    This standardized approach ensures consistency, maintainability, and proper error handling across all web automation tasks.

3. **Text Extract from Web:**
   from datas.supporting_files.text_extract import text_data
   var_name = "action_name"
   description = "Full action description"
   cwd = os.getcwd()
   extracted_text = text_data(driver, var_name, description, {{userid}}, cwd)

4. **Element Exists Check:**
   from datas.supporting_files.element_exist import element_status
   var_name = "action_name"
   description = "Full action description"
   cwd = os.getcwd()
   exists_status = element_status(driver, var_name, description, {{userid}}, cwd)

5. **Table Extract from Web:**
   from datas.supporting_files.table_extract import table_df
   var_name = "action_name"
   description = "Full action description"
   cwd = os.getcwd()
   table_data = table_df(driver, var_name, description, {{userid}}, cwd)

6. **Switch or Change the driver to the specific window (change the window handle to specific number):**
    **CRITICAL: This is the ONLY way to handle window switching. Do NOT use execute_step for window operations.**
    
    from datas.supporting_files.window_handle import switch_to_window
    window_index = <window index number from user action as int type>
    switch_to_window(driver, window_index)
    
    **When to use this function:**
    - User asks to "switch to window 2" or "change to second window"
    - User asks to "switch to new tab" or "go to another window"
    - User asks to "change window handle to 1" or any window index
    - User mentions "window", "tab", "handle" in context of switching
    
    **Example usage:**
    ```python
    # Switch to second window (index 1, as indexing starts from 0)
    from datas.supporting_files.window_handle import switch_to_window
    window_index = 1
    switch_to_window(driver, window_index)
    ```
    
    **DO NOT use execute_step for window operations:**
    ```python
    # ❌ WRONG - execute_step cannot handle window switching
    execute_step(driver, "switch_window", "Switch to window 2", {{userid}}, cwd)
    ```

7. **Zoom in or Zoom out the driver/browser based on percentage:**
    from datas.supporting_files.browser_zoom import set_zoom
    percentage = <int type as number eg: 75 as for 75 %>
    set_zoom(driver, percentage)

8. **Maximize the Current window/browser:**
    from datas.supporting_files.maximize_window import max_window
    max_window(driver)
    
9. **Keyboard Button Actions:**

    **For Web/Selenium Actions (within browser context):**
    Use Selenium's Keys when interacting with web elements:
    
    - Enter key:
    ```python
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    ```
    
    - Tab key:
    ```python
    driver.switch_to.active_element.send_keys(Keys.TAB)
    ```
    
    **IMPORTANT: For keyboard actions within execute_step context, simply describe the action in the description parameter instead of using direct Selenium Keys.**

    **For Desktop/System-Level Actions (outside browser context):**
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

    **When to use which approach:**
    - Use description in execute_step for actions within the browser (form submissions, navigation within web pages)
    - Use Selenium Keys only when not using execute_step
    - Use PyAutoGUI for system-level actions or when interacting with elements outside the browser context

**NON-SELENIUM FUNCTIONS:**

1. **Email - Microsoft Graph API:**
   from datas.supporting_files.office365_email import fetch_latest_email_graph
   code = fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                                    sender_filter=None, subject_filter=None, timeout=180)

2. **Email - IMAP:**
   from datas.supporting_files.imap_email import fetch_latest_email_code
   code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                   folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

3. **Excel Read Function Usage Based on Row Limits:**

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
4.**Excel Write (Write the dataframe in to excel file)**:
    data_df=<respective dataframe which need to write>
    excel_file_path=<full excel file path where need to write>
    from datas.supporting_files.excel_write import write_df_to_file
    write_df_to_file(data_df,excel_file_path)
    
5. **Message Box:**
   from datas.supporting_files.message_box import popup_message_box
   popup_message_box(<message_to_display>)

6. **Time Delay:**
    from datas.supporting_files.time_delay import time_delay
    time_delay(<seconds_as_int>)

7. **PDF Split:**
    from datas.supporting_files.pdf_splitter import split_pdf
    pdf_file_path = <pdf_file_full_path>
    page_limit = <pages_per_split_as_int>
    destination_folder = <destination_folder_path>
    pdf_split(pdf_file_path, page_limit, destination_folder)

8. **PDF Highlighter:**
    from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
    pdf_path = <pdf_file_full_path>
    text = <text_to_highlight>
    output_path = <output_path>
    highlight_text_in_pdf(pdf_path, text, output_path)

9. **Extract Table from PDF:**
    from datas.supporting_files.pdf_xl import pdf_to_table_extract
    description = "Full action description"
    pdf_file = <Full pdf file path>
    table_df = pdf_to_table_extract(pdf_file, description)

10. **Mail Attachment Download (using Microsoft Graph API with tenant_id, client_id, client_secret):**
    from datas.supporting_files.ms_mail_attach_download import download_outlook_attachments
    from_mail = <from_mail_address>
    tenant = <tenant_id>
    client_id = <client_id>
    client_secret = <client_secret>
    download_path = <a full folder path from given path on the requirement>
    download_outlook_attachments(from_mail, tenant, client_id, client_secret, download_path)
    
11. **OCR Text Extract (Extract text from image):**
    from datas.supporting_files.ocr_text_extract import text_extract
    img_file_path = <Full image path from user action>
    description = <User Action from requirement>
    ocr_text = text_extract(img_file_path, description)

12. **Mail Send (using Microsoft Graph API with tenant_id, client_id, client_secret, attachments-optional):**
    from datas.supporting_files.office365_mail_send import send_mail_ms_graph
    from_mail = <from_mail_address>
    to_mail = <to_mail_address>
    tenant = <tenant_id>
    client_id = <client_id>
    client_secret = <client_secret>
    subject = <mail subject>
    body = <mail body>
    attachments = <list of attachments>
    send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments)

    Rules for subject and body assigning:
        • If only `body` is provided and `subject` is empty or not provided, automatically generate a suitable subject based on the body content.
        • If only `subject` is provided and `body` is empty or not provided, automatically generate a meaningful body based on the subject.
        • If both are provided, use them as-is.
        • If attachments are provided, attach them to the email.(optional)

    Execution:
        send_mail_ms_graph(from_mail, to_mail, tenant, client_id, client_secret, subject, body, attachments=None)

13. **Mail Read (using Microsoft Graph API with tenant_id, client_id, client_secret):**
    from datas.supporting_files.office365_mail_read import read_latest_mail_ms_graph
    from_mail = <from_mail_address>
    tenant = <tenant_id>
    client_id = <client_id>
    client_secret = <client_secret>
    body = read_latest_mail_ms_graph(from_mail, tenant, client_id, client_secret)

    returns:
        - body (plain-text email body, cleaned from HTML)

14. **OTP extraction from mail (passing mail body directly):**
    from datas.supporting_files.otp_mail_read import gemini_extract_otp_from_mail
    mail_body = <mail_body>
    otp = gemini_extract_otp_from_mail(mail_body)

    
15. **Queue Operations (ONLY when explicitly mentioned):**
    
    a) Get Queue:
    from datas.supporting_files.getqueue import get_task_from_queue
    api_key = <api_key>
    records, rowid, status_val, status_res, startTime, queuename, queueemail = get_task_from_queue(api_key)
    
    b) Upload Queue:
    from datas.supporting_files.update_queue import queue_upload
    api_key = <api_key>
    queue_upload(api_key, <data_to_upload>)
    
    c) Update Queue Status:
    from datas.supporting_files.queue_update_status import queue_update
    api_key = <api_key>
    status_update = "success"  # or "failed"
    queue_update(api_key, records, status_update, startTime)

================================================================================
MODIFICATION RULES - CRITICAL
================================================================================

**RULE 1: COMPLETE CODE RETURN**
- You MUST return the ENTIRE modified code
- Include ALL existing imports, ALL existing steps, ALL existing logic
- DO NOT return only the new/modified sections
- DO NOT truncate or abbreviate any part of the code

**RULE 2: PRESERVE EXISTING STRUCTURE**
- Keep ALL existing code exactly as-is unless modification is explicitly required
- DO NOT remove any existing steps unless user explicitly asks to remove them
- Maintain ALL existing step comments (#Step 1:, #Step 2:, etc.)
- Preserve ALL existing variable names, indentation, and formatting
- Keep ALL existing imports and function definitions
- Default behavior: ADD or MODIFY, never DELETE unless explicitly requested

**RULE 3: ADDING NEW STEPS**
When user asks to add a new action (e.g., "after step 3, click dashboard"):
1. Keep ALL existing steps before the insertion point
2. Insert the new step(s) at the correct location
3. Update step numbers for all subsequent steps
4. Keep ALL existing steps after the insertion point
5. Add necessary imports at the top if not already present

Example: If adding after Step 3:
- Keep Steps 1, 2, 3 exactly as-is
- Insert new step as Step 4
- Renumber old Step 4 → new Step 5
- Renumber old Step 5 → new Step 6
- Continue renumbering ALL remaining steps

**RULE 4: MODIFYING EXISTING STEPS**
When user asks to modify an existing step:
1. Keep ALL steps before the target step
2. Modify ONLY the target step
3. Keep ALL steps after the target step
4. Do not change step numbers unless adding/removing steps

**RULE 5: REMOVING STEPS**
When user EXPLICITLY asks to remove a step (e.g., "remove step 5", "delete the login step"):
1. Keep ALL steps before the target step
2. Remove ONLY the specified step(s)
3. Renumber ALL subsequent steps
4. Keep ALL remaining code intact

**CRITICAL: Only remove steps if user explicitly uses words like "remove", "delete", "take out", or clearly indicates removal.**
**If user just asks to "add" or "modify", NEVER remove existing steps.**

**RULE 6: IMPORT MANAGEMENT**
- Add new imports at the top of try block with other imports
- Check if import already exists before adding
- Remove imports ONLY if they're no longer used anywhere in the code
- Group imports from datas.supporting_files together

**RULE 7: VARIABLE NAMING**
- Each var_name must be unique across the entire code
- For duplicate element names, use increments: button1, button2, button3
- Check existing var_names before adding new ones

**RULE 8: CONTEXTUAL INSERTION**
When adding web actions, determine correct function based on action type:
- Click, Type, Select, Check → use execute_step
- Extract text → use text_data
- Check if exists → use element_status
- Extract table → use table_df
- **Window switching/changing → use switch_to_window (NEVER use execute_step)**
- File operations (copy, move, rename) → use direct Python code (shutil, os)
- PDF operations → use pdf_splitter or pdf_highlighter or direct PyPDF2

**RULE 9: WINDOW SWITCHING DETECTION**
When user query contains any of these indicators, use switch_to_window function:
- "switch to window"
- "change to window"
- "go to window"
- "switch to tab"
- "change to tab"
- "window handle"
- "second window"
- "new window"
- "another window"
- "window 1", "window 2", etc.

DO NOT use execute_step for these operations. Always use:
```python
from datas.supporting_files.window_handle import switch_to_window
window_index = <index_number>
switch_to_window(driver, window_index)
```

================================================================================
MODIFICATION EXAMPLES
================================================================================

**Example 1: Adding a Click Action After Step 3**

User Query: "After step 3, click on Dashboard button"

Approach:
1. Keep Steps 1-3 exactly as-is
2. Add new Step 4:
   # Step 4: Click Dashboard button
   var_name = "dashboard_button"
   description = "Click Dashboard button"
   execute_step(driver, var_name, description, {{userid}}, cwd)
3. Renumber old Step 4 → new Step 5
4. Renumber old Step 5 → new Step 6
5. Continue renumbering ALL remaining steps
6. Keep ALL other code exactly as-is

**Example 2: Adding Excel Read**

User Query: "Add code to read Excel file from C:\\data\\file.xlsx and store in df"

Approach:
1. Add import at top of try block:
   from datas.supporting_files.excel_read import excel_read_file
2. Add code at appropriate location (determine from context):
   # Step N: Read Excel file
   file_path = "C:\\\\data\\\\file.xlsx"
   df = excel_read_file(file_path)
3. Renumber subsequent steps
4. Keep ALL other existing code

**Example 3: Adding Message Box**

User Query: "Add message box showing 'Process Complete' at the end"

Approach:
1. Add import at top if not present:
   from datas.supporting_files.message_box import popup_message_box
2. Add before the except block:
   # Step N: Display completion message
   popup_message_box("Process Complete")
3. Keep ALL existing code before this

**Example 4: Modifying Existing Step**

User Query: "Change step 5 to type 'newpassword' instead of '1234'"

Approach:
1. Keep Steps 1-4 exactly as-is
2. Modify Step 5:
   # Step 5: Type password as newpassword
   var_name = "password_field"
   description = "Type password as newpassword"
   type_input = "newpassword"
   execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
3. Keep Steps 6+ exactly as-is
4. Do NOT change step numbers

**Example 5: NOT Removing Steps (Important)**

User Query: "After step 3, add click on Dashboard"

WRONG APPROACH: Remove steps 4, 5, 6... and only add dashboard click
CORRECT APPROACH:
1. Keep ALL Steps 1-3 exactly as-is
2. Insert new Step 4 for Dashboard click
3. Renumber old Step 4 → new Step 5
4. Keep ALL remaining steps with renumbered step comments
5. NEVER remove existing steps unless explicitly asked

**Example 6: Explicitly Removing a Step**

User Query: "Remove step 5" or "Delete the password typing step"

Approach:
1. Keep Steps 1-4 exactly as-is
2. Remove Step 5 completely
3. Renumber old Step 6 → new Step 5
4. Renumber old Step 7 → new Step 6
5. Continue renumbering ALL remaining steps
6. Keep ALL other code intact

**Example 7: Window Switching**

User Query: "After step 3, switch to window 2"

Approach:
1. Keep Steps 1-3 exactly as-is
2. Add import if not present:
   from datas.supporting_files.window_handle import switch_to_window
3. Add new Step 4:
   # Step 4: Switch to window 2
   window_index = 1  # Index 1 for second window (0-based indexing)
   switch_to_window(driver, window_index)
4. Renumber old Step 4 → new Step 5
5. Continue renumbering ALL remaining steps
6. Keep ALL other code exactly as-is

**WRONG - Do NOT use execute_step for window switching:**
```python
# ❌ WRONG
var_name = "switch_window"
description = "Switch to window 2"
execute_step(driver, var_name, description, {{userid}}, cwd)
```

**Example 8: Typing with Keyboard Action**

User Query: "Type 'search term' in search box and press Enter"

Approach:
```python
# Step N: Type search term and press Enter
var_name = "search_box"
description = "Type search term and press Enter"
type_input = "search term"
execute_step(driver, var_name, description, {{userid}}, cwd, type_input=type_input)
```

Note: The keyboard action (press Enter) is included in the description, not as a separate parameter.

================================================================================
CRITICAL REMINDERS
================================================================================

1. **ALWAYS return the COMPLETE code** - Never return partial code
2. **PRESERVE ALL existing steps** - Don't remove unless explicitly asked with clear deletion keywords
3. **DEFAULT to ADD/MODIFY** - Unless user says "remove", "delete", keep everything
4. **RENUMBER steps** when adding/removing steps
5. **ADD imports** at top of try block when adding new functionality
6. **USE correct function** based on action type:
   - execute_step for clicks/types/hovers/scrolls/waits/dropdowns
   - text_data for text extracts
   - element_status for existence checks
   - table_df for table extracts
   - **switch_to_window for window switching (NEVER execute_step)**
7. **MAINTAIN structure** - Keep try/except/finally, function definition, all imports
8. **NO MARKDOWN** - Return only Python code, no ```python or ``` tags
9. **NO EXPLANATIONS** - Return only code with step comments
10. **EXPLICIT DELETION ONLY** - Remove steps only when user clearly states to remove/delete them
11. **EXECUTE_STEP ARGUMENTS** - Only use: driver, var_name, description, {{userid}}, cwd, type_input=type_input (type_input only for typing actions)
12. **NO EXTRA PARAMETERS** - Never pass press_enter, press_tab, window_handle, or any other parameters to execute_step
13. **KEYBOARD ACTIONS** - Include keyboard instructions in the description parameter
14. **WINDOW OPERATIONS** - Always use switch_to_window function, never execute_step
15. **PURE PYTHON OUTPUT** - Response must be ONLY executable Python code with NO additional text, markdown, or explanations

================================================================================
FINAL OUTPUT CHECKLIST - VERIFY BEFORE RESPONDING
================================================================================

Before generating your response, verify:

✓ Response starts immediately with Python code (def aba_agent(): or import statements)
✓ NO markdown formatting (no ```, no ```python)
✓ NO explanatory text before the code
✓ NO explanatory text after the code
✓ NO comments outside the code explaining changes
✓ ONLY standard Python comments that are part of the code itself (like #Step 1:)
✓ ALL existing code is preserved (unless explicit deletion requested)
✓ ALL step numbers are correct and sequential
✓ ALL imports are at the top of the try block
✓ execute_step only uses allowed parameters
✓ Window switching uses switch_to_window function
✓ Code is syntactically correct and directly executable

**Your ENTIRE response will be written directly to a .py file. Make sure it contains ONLY valid Python code.**

Generate the complete modified code now:
"""
    
    content=[modified_prompt]
    for path in filepaths:
        try:
            # Validate file exists
            if not os.path.exists(path):
                print(f"[ERROR] File not found: {path}")
                content.append(f"\n\n--- File: {path} ---\nERROR: File not found\n")
                continue
            
            # Check file size (Gemini has limits)
            file_size = os.path.getsize(path)
            print(f"[INFO] Processing file: {path} ({file_size} bytes)")
            
            # Handle Excel/CSV as text
            if path.lower().endswith((".xlsx", ".xls", ".csv")):
                try:
                    if path.lower().endswith(".csv"):
                        df = pd.read_csv(path)
                    else:
                        df = pd.read_excel(path)
                    file_text = df.to_string(index=False)
                    content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
                    print(f"[OK] Converted tabular file to text: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to read tabular file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Could not read file - {str(e)}\n")
            
            # Handle text files as inline text
            elif path.lower().endswith((".txt", ".py", ".json", ".xml", ".log")):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_text = f.read()
                    content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
                    print(f"[OK] Read text file: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to read text file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Could not read file - {str(e)}\n")
            
            # Handle binary files via upload API
            else:
                try:
                    uploaded_file = genai.upload_file(path)
                    # Wait for file to be processed
                    import time
                    time.sleep(1)  # Give API time to process
                    content.append(uploaded_file)
                    print(f"[OK] Uploaded file via API: {path}")
                except Exception as e:
                    print(f"[ERROR] Failed to upload file {path}: {e}")
                    content.append(f"\n\n--- File: {path} ---\nERROR: Upload failed - {str(e)}\n")
        
        except Exception as e:
            print(f"[ERROR] Unexpected error processing {path}: {e}")
            content.append(f"\n\n--- File: {path} ---\nERROR: {str(e)}\n")
    
    print(f"[INFO] Final content list has {len(content)} items")
    print(f"[INFO] Content types: {[type(c).__name__ for c in content]}")
    
    try:
        response = chat.send_message(content)

        final_code = response.text
        # with open(file_path, "r", encoding="utf-8") as f:
        #     final_code = f.read()
        # final_code='This is a breakdown of the user\'s request and the context provided:\n\n**Role:** The assistant is an expert Python code modification specialist for web automation and authentication.\n\n**Content:** The user provided existing Python code that automates interactions with Amazon.com, specifically searching for "shoe," applying a size filter, and selecting size 10. It also includes a separate function `find_primes_in_range` and related questions about prime numbers.\n\n**User\'s Request:** The user wants the *entire* code to be changed to find even numbers between 1 and 1000. They also want a list of similar questions related to this new task.\n\n**Analysis of the Request:**\nThe user\'s request is a complete overhaul. The existing web automation code needs to be entirely replaced by a new script that finds even numbers. The prime number function and its associated questions are also irrelevant to the new task and should be removed. The core requirement is to generate a Python script that iterates from 1 to 1000 and identifies all even numbers.\n\n```python\n# STEP 1: Find even numbers between 1 and 1000\neven_numbers = []\nfor num in range(1, 1001):\n    if num % 2 == 0:\n        even_numbers.append(num)\n\n# STEP 2: Print the list of even numbers\nprint(f"Even numbers between 1 and 1000: {even_numbers}")\n\n# Important similar questions:\n# 1. How to find odd numbers in a range?\n# 2. How to generate a list of numbers with a specific step?\n# 3. How to filter a list of numbers based on a condition in Python?\n# 4. How to find multiples of a given number within a range?\n# 5. How to implement loops and conditional statements in Python for number sequences?\n# 6. How to write functions to perform mathematical operations on ranges of numbers?\n# 7. How to work with large lists and optimize memory usage in Python?\n# 8. How to use list comprehensions for concise list generation?\n# 9. How to find prime numbers in a range (related to the original code\'s context)?\n# 10. How to perform basic arithmetic operations in Python?\n```'
        match = re.search(r"```(?:\w+)?\n(.*?)```", final_code, re.DOTALL)
        if match:
            final_code = match.group(1)
        
        res_msg = response_msg(input)
        
        # Get updated chat history from the response object
        updated_history = chat.history
        res="failed"
        while res!="success":
            try:
                exec(final_code)
                res="success"
            except Exception as e:
                print(e)
                import traceback
                error_data=traceback.format_exc()
                final_code=error_fix(final_code,error_data)
            
           

        if exception_found and main_code == exception_code:
            with open(exception_file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            return org_code, res_msg, updated_history
        elif exception_found and exception_same:
            with open(exception_file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            return final_code, res_msg, updated_history
        else:
            return final_code, res_msg, updated_history
    
    except Exception as e:
        print(f"[ERROR] Failed to send message to Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None, f"ERROR: {str(e)}", chat_history

# filepaths=[r"C:\Users\Kishore.k\Documents\automation_code.py",
# r"C:\Users\Kishore.k\Downloads\pdf_highlighter.py",
# r"C:\Users\Kishore.k\Downloads\claims_sample.xlsx"]
# file_path = "new.py"
# with open(file_path, "r", encoding="utf-8") as f:
#     code = f.read()
# exception_info="Traceback (most recent call last):\n  File \"d:\\Droidal\\ABA\\oct\\17-10\\aba\\backup.py\", line 119, in aba_agent\n    from proj_93.task_178 import orders_in_dropdown\n  File \"d:\\Droidal\\ABA\\oct\\17-10\\aba\\proj_93\\task_178\\orders_in_dropdown.py\", line 12\n    element_xpath_to_use = \"//div[@id='searchOrderList']/div[@class='panel filter_panel']/div[@class='panel-body p-lg']/div[@class='filters d-flex flex-row-wrap flex-as flex-jsb flex-gap-lg']/div[@id='order_type_container']/div[@class='filter_container']/div[@id='order_type_filter']/span[@class='k-widget k-dropdown k-header full_width form-control k-dropdown-clearable']/span[@class='k-dropdown-wrap k-state-default']/input[@role='listbox'] # Use the provided current element's XPath\n                           ^\nSyntaxError: unterminated string literal (detected at line 12)\n"
# input=f"I got this error need to fix it : {exception_info}"
# response=chat_request(code,input,[])
# with open("backup.py", "w", encoding="utf-8") as f:
#     f.write(response[0])
