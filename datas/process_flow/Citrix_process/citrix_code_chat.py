import google.generativeai as genai
import config
import pandas as pd

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

def chat_request(code,input,filepaths):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    modified_prompt=prompt = f"""
You are an expert Python code modification assistant specializing in Citrix automation workflows with strict adherence to standardized code patterns.

User Query: {input}

The user wants to modify the following existing code based on their request:

Existing Code:
{code}

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
STANDARD FUNCTION IMPORTS & PATTERNS (MANDATORY FOR ALL MODIFICATIONS)
================================================================================
When adding or modifying code, you MUST use these standard patterns:

1. **URL Launch Function:**
from datas.supporting_files.citrix_process.launch_url import open_url_with_selenium
driver = open_url_with_selenium(url)
- Always returns 'driver' variable

2. **Email Fetching - Microsoft Graph API (Office 365):**
from datas.supporting_files.citrix_process.office365_email import fetch_latest_email_graph
code = fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                                sender_filter=None, subject_filter=None, timeout=180)

3. **Email Fetching - IMAP (Gmail, Yahoo, Custom Domains):**
from datas.supporting_files.citrix_process.imap_email import fetch_latest_email_code
code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

4. **Excel Read from File:**
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

5. **Message Box:**
from datas.supporting_files.citrix_process.message_box import popup_message_box
popup_message_box(<msg to populate>)

6. **Extract Text from Field:**
from datas.supporting_files.citrix_process.text_extract import text_data
var_name = "action_name"
description = "Full action description"
org_path = os.getcwd()
<relevant_variable> = text_data(var_name, description, {{userid}}, org_path)

CRITICAL: Never pass 'driver' as an argument to text_data - it only takes: var_name, description, {{userid}}, org_path

7. **Element Exists:**
from datas.supporting_files.citrix_process.element_exist import element_status
var_name = "action_name"
description = "Full action description"
org_path = os.getcwd()
<status_variable> = element_status(var_name, description, {{userid}}, org_path)

CRITICAL: Never pass 'driver' as an argument to element_status - it only takes: var_name, description, {{userid}}, org_path

8. **Table Extract:**
from datas.supporting_files.citrix_process.table_extract import table_df
var_name = "action_name"
description = "Full action description"
org_path = os.getcwd()
table_data_df = table_df(var_name, description, {{userid}}, org_path)

CRITICAL: Never pass 'driver' as an argument to table_df - it only takes: var_name, description, {{userid}}, org_path

9. **Time Delay:**
from datas.supporting_files.citrix_process.time_delay import time_delay
time_delay(<respective seconds as int type>)

10. **PDF Split (Page wise)**
    from datas.supporting_files.citrix_process.pdf_splitter import split_pdf
    pdf_path=<pdf file full path>
    page_limit=<limit pages per split in int type>
    dest_folder=<destination folder for splitted files to save if doesn't provide any means just keep the actual pdf file folder path>
    pdf_split(pdf_path,page_limit,dest_folder)

11. **PDF Highlighter:**
    from datas.supporting_files.citrix_process.pdf_highlighter import highlight_text_in_pdf
    pdf_path=<pdf file full path>
    text=<text to highlight>
    output_path=<save as seperate file means that path else same pdf path>
    highlight_text_in_pdf(pdf_path,text,output_path)

12. **Mail Attachement Download (using Microsoft Graph API with tenant_id, client_id, client_secret)**
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


    
16. **Execute Step (for all UI element interactions):**
    from datas.supporting_files.citrix_process.execute_step_code import execute_step
    import os
    cwd = os.getcwd()
    var_name = "action_name"
    description = "Full action description"
    execute_step(var_name, description, {{userid}}, cwd)
    
    CRITICAL RULES:
    - execute_step must be called ONLY with these arguments: var_name, description, {{userid}}, cwd
    - Never pass 'driver' as an argument to execute_step
    - Additional information must be included inside the description string, not as extra arguments
    - Always reuse the variable names "var_name" and "description" - do not create unique names like "button_var_name"

17. **Queue Operations (ONLY when explicitly mentioned):**
    
    a) Get Queue (Retrieve from Queue):
    from datas.supporting_files.citrix_process.getqueue import get_task_from_queue
    api_key = <which is passed>
    records, rowid, status_val, status_res, startTime, queuename, queueemail = get_task_from_queue(api_key)
    
    b) Upload Queue:
    from datas.supporting_files.citrix_process.update_queue import queue_upload
    api_key = <which is passed>
    queue_upload(api_key, <data_to_pushed_on_queue>)
    
    c) Update Queue Status:
    from datas.supporting_files.citrix_process.queue_update_status import queue_update
    statusupdate = "success"  # or "failed"
    api_key = <which is passed>
    queue_update(api_key, records, statusupdate, startTime)

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
- ALL imports must remain INSIDE the aba_agent() function - never move them outside

**RULE 3: ADDING NEW STEPS**
When user asks to add a new action (e.g., "after step 3, click dashboard"):
1. Keep ALL existing steps before the insertion point
2. Insert the new step(s) at the correct location
3. Update step numbers for all subsequent steps
4. Keep ALL existing steps after the insertion point
5. Add necessary imports at the top of try block if not already present (INSIDE aba_agent)

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
- ALL imports must be placed INSIDE the aba_agent() function
- Add new imports at the top of try block with other imports (INSIDE aba_agent)
- Check if import already exists before adding
- Remove imports ONLY if they're no longer used anywhere in the code
- Group imports from datas.supporting_files.citrix_process together
- NEVER place imports outside the aba_agent() function definition

**RULE 7: VARIABLE NAMING - UNIQUENESS ENFORCEMENT (CRITICAL)**
- BEFORE adding any new var_name, scan the ENTIRE existing code to identify ALL currently used var_name values
- Each var_name VALUE must be GLOBALLY UNIQUE across the entire project - no duplicates allowed
- When adding new variables, check against all existing var_name VALUE assignments in the code
- For duplicate element names, use incremented suffixes: continue_button, continue_button1, continue_button2, continue_button3, etc.
- Apply this rule to ALL functions that use var_name parameter: execute_step, text_data, element_status, table_df
- If user requests adding an action with a name that already exists, automatically increment it (e.g., if "login_button" exists, use "login_button1")
- Always reuse variable names "var_name" and "description" - never create unique variable names

**CRITICAL: Element Existence Checks**
- When adding element_status (exists check) before an action, the var_name VALUE for the exists check MUST be different from the action's var_name VALUE
- Pattern: If action uses var_name = "button_name", the exists check MUST use var_name = "button_name_exist" or "button_name_exists"
- ALWAYS reuse the simple variable names "var_name" and "description" for assignments

**RULE 8: CONTEXTUAL INSERTION**
When adding UI actions, determine correct function based on action type:
- Click, Type, Select, Check → use execute_step (NO driver parameter)
- Extract text → use text_data (NO driver parameter)
- Check if exists → use element_status (NO driver parameter)
- Extract table → use table_df (NO driver parameter)
- File operations (copy, move, rename) → use direct Python code (shutil, os)
- PDF operations → use pdf_splitter or pdf_highlighter

**RULE 9: QUEUE OPERATION RULES**
- Add queue operations ONLY when user explicitly requests them
- Use keywords: "queue", "get from queue", "upload to queue", "update queue status"
- When adding queue operations, include the necessary import (INSIDE aba_agent)

**RULE 10: EMAIL OPERATION RULES**
- Use Microsoft Graph API for: Office 365, Outlook, Microsoft email, tenant, Azure AD
- Use IMAP for: Gmail, Yahoo, custom domains, or when email/password provided
- Write email fetching directly inside aba_agent() as native code
- Never wrap email logic in var_name/description pattern
- sender_filter and subject_filter must be optional (default=None)

================================================================================
MODIFICATION EXAMPLES
================================================================================

**Example 1: Adding a Click Action After Step 3**

User Query: "After step 3, click on Dashboard button"

Approach:
1. Keep Steps 1-3 exactly as-is
2. Check existing var_name values: ["username_field", "password_field", "login_button"]
3. Add new Step 4:
   # Step 4: Click Dashboard button
   var_name = "dashboard_button"
   description = "Click Dashboard button"
   execute_step(var_name, description, {{userid}}, cwd)
4. Renumber old Step 4 → new Step 5
5. Renumber old Step 5 → new Step 6
6. Continue renumbering ALL remaining steps
7. Keep ALL other code exactly as-is

**Example 2: Adding Excel Read**

User Query: "Add code to read Excel file from C:\\data\\file.xlsx and store in df"

Approach:
1. Add import at top of try block INSIDE aba_agent:
   from datas.supporting_files.citrix_process.excel_read import excel_read_file
2. Add code at appropriate location:
   # Step N: Read Excel file
   file_path = "C:\\\\data\\\\file.xlsx"
   df = excel_read_file(file_path)
3. Renumber subsequent steps
4. Keep ALL other existing code

**Example 3: Adding Message Box**

User Query: "Add message box showing 'Process Complete' at the end"

Approach:
1. Add import at top if not present (INSIDE aba_agent):
   from datas.supporting_files.citrix_process.message_box import popup_message_box
2. Add before the except block:
   # Step N: Display completion message
   popup_message_box("Process Complete")
3. Keep ALL existing code before this

**Example 4: Modifying Existing Step**

User Query: "Change step 5 to type 'newpassword' instead of '1234'"

Approach:
1. Keep Steps 1-4 exactly as-is
2. Modify Step 5 description:
   # Step 5: Type password as newpassword
   var_name = "password_field"
   description = "Type password as newpassword"
   execute_step(var_name, description, {{userid}}, cwd)
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

**Example 7: Adding Element Exists Check with Unique var_name**

User Query: "Before clicking Continue button, check if it exists"

Check existing var_name values: ["login_button", "username_field", "continue_button"]

Correct Addition:
```python
# Add imports if needed (INSIDE aba_agent)
from datas.supporting_files.citrix_process.element_exist import element_status
from datas.supporting_files.citrix_process.execute_step_code import execute_step

cwd = os.getcwd()

# Check if element exists (unique var_name with _exist suffix)
var_name = "continue_button_exist"
description = "Check if Continue button exists"
if element_status(var_name, description, {{userid}}, cwd):
    # Click the button (different var_name without _exist)
    var_name = "continue_button1"  # Incremented because "continue_button" already exists
    description = "Click Continue button"
    execute_step(var_name, description, {{userid}}, cwd)
```

INCORRECT - DO NOT DO THIS:
```python
# WRONG - Same var_name value for both
var_name = "continue_button"
if element_status(var_name, description, {{userid}}, cwd):
    var_name = "continue_button"  # DUPLICATE
    execute_step(var_name, description, {{userid}}, cwd)

# WRONG - Passing driver parameter
execute_step(driver, var_name, description, {{userid}}, cwd)

# WRONG - Creating unique variable names
continue_var_name = "continue_button"  # Should just use "var_name"
```

================================================================================
CRITICAL REMINDERS
================================================================================

1. **ALWAYS return the COMPLETE code** - Never return partial code
2. **PRESERVE ALL existing steps** - Don't remove unless explicitly asked with clear deletion keywords
3. **DEFAULT to ADD/MODIFY** - Unless user says "remove", "delete", keep everything
4. **RENUMBER steps** when adding/removing steps
5. **ADD imports INSIDE aba_agent()** at top of try block when adding new functionality
6. **USE correct function** without driver parameter (execute_step, text_data, element_status, table_df)
7. **MAINTAIN structure** - Keep try/except/finally, function definition, all imports INSIDE aba_agent
8. **NO MARKDOWN** - Return only Python code, no ```python or ``` tags
9. **NO EXPLANATIONS** - Return only code with step comments
10. **EXPLICIT DELETION ONLY** - Remove steps only when user clearly states to remove/delete them
11. **UNIQUE var_name VALUES** - Check all existing var_name values before adding new ones
12. **REUSE variable names** - Always use "var_name" and "description", never create unique names
13. **NO driver parameter** - Never pass driver to execute_step, text_data, element_status, table_df

================================================================================
OUTPUT REQUIREMENTS (CRITICAL - ABSOLUTE RULES)
================================================================================

**THESE RULES ARE MANDATORY AND NON-NEGOTIABLE:**

1. **OUTPUT FORMAT - PYTHON CODE ONLY**:
   - Your response must contain ONLY executable Python code
   - ABSOLUTELY NO markdown code blocks (no ```python, no ```, no backticks)
   - ABSOLUTELY NO explanations, descriptions, or commentary
   - ABSOLUTELY NO text before or after the code
   - First character must be Python code, last character must be Python code

2. **CODE VALIDITY**:
   - Code must be syntactically correct Python
   - All imports must be INSIDE aba_agent() function
   - All variables defined before use
   - Proper indentation throughout

3. **COMPLETENESS**:
   - Return the ENTIRE modified code file
   - ALL imports INSIDE the aba_agent() function
   - Include complete aba_agent() function structure
   - Include try/except/finally blocks
   - Verify NO imports are outside aba_agent()

4. **STANDARD COMPLIANCE**:
   - All modifications follow standard patterns
   - All supporting_files imports use exact syntax
   - All function calls match exact parameter signatures
   - All var_name values globally unique
   - Never pass driver to execute_step, text_data, element_status, table_df

Generate the complete modified code now (PYTHON CODE ONLY, NO EXPLANATIONS):
"""


    content=[modified_prompt]
    for path in filepaths:
        if path.endswith((".xlsx", ".csv")):
            file_text = convert_xlsx_to_text(path)
            content.append(f"\n\n--- File: {path} ---\n{file_text}\n")
        else:
            content.append(genai.upload_file(path))
    prompt = content
    response = chat.send_message(prompt)
    final_code=response.text
    if final_code.startswith("```"):
        final_code = "\n".join(final_code.strip().split("\n")[1:-1])
    res_msg=response_msg(input)
    return final_code,res_msg

# filepaths=[r"C:\Users\Kishore.k\Documents\automation_code.py",
# r"C:\Users\Kishore.k\Downloads\pdf_highlighter.py",
# r"C:\Users\Kishore.k\Downloads\claims_sample.xlsx"]
# code=""
# input="Analyze the attached files and summarize the context"
# response=chat_request(code,input,filepaths)
# print(response)
