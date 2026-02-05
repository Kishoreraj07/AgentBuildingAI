import google.generativeai as genai
import config
import pandas as pd
import os
import re,json

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

def chat_request(code,input,filepaths):
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
    chat = model.start_chat()

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
STANDARD FUNCTION IMPORTS & PATTERNS (Use for Web Automation)
================================================================================

**SELENIUM FUNCTIONS (Use ONLY for web browser actions):**

1. **URL Launch:**
   from datas.supporting_files.launch_url import open_url_with_selenium
   driver = open_url_with_selenium(url)

2. **Click & Type (Web element interactions):**
   from datas.supporting_files.execute_step_code import execute_step
   var_name = "action_name"
   description = "Full action description"
   cwd = os.getcwd()
   execute_step(driver, var_name, description, {{userid}}, cwd)

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

**NON-SELENIUM FUNCTIONS:**

6. **Email - Microsoft Graph API:**
   from datas.supporting_files.office365_email import fetch_latest_email_graph
   code = fetch_latest_email_graph(user_email, tenant_id, client_id, client_secret,
                                    sender_filter=None, subject_filter=None, timeout=180)

7. **Email - IMAP:**
   from datas.supporting_files.imap_email import fetch_latest_email_code
   code = fetch_latest_email_code(email_id, email_pass, imap_server="imap.gmail.com",
                                   folder="INBOX", sender_filter=None, subject_filter=None, timeout=180)

8. **Excel Read:**
   from datas.supporting_files.excel_read import excel_read_file
   file_full_path = <full_path>
   file_data_frame = excel_read_file(file_full_path)

9. **Message Box:**
   from datas.supporting_files.message_box import popup_message_box
   popup_message_box(<message_to_display>)

10. **Time Delay:**
    from datas.supporting_files.time_delay import time_delay
    time_delay(<seconds_as_int>)

11. **PDF Split:**
    from datas.supporting_files.pdf_splitter import split_pdf
    pdf_file_path = <pdf_file_full_path>
    page_limit = <pages_per_split_as_int>
    destination_folder = <destination_folder_path>
    pdf_split(pdf_file_path, page_limit, destination_folder)

12. **PDF Highlighter:**
    from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
    pdf_path = <pdf_file_full_path>
    text = <text_to_highlight>
    output_path = <output_path>
    highlight_text_in_pdf(pdf_path, text, output_path)

13. **Queue Operations (ONLY when explicitly mentioned):**
    
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
- File operations (copy, move, rename) → use direct Python code (shutil, os)
- PDF operations → use pdf_splitter or pdf_highlighter or direct PyPDF2

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
2. Modify Step 5 description:
   # Step 5: Type password as newpassword
   var_name = "password_field"
   description = "Type password as newpassword"
   execute_step(driver, var_name, description, {{userid}}, cwd)
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

================================================================================
CRITICAL REMINDERS
================================================================================

1. **ALWAYS return the COMPLETE code** - Never return partial code
2. **PRESERVE ALL existing steps** - Don't remove unless explicitly asked with clear deletion keywords
3. **DEFAULT to ADD/MODIFY** - Unless user says "remove", "delete", keep everything
4. **RENUMBER steps** when adding/removing steps
5. **ADD imports** at top of try block when adding new functionality
6. **USE correct function** based on action type (execute_step for clicks/types, text_data for extracts, etc.)
7. **MAINTAIN structure** - Keep try/except/finally, function definition, all imports
8. **NO MARKDOWN** - Return only Python code, no ```python or ``` tags
9. **NO EXPLANATIONS** - Return only code with step comments
10. **EXPLICIT DELETION ONLY** - Remove steps only when user clearly states to remove/delete them

================================================================================
OUTPUT REQUIREMENTS
================================================================================

