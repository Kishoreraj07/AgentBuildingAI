import google.generativeai as genai
from datas.source_files import config
import importlib,json,os
def main(outer_html,var_name):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    function_name = f"dt_extract()"
    prompt = f"""Here is the Outer HTML content of a table-like field: {outer_html}

    Your task:
    Generate complete Python code that extracts data dynamically from the webpage DOM using Selenium WebDriver (not by parsing HTML content or reading from files).
    The function should locate all rows (divs or containers) representing orders and extract key fields such as:
    - Order ID, Order Type, Order Status
    - Priority, Reason
    - Patient Name, Address
    - Contact Name, Contact Phone
    - Branch, Warehouse
    - Ordered Date, Requested Date

    The function must automatically expand any collapsed rows (for example, clicking 'expand' buttons) before extracting details.
    It should safely handle missing elements and continue extracting the rest without raising exceptions.

    RULES:
    - The entire code must be contained within a single function named: {function_name}
    - The function should accept only one argument: driver (an instance of Selenium WebDriver)
    - Use Selenium methods like find_element, find_elements, and execute_script for expansion
    - Implement a helper method (safe_find) inside the function to safely extract text
    - Use time.sleep or WebDriverWait after expanding sections to allow elements to load
    - Return a list of dictionaries named data_table
    - Do not include any print statements, comments, or function calls outside the function
    - Only output the full, runnable Python code — no explanations
    """



    response = chat.send_message(prompt)
    code_to_write=response.text
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()
    return code_to_write

def get_dt(outer_html,var_name,driver):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]
    code_write=main(outer_html,var_name)
    file_name=f"{var_name}_table_dt"
    file_path=f"{proj_fol}/{task_fol}/{file_name}.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code_write)
    # module_path = f"{proj_fol}.{task_fol}.{file_name}"
    # module = importlib.import_module(module_path)
    # dt = getattr(module, function_name)()
    # return dt

