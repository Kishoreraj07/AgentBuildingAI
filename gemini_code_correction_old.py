import google.generativeai as genai
import config
from selenium.webdriver.support.ui import WebDriverWait
# import screenshot_xpath
import google.generativeai as genai
from selenium.webdriver.common.by import By 
import json
def table_dropdown_find(input):
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    prompt = f"""This is the user's action description: {input}

    Your task:
    Classify the description based on its intent and return the result **only** as a JSON object — no extra text or explanation.

    Classification rules:

    1. If the description indicates selecting, choosing, or picking an option from a dropdown, menu, or list,
    return:
    {{"result": "dropdown_selection"}}

    2. If the description refers to extracting, reading, or retrieving a data table, grid, or tabular content from the page,
    return:
    {{"result": "table_extraction"}}

    3. If the description only mentions clicking or opening a dropdown/menu without selecting or choosing any option,
    return:
    {{}}

    4. If the description involves navigating to or clicking on a **tab**, **sidebar item**, or **taskbar item**, 
    since it is not related to dropdown selection,
    return:
    {{}}

    5. If the description involves clicking or opening a dropdown and then typing specific text (without selecting or choosing any option),
    since it is not about selecting options,
    return:
    {{}}

    6. For all other unrelated actions (typing, clicking buttons, extracting text, etc.),
    return:
    {{}}

    Output rule:
    - Respond **only** with the JSON object, with no explanation, commentary, or formatting.
    """

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
    if len(res)==0:
        if res=='':
            res={}
        return res
    return res

