import google.generativeai as genai
import config
import json
def gemini_response(input):
    """Generate desktop automation code using pywinauto for a given input (exe path)."""
    # if isinstance(input, list):
    #     input = "\n".join(input)

    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()

    prompt =f"""
Here is the user requirement: {input}

The above requirement describes a Native Application Automation flow as a list of steps.
Generate the corresponding Python code for it.

Process each step in the list sequentially and generate code accordingly.

Do not include any additional explanations or text.  
Ensure the final returned code is syntactically correct and properly indented.

=============================
CODE GENERATION RULES:
=============================
1. The entire code must be wrapped inside a single function named aba_agent().
   - Do not include any function calls or code outside this function.

2. The entire code inside aba_agent() must be wrapped within a try-except block.

3. The except block must follow this exact structure:
       os.makedirs("json_info", exist_ok=True)
       with open("json_info/exception_info.json", "w") as f:
           json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)

4. Ensure there are absolutely no:
   - Indentation errors
   - Syntax errors
   - Additional output text

5. For each step in the user requirement list, add a comment tag:
   #Step 1: <exact action description from requirement>
   #Step 2: <exact action description from requirement>
   #Step 3: <exact action description from requirement>
   
   Use ONLY these step comment tags. No other explanatory comments or tags should be included.

=============================
SPECIAL FUNCTION USAGE RULES:
=============================
Use the following pre-built functions ONLY when the user explicitly requests these specific actions.
For all other operations, build the logic directly without assuming functions exist.

A. MESSAGE BOX / POPUP:
   If user wants to display a message box or popup:
   
   from datas.supporting_files.message_box import popup_message_box
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
   If user wants to split a PDF file:
   
   from datas.supporting_files.pdf_splitter import split_pdf
   pdf_file_path = <pdf_file_full_path>
   page_limit = <pages_per_split_as_integer>
   destination_folder = <destination_folder_path_or_source_folder_if_not_specified>
   pdf_split(pdf_file_path, page_limit, destination_folder)

D. PDF TEXT HIGHLIGHTING:
   If user wants to highlight text in a PDF:
   
   from datas.supporting_files.pdf_highlighter import highlight_text_in_pdf
   pdf_path = <pdf_file_full_path>
   text = <text_to_highlight>
   output_path = <output_path_or_same_pdf_path_if_not_specified>
   highlight_text_in_pdf(pdf_path, text, output_path)

E. TIME DELAY / WAIT:
   If user wants to wait or add delay:
   
   from datas.supporting_files.time_delay import time_delay
   time_delay(<seconds_as_integer>)

G. Extract Table from PDF:
   If the User wants to extract the table from given pdf file by passing path
   
   from datas.supporting_files.pdf_xl import pdf_to_table_extract
   description = "Full action description"
   pdf_file = <Full pdf file path>
   table_df = pdf_to_table_extract(pdf_file,description)

H. SCREENSHOT PICK:
   If the user wants to capture a screenshot of the current screen, use the code below.

   from datas.supporting_files.screenshot_pick import take_screenshot
   image_path = <full image path as per the user's requirement>
   take_screenshot(image_path)

   Rules:
   - If no path is provided by the user, use the default path: "temp_img.png"

=============================
IMPORTANT:
=============================
- ONLY use the above pre-built functions for their specific operations when explicitly requested
- For ALL other operations (file rename, copy, move, delete, navigate folders, etc.), write the logic directly using standard Python libraries
- Do NOT assume or create import statements for functions that don't exist
- Build direct implementation for any operation not listed above
- Each step from the user requirement list must have a corresponding #Step N: <action> comment tag

Only return the valid, correctly indented Python code that meets the above rules.
"""

    try:
        response = chat.send_message(prompt)
        code_to_write = response.text.strip("` \n python")  # Minor: Trim more variants
    except Exception as e:
        raise ValueError(f"Gemini API error: {e}")
    return code_to_write