1. Return the COMPLETE, ENTIRE modified Python code
2. Include ALL existing code plus modifications
3. NO markdown formatting (no ```python or ```)
4. NO explanations or commentary outside the code
5. Maintain proper indentation throughout
6. Keep step comment format: #Step N: <description>
7. Ensure code is syntactically correct and executable

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
        # final_code='This is a breakdown of the user\'s request and the context provided:\n\n**Role:** The assistant is an expert Python code modification specialist for web automation and authentication.\n\n**Content:** The user provided existing Python code that automates interactions with Amazon.com, specifically searching for "shoe," applying a size filter, and selecting size 10. It also includes a separate function `find_primes_in_range` and related questions about prime numbers.\n\n**User\'s Request:** The user wants the *entire* code to be changed to find even numbers between 1 and 1000. They also want a list of similar questions related to this new task.\n\n**Analysis of the Request:**\nThe user\'s request is a complete overhaul. The existing web automation code needs to be entirely replaced by a new script that finds even numbers. The prime number function and its associated questions are also irrelevant to the new task and should be removed. The core requirement is to generate a Python script that iterates from 1 to 1000 and identifies all even numbers.\n\n```python\n# STEP 1: Find even numbers between 1 and 1000\neven_numbers = []\nfor num in range(1, 1001):\n    if num % 2 == 0:\n        even_numbers.append(num)\n\n# STEP 2: Print the list of even numbers\nprint(f"Even numbers between 1 and 1000: {even_numbers}")\n\n# Important similar questions:\n# 1. How to find odd numbers in a range?\n# 2. How to generate a list of numbers with a specific step?\n# 3. How to filter a list of numbers based on a condition in Python?\n# 4. How to find multiples of a given number within a range?\n# 5. How to implement loops and conditional statements in Python for number sequences?\n# 6. How to write functions to perform mathematical operations on ranges of numbers?\n# 7. How to work with large lists and optimize memory usage in Python?\n# 8. How to use list comprehensions for concise list generation?\n# 9. How to find prime numbers in a range (related to the original code\'s context)?\n# 10. How to perform basic arithmetic operations in Python?\n```'
        match = re.search(r"```(?:\w+)?\n(.*?)```", final_code, re.DOTALL)
        if match:
            final_code = match.group(1)
        
        res_msg = response_msg(input)
        if exception_found and main_code == exception_code:
            with open(exception_file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            return org_code,res_msg
        elif exception_found and exception_same:
            with open(exception_file_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            return final_code,res_msg
        else:
            return final_code, res_msg
    
    except Exception as e:
        print(f"[ERROR] Failed to send message to Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None, f"ERROR: {str(e)}"

# filepaths=[r"C:\Users\Kishore.k\Documents\automation_code.py",
# r"C:\Users\Kishore.k\Downloads\pdf_highlighter.py",
# r"C:\Users\Kishore.k\Downloads\claims_sample.xlsx"]
# file_path = "code_py/execute_code.py"
# with open(file_path, "r", encoding="utf-8") as f:
#     code = f.read()
# exception_info="Traceback (most recent call last):\n  File \"d:\\Droidal\\ABA\\oct\\17-10\\aba\\backup.py\", line 119, in aba_agent\n    from proj_93.task_178 import orders_in_dropdown\n  File \"d:\\Droidal\\ABA\\oct\\17-10\\aba\\proj_93\\task_178\\orders_in_dropdown.py\", line 12\n    element_xpath_to_use = \"//div[@id='searchOrderList']/div[@class='panel filter_panel']/div[@class='panel-body p-lg']/div[@class='filters d-flex flex-row-wrap flex-as flex-jsb flex-gap-lg']/div[@id='order_type_container']/div[@class='filter_container']/div[@id='order_type_filter']/span[@class='k-widget k-dropdown k-header full_width form-control k-dropdown-clearable']/span[@class='k-dropdown-wrap k-state-default']/input[@role='listbox'] # Use the provided current element's XPath\n                           ^\nSyntaxError: unterminated string literal (detected at line 12)\n"
# input=f"I got this error need to fix it : {exception_info}"
# response=chat_request(code,input,[])
# with open("backup.py", "w", encoding="utf-8") as f:
#     f.write(response[0])