def write_code(file_path,code):
    # file_path='backup.py'
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
def code_correction(desc,xpath,file_path,var_name,driver,userid, listvariable=[]):

    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False

    if type(xpath) == list:
        co_ordinates_status=True
    if isinstance(xpath, str):
        if xpath.lower().endswith(".png"):
            img_status = True
    WebDriverWait(driver, 20).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    html_content = driver.execute_script("return document.documentElement.outerHTML;")
    # with open("page_content.html", "w", encoding="utf-8") as f:
    #     f.write(html_content)
    # xpath=screenshot_xpath.get_xpath(driver,desc,html_content)
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()
    # result=table_dropdown_find(desc)
    # dropdown_selection=False
    # table_extraction=False
    # if len(result)>0:
    #     if result["result"]=="dropdown_selection":
    #         dropdown_selection=True
    #     elif result["result"]=="table_extraction":
    #         table_extraction=True
    if not co_ordinates_status and not img_status:
        element = driver.find_element(By.XPATH, xpath)
        outer_html = element.get_attribute("outerHTML")
    

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run(driver)` that performs the described UI action using `pyautogui` for mouse and keyboard automation. 
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
                3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{var_name}` key.
                5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                7. Include concise inline comments explaining key steps, imports, and assumptions.
                8. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {desc} → will be replaced with the user's action description (used for the logic and inline comments).
            - {var_name} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic according to {desc}):
            def run(driver):
                import pyautogui
                import time
                import json
                import os

                # Silence unused parameter
                _ = driver

                json_path = "json_info/json_xpath.json"

                # Validate JSON file existence
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"JSON file not found: {{json_path}}")

                # Load coordinate data
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                element_name={var_name}

                coordinates_points = json_info.get({{}})
                if not isinstance(coordinates_points, (list, tuple)) or len(coordinates_points) != 2:
                    raise ValueError("Expected coordinate_index as a list of 2 integers for key: " + str({var_name}))

                x_center, y_center = map(int, coordinates_points)

                # Perform the UI action described in {desc}
                time.sleep(1)
                pyautogui.moveTo(x_center, y_center, duration=0.3)
                pyautogui.click()
                time.sleep(0.3)
                # <Continue the logic based on the user's action: {desc}>

            Notes / Constraints:
            - The coordinate order is always [x_axis, y_axis].
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
                ✅ Correct:   x_center, y_center = coordinates
                ❌ Incorrect: left, right, top, bottom = coordinates
            - Here assigning coordinates_points should be like below pattern only
                element_name={var_name}
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get({{element_name}}) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """


    elif img_status and not co_ordinates_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            4. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), generate only click code.
            - If the description implies a typing action (e.g., "type username as www"), generate only typing code — do not include click/extract logic.
            - If the description implies a text extraction action (e.g., "extract OTP from image"), generate only text extraction code — not click/type code.
            5.Do not use the description : {desc} \n Inside the code create prefered logic based on the  by analyzed the description
            5. Use pyautogui.locateOnScreen(image_path, confidence=confidence) for image matching.
            6. Include proper error handling (e.g., image not found).

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for image click action):

            def run(driver=None):
                import json
                import timeelement_name
                import pyautogui
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
                time.sleep(1)
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is None:
                    print("Image not found on screen!")
                    return False
                x, y = pyautogui.center(location)
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                return True
            """

    else:
        prompt = f"""
        Generate a **final Selenium-based Python automation code** for the following user requirement.

        ===============================================================================
        🧠 USER REQUIREMENT
        ===============================================================================
        {desc}

        ===============================================================================
        🔍 PROVIDED ELEMENT INFORMATION
        ===============================================================================
        - XPath of the element (use EXACTLY this, do NOT modify): {xpath}
        - Outer HTML (context only): {outer_html}
        - Full Page HTML (context only): {html_content}
        - Variable name: {var_name}

        ===============================================================================
        🎯 PRIMARY OBJECTIVE
        ===============================================================================
        Generate **runnable Selenium + Python code** that performs both:
        - The provided `driver`
        - The given `xpath`
        - The required browser automation actions.
        - Any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.).
        - Do not create or modify any new XPath.
        - Does NOT create, modify, or alter any XPath.
        - Must load the XPath dynamically from the JSON file using the exact pattern below:

            import json
            json_path = "json_info/json_xpath.json"
            element_name = {var_name}

            with open(json_path, "r") as f:
                xpath_json = json.load(f)

            xpath = xpath_json[element_name]

        Always use the `xpath` variable for locating elements. Never hardcode any XPath.

        ===============================================================================
        🧩 ACTION DETECTION RULES
        ===============================================================================
        Detect the action type from the description:
        - “type”, “enter”, “input” → typing actions
        - “click”, “press”, “submit” → clicking
        - “select”, “choose”, “pick” → dropdown selection
        - “extract”, “read”, “get”, “fetch” → data extraction
        - “vault”, “from vault”, “get from vault” → vault retrieval
        - “save”, “export”, “write”, “store”, “download” → native file operations (Excel, CSV, JSON, text)
        - “screenshot”, “capture screen” → browser screenshot

        ===============================================================================
        🔐 VAULT HANDLING RULES
        ===============================================================================
        If vault retrieval is mentioned (“from vault”, “get from vault”, “retrieve from vault”):
        1. Extract the asset name (the word before “from vault”).
        2. Add these imports:
            import sys, os, requests
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        3. Retrieve from:
            vault_url = f"https://droidal.ai/app/project/asset/{userid}/{{asset_name}}/"
            response = requests.get(vault_url)
            vault_data = response.json()
            vault_keys = list(vault_data.keys())
            var_name = vault_data[vault_keys[6]] if len(vault_keys) >= 7 else ""
        4. Use var_name for typing into the field.
    
    ===============================================================================
    ⚙️ IMPLEMENTATION RULES
    ===============================================================================
    function_arg = {listvariable}
    arg_con = "run(driver,)"
    for list in function_arg:
        arg_con += list + ","
    function_string = arg_con[:-1]+")"
    1. The function name must be exactly {{function_string}}.
    2. Use the xpath on the code by below pattern
        import json
        json_path="json_info/json_xpath.json"
        element_name={var_name}
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xapth=xpath_json[{{element_name}}]

    3. Do NOT hardcode the XPath anywhere in the code.  
        Always use the `xpath` variable loaded from the JSON file.
    4. Dont miss the needed package import :
    import json #must
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    5. Dropdown handling rules:
    - If element contains `<select>`, use `Select(element).select_by_visible_text(...)`.
    - If element is a custom async-ui-select or div-based dropdown:
            1. Click on the dropdown trigger element.
            2. Wait for the options container to appear (`ul.ui-select-choices` or `.ui-select-choices-row`).
            3. Find the correct option by its visible text (e.g., "Declined") and click it.
            4. Example structure to follow:
                ```python
                element = driver.find_element(By.XPATH, xpath)
                element.click()
                wait = WebDriverWait(driver, 10)
                option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'ui-select-choices-row')]//span[normalize-space()='Declined']")))
                option.click()
                ```
    - Ensure to match the nested `<span>` text for options, not just `<div>`.

    6. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

        ===============================================================================
        📊 TABLE / DIV-CONTAINER EXTRACTION RULES (✅ FIXED)
        ===============================================================================
        When the user requirement mentions:
        - "extract table", "get table data", "read table", "fetch table contents"
        - "extract grid", "extract div table", "extract container", or "get div data"

        You must:
        1. Locate the table or div container using the provided XPath.
        2. Wait for it to be visible using WebDriverWait.
        3. Detect whether it is a traditional <table> element or a <div>-based grid.
        4. Extract all visible rows and cells (or nested divs) into a structured list.
        5. ✅ Normalize column counts to prevent pandas or Excel export errors.

        🔹 For <table> elements:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        rows = element.find_elements(By.XPATH, ".//tr")
        table_data = []
        for row in rows:
            cols = row.find_elements(By.XPATH, ".//th|.//td")
            row_data = [col.text.strip() for col in cols]  # Keep blanks for alignment
            table_data.append(row_data)
        # Normalize column counts
        max_cols = max(len(r) for r in table_data) if table_data else 0
        for r in table_data:
            while len(r) < max_cols:
                r.append("")

        print(table_data)

        ===============================================================================
        💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION FIXED)
        ===============================================================================
        Dynamically detect both file path and format based on the user description.

        🧩 Step 1: Path Detection
        - If the description includes any of these patterns:
            “in this path”, “to path”, “save at”, “save in”, “write it in”
        - Extract the full file path.
        - If none found, default to “output.xlsx”.

        🧩 Step 2: File Type Detection
        - Detect from both description and path:
            if "excel" in desc.lower() or "xlsx" in desc.lower() or output_path.endswith(".xlsx"):
                → Excel (.xlsx) via openpyxl
            elif "csv" in desc.lower() or output_path.endswith(".csv"):
                → CSV (.csv) via csv
            elif "json" in desc.lower() or output_path.endswith(".json"):
                → JSON (.json) via json
            else:
                → Default Excel (.xlsx)

        🧩 Step 3: Example Export Implementations

        Excel export:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            for row in table_data:
                ws.append(row)
            wb.save(output_path)

        CSV export:
            import csv
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(table_data)

        JSON export:
            import json
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=4)

        Screenshot:
            driver.save_screenshot(output_path if provided else "screenshot.png")

        ===============================================================================
        ✅ OUTPUT FORMAT (MANDATORY)
        ===============================================================================
        Output must exactly follow this format:

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

    def run(driver,{{function_string}}):
        import json
        json_path="json_info/json_xpath.json"
        element_name="{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xapth=xpath_json[{{element_name}}]
        # Generated logic here
    
    ===============================================================================
    NOTE: (MANDATORY)
    ===============================================================================
    - All import statements must be placed inside the `aba_agent()` function block.
    - The import statement `import json` is mandatory and must always be included.
    ===============================================================================
    💬 EXAMPLES
    ===============================================================================
    - "select Declined from Bill Status dropdown"
    - "choose Completed from Status menu"
    - "type username from vault in username field"
    - "extract table and save to Excel"
    - "fetch table and export to CSV"
    - "click on Submit button"
    - "capture screenshot of current page"
    - "read div container and export as JSON"
    ===============================================================================

    ================================================================================
    RULES
    ================================================================================
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
    write_code(file_path,code_to_write)
    return code_to_write


