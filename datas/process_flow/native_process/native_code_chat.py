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
    modified_prompt= f"""
Here is the User Query: {input}

User request is related to modifying the existing code based on their query.

Here is the existing code: {code}

If the query references any files, the attached files and their full paths are: {filepaths}

Based on the User Query, update or modify the code as needed and return it as Python code.

=============================
MODIFICATION RULES:
=============================
1. If the User Query doesn't require any code changes, return the existing code as-is without any modifications.

2. Do NOT change the existing function name (e.g., aba_agent()).

3. Do NOT call the function; only define it.

4. Maintain the existing try-except-finally structure.

5. When adding new steps, follow the existing comment pattern:
   #Step N: <action description>

6. No additional explanations or text - just provide the code.

=============================
SPECIAL FUNCTION ADDITIONS:
=============================
If the User Query requests adding these specific functionalities, use the corresponding pre-built functions:

A. MESSAGE BOX / POPUP:
   Add this import at the top of try block:
   from datas.supporting_files.message_box import popup_message_box
   
   Add this code where needed:
   popup_message_box(<message_to_display>)

B. EXCEL FILE READING:
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

C. PDF SPLITTING:
   Add this import at the top of try block:
   from datas.supporting_files.pdf_splitter import split_pdf
   
   Add this code where needed:
   pdf_file_path = <pdf_file_full_path>
   page_limit = <pages_per_split_as_integer>
   destination_folder = <destination_folder_path_or_source_folder_if_not_specified>
   pdf_split(pdf_file_path, page_limit, destination_folder)

D. PDF TEXT HIGHLIGHTING:
   Add this import at the top of try block:
   from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
   
   Add this code where needed:
   pdf_path = <pdf_file_full_path>
   text = <text_to_highlight>
   output_path = <output_path_or_same_pdf_path_if_not_specified>
   highlight_text_in_pdf(pdf_path, text, output_path)

E. TIME DELAY / WAIT:
   Add this import at the top of try block:
   from datas.supporting_files.time_delay import time_delay
   
   Add this code where needed:
   time_delay(<seconds_as_integer>)

F. MFA/OTP FROM MOBILE AUTHENTICATOR:
   Add this function definition at the top of try block (after imports):
   import time
   from pyotp import TOTP
   def mfa_token(tokens):
       time.sleep(1)
       totp = TOTP(tokens)
       token = totp.now()
       return token
   
   Use mfa_token(<secret_token>) wherever OTP input is required.

G. Extract Table from PDF:
    Add this import at the top of try block:
    from datas.supporting_files.pdf_xl import pdf_to_table_extract

    Usage:
    description = "Full action description"
    pdf_file = <Full pdf file path>

    Call:
    table_df = pdf_to_table_extract(pdf_file,description)

H. SCREEN SHOT PICK:
    If the user wants to capture a screenshot of the current screen, use the code below.
    
    Import:
    from datas.supporting_files.screenshot_pick import take_screenshot

    Usage:
    image_path = <full image path as per the user's requirement>
    If no path is provided by the user, use the default path: "temp_img.png"

    Call:
    take_screenshot(image_path)

=============================
MODIFICATION GUIDELINES:
=============================
1. Add imports at the appropriate location in the try block (with other imports)

2. Add new code at the logical position based on the User Query

3. If User Query asks to modify existing steps, update those specific steps only

4. If User Query asks to add new steps, append them with appropriate step numbers

5. For operations NOT in the special functions list (file copy, move, rename, delete, etc.), 
   write the logic directly using standard Python libraries (os, shutil, etc.)

6. Maintain proper indentation and syntax

7. Keep the existing error handling structure intact

=============================
IMPORTANT:
=============================
- Only modify code if the User Query explicitly requires changes
- If no changes are needed, return the exact existing code
- Do NOT assume or create functions that don't exist
- Use pre-built functions ONLY for their specific operations when requested
- All other operations must use direct Python implementation

Return only the valid, correctly indented Python code.
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
