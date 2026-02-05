import google.generativeai as genai
from datas.source_files import config
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

def code_correction(desc,xpath,file_path,var_name,driver,userid, add_info,type_input,listvariable=[]):
    if type_input==None:
        type_input=""
    dynamic_status=False
    if add_info["xpath_variables"] !="":
        dynamic_xpath_variables=add_info["xpath_variables"]
        dynamic_status=True
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
    if not co_ordinates_status and not img_status and not region_status:
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
    
    
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
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


    elif img_status and not co_ordinates_status and not region_status:
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
    elif region_status and not co_ordinates_status and not img_status:
        prompt=f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            bound_index = json_info[{var_name}]
            4. Extract coordinates from bound_index as [left, top, right, bottom] format.
            5. ALWAYS take a LIVE screenshot of the specified region from the current screen using pyautogui.screenshot().
            6. CRITICAL: Save the captured region screenshot temporarily and use pyautogui.locateOnScreen() to find the exact location of the captured image on screen.
            7. NEVER directly use calculated coordinates (center_x, center_y) for clicking. ALWAYS locate the image on screen first.
            8. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), capture the region, locate it on screen using the captured image, then click.
            - If the description implies a typing action (e.g., "type username as www"), locate the region image on screen, click it, then type text.
            - If the description implies a text/table extraction action (e.g., "extract OTP", "extract table data"), capture the region live and use OCR to extract text.
            - If the description mentions scrolling (e.g., "scroll down", "scroll in table"), locate the region image and scroll within it.
            - If the description mentions hover (e.g., "hover over element"), locate the region image and move mouse to its center.
            - If the description mentions double-click, locate the region image and perform double-click.
            - If the description mentions right-click, locate the region image and perform right-click.
            - If the description mentions drag (e.g., "drag element"), locate the region image and perform drag operation.
            9. Do not use the description: {desc} directly in the code. Create preferred logic by analyzing the description.
            10. For all click-based actions, the workflow must be: Capture region → Save as temp image → Locate image on screen → Click the located position.
            11. For typing actions, extract the text to be typed from the description (e.g., "type username as admin" → type "admin").
            12. For extraction actions, return the extracted text as the function output.
            13. Include proper error handling (e.g., invalid coordinates, screenshot failure, image not found on screen, OCR failure).
            14. Add appropriate time.sleep() delays between actions for stability.
            15. Use confidence parameter (0.8 or 0.9) for image matching to handle minor variations.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for region click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for text/table extraction action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    extracted_text = pytesseract.image_to_string(region_screenshot).strip()
                    print(f"Extracted text: {{extracted_text}}")
                    return extracted_text if extracted_text else ""
                except Exception as e:
                    print(f"Error: {{e}}")
                    return ""

            Example reference (for typing action with text extraction from description):

            def run(driver=None):
                import json
                import time
                import pyautogui
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    time.sleep(0.3)
                    
                    pyautogui.typewrite("text_here", interval=0.1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for double-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.doubleClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for scroll action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.scroll(-3)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for hover action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for right-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.rightClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False
            """
    else:
        if dynamic_status:
            prompt=f"""
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
- Type Input Data: {type_input}

===============================================================================
🎯 PRIMARY OBJECTIVE
===============================================================================
Generate **runnable Selenium + Python code** that performs:
- EXACTLY what the user requirement describes - NO MORE, NO LESS
- ALL actions mentioned in the user requirement MUST be implemented
- NO actions should be commented out or made optional
- Use the provided `driver` and `xpath`
- Required browser automation actions
- Any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)

**CRITICAL RULES:**
1. If user says "type and press Enter" → Implement BOTH typing AND Enter key press
2. If user says "click and type" → Implement BOTH click AND type
3. If user says "type password and submit" → Implement BOTH type AND click submit
4. NEVER decide which actions to include/exclude - implement ALL mentioned actions
5. NEVER comment out any action mentioned in the requirement
6. NEVER add optional code with comments like "uncomment if needed"
7. Does NOT create, modify, or alter any XPath
8. Must load the XPath and dynamic variables from JSON files using the exact pattern below:

    import json
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)

Always use the `xpath` variable for locating elements. Never hardcode any XPath or dynamic variables.

===============================================================================
🧩 ACTION DETECTION RULES
===============================================================================
Detect ALL actions from the description and implement ALL of them:

1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
   - Standard click for buttons, links, any clickable element
   - Wait for element to be clickable (30 sec max)

2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
   - For text input fields
   - Wait for element to be visible (30 sec max)
   - **CRITICAL: Use the type_input parameter passed to the function**
   - **NEVER hardcode the typing value in the function body**
   - **The type_input parameter contains the exact data to type**
   - Example implementations:
     ```python
     # ✓ CORRECT - Using the type_input parameter
     def run(driver, type_input):
         element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
         element.clear()
         element.send_keys(type_input)
     
     # ❌ WRONG - Hardcoding or using placeholder text
     element.send_keys("enter your username")  # DON'T DO THIS
     element.send_keys("type password here")   # DON'T DO THIS
     type_input = "hardcoded_value"           # DON'T DO THIS
     ```

3. **KEYBOARD ACTION**: "press Enter", "press Tab", "hit Enter", "press key"
   - **MUST be implemented if mentioned in user requirement**
   - After typing, if "press Enter" or "press Tab" is mentioned, add:
     ```python
     from selenium.webdriver.common.keys import Keys
     element.send_keys(Keys.ENTER)  # or Keys.TAB
     ```
   - **NEVER comment out keyboard actions**
   - **NEVER make keyboard actions optional**

4. **COMBINED ACTIONS** - Implement ALL mentioned actions in sequence:
   - "type username and press Enter" → type + Keys.ENTER
   - "enter password and submit" → type + click submit button
   - "click field and type text" → click + type
   - "type and tab to next field" → type + Keys.TAB
   - **ALL actions MUST be implemented, NONE should be commented**

5. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
   - Scroll into view and hover
   - Wait for element to be present (30 sec max)

6. **ELEMENT WAIT**: "wait for element", "check element", "element exists", "verify element"
   - Check element presence only
   - Return True/False status
   - Do not perform click or type action

7. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
   - **Analyze Outer HTML first**:
       - If contains `<select>` → Use Select class
       - If custom dropdown (ui-select, div-based) → Click + wait + click option
   - Extract option text from description (e.g., "select Declined" → "Declined")

8. **SCROLL ACTION**: "scroll to", "scroll into view"
   - Scroll element into view
   - "scroll to and click", "scroll and click" → Use SCROLL + CLICK COMBINED ACTION pattern
   - Wait for element presence

9. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
   - Wait for element visibility
   - Return element text or value attribute

10. **CLEAR FIELD**: "clear", "empty", "delete content"
    - Wait for element visibility
    - Clear the input field

11. **Other Actions**
    - "vault", "from vault", "get from vault" → vault retrieval
    - "save", "export", "write", "store", "download" → native file operations (Excel, CSV, JSON, text)
    - "screenshot", "capture screen" → browser screenshot

===============================================================================
🔐 VAULT HANDLING RULES
===============================================================================
If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
1. Extract the asset name (the word before "from vault").
2. Add these imports:
    import sys, os, requests
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
3. Retrieve from:
    vault_url = f"https://droidal.ai/app/project/asset/{{userid}}/{{asset_name}}/"
    response = requests.get(vault_url)
    vault_data = response.json()
    vault_keys = list(vault_data.keys())
    retrieved_value = vault_data[vault_keys[6]] if len(vault_keys) >= 7 else ""
4. Use retrieved_value for typing into the field.

**IMPORTANT**: The type_input parameter should contain the vault-retrieved value when calling the function.

===============================================================================
⚙️ IMPLEMENTATION RULES
===============================================================================
function_arg = {listvariable}
arg_con = "run(driver"
for list in function_arg:
    arg_con += ", " + list
# Add type_input parameter for TYPE actions
if action_is_type:
    arg_con += ", type_input"
arg_con += ")"
function_string = arg_con

1. **Function Signature Rules**:
   - For TYPE actions: def run(driver, type_input):
   - For NON-TYPE actions: def run(driver):
   - Additional parameters from {listvariable} should be added as needed

2. Use the xpath on the code by below pattern:
    import json
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)

3. Do NOT hardcode the XPath or dynamic variables anywhere in the code.  
    Always use the `xpath` variable loaded from the JSON file with values from dynamic_xpath.json.

4. Don't miss the needed package import:
import json #must
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# Add Keys import if keyboard action is needed
from selenium.webdriver.common.keys import Keys

5. **Type Functionality (CRITICAL):**
    - **For TYPE actions, the function MUST accept type_input as a parameter**
    - **Function signature: def run(driver, type_input):**
    - **ALWAYS use the type_input parameter directly - DO NOT reassign or hardcode it**
    - **NEVER create a new variable type_input = "some_value" inside the function**
    
    Example:
    ```python
    # ✓ CORRECT - Using parameter
    def run(driver, type_input):
        import json
        from selenium.webdriver.common.keys import Keys
        
        # Load XPath from JSON
        json_path = "json_info/json_xpath.json"
        element_name = "{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        
        # Load dynamic variables from JSON
        dynamic_var_path = "json_info/dynamic_xpath.json"
        with open(dynamic_var_path, "r") as f:
            dynamic_info = json.load(f)
        values = dynamic_info["data"]
        
        # Format XPath with dynamic values
        xpath = xpath_json[element_name].format(*values)
        
        element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        element.clear()
        element.send_keys(type_input)  # Use the parameter directly
        
        # If user says "press Enter", implement it - DON'T comment it out
        element.send_keys(Keys.ENTER)
    
    # ❌ WRONG - Hardcoding inside function
    def run(driver, type_input):
        type_input = "hardcoded_value"  # DON'T DO THIS
        element.send_keys(type_input)
    
    # ❌ WRONG - Not accepting parameter
    def run(driver):
        type_input = "{type_input}"  # DON'T DO THIS
        element.send_keys(type_input)
    
    # ❌ WRONG - Commenting out user-requested actions
    def run(driver, type_input):
        element.send_keys(type_input)
        # element.send_keys(Keys.ENTER)  # DON'T comment out if user asked for it
    ```

6. **SCROLL + CLICK COMBINED ACTION**: "scroll to and click", "scroll and click", "scroll to element and click", "bring into view and click"
   - **This is a COMBINED action requiring both scroll and click**
   - Must perform in sequence: scroll → wait → click
   - Use the pattern below:

**Implementation Pattern:**
```python
def run(driver):
    import json
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)
    
    # Wait for element presence
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    
    # Scroll element into view
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    
    # Wait for scroll to complete
    time.sleep(0.5)
    
    # Wait for element to be clickable and click
    clickable_element = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    clickable_element.click()
```

**Key Points for Scroll + Click:**
- Always use smooth scrolling with center alignment
- Add 0.5s delay after scroll for stability
- Re-verify element is clickable after scroll
- Use xpath variable from JSON (never hardcode)
- Import time module for sleep

7. Dropdown handling rules:
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

8. **CRITICAL**: Output must be valid runnable Python code ONLY - no explanations, no markdown, no comments about optional features

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
    "in this path", "to path", "save at", "save in", "write it in"
- Extract the full file path.
- If none found, default to "output.xlsx".

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

**For TYPE actions:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver, type_input):
    import json
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)
    
    # Use type_input parameter directly - DO NOT reassign
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
```

**For TYPE + KEYBOARD actions (e.g., "type and press Enter"):**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver, type_input):
    import json
    from selenium.webdriver.common.keys import Keys
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)
    
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    # Implement keyboard action as user requested - NO commenting out
    element.send_keys(Keys.ENTER)
```

**For NON-TYPE actions:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver):
    import json
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)
    
    # ... rest of the logic
```

===============================================================================
NOTE: (MANDATORY)
===============================================================================
- All import statements must be placed inside the `run()` function block.
- The import statement `import json` is mandatory and must always be included.
- The xpath formatting with dynamic variables must always follow the pattern:
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values
    xpath = xpath_json[element_name].format(*values)
- This pattern is NON-NEGOTIABLE and must be present in every generated code.
- Dynamic variables must ALWAYS be loaded from the JSON file, NEVER hardcoded.
- **For TYPE actions**: 
  * Function signature MUST be: def run(driver, type_input):
  * ALWAYS use the type_input parameter directly
  * NEVER reassign type_input inside the function
  * NEVER hardcode typing values
- **For NON-TYPE actions**: Function signature is: def run(driver):
- **For COMBINED actions**: Implement ALL actions mentioned by the user
  * If user says "type and press Enter" → Implement typing + Keys.ENTER
  * If user says "click and type" → Implement click + typing
  * NEVER comment out any action mentioned in the requirement
  * NEVER make actions optional with comments

===============================================================================
💬 EXAMPLES
===============================================================================
- "select Declined from Bill Status dropdown" → def run(driver):
- "choose Completed from Status menu" → def run(driver):
- "type username from vault in username field" → def run(driver, type_input):
- "extract table and save to Excel" → def run(driver):
- "fetch table and export to CSV" → def run(driver):
- "click on Submit button" → def run(driver):
- "capture screenshot of current page" → def run(driver):
- "read div container and export as JSON" → def run(driver):
- "type password as welcome#2025" → def run(driver, type_input): # type_input="welcome#2025"
- "enter admin in username field" → def run(driver, type_input): # type_input="admin"
- "type username and press Enter" → def run(driver, type_input): # type + Keys.ENTER
- "enter password and hit Tab" → def run(driver, type_input): # type + Keys.TAB
- "click search box and type query" → def run(driver, type_input): # click + type
- "type email and submit" → def run(driver, type_input): # type + click or type + Keys.ENTER

===============================================================================
🔴 CRITICAL TYPE ACTION RULES (READ CAREFULLY)
===============================================================================
When generating code for TYPE actions:

1. **Function Signature**: MUST be def run(driver, type_input):

2. **Parameter Usage**:
   ✓ Use type_input parameter directly
   ✓ element.send_keys(type_input)
   
3. **What NOT to do**:
   ❌ type_input = "hardcoded_value"  # Never reassign
   ❌ type_input = "{type_input}"     # Never use f-string value
   ❌ element.send_keys("enter text") # Never use literals
   ❌ def run(driver):                # Never omit parameter
   
4. **What TO do**:
   ✓ def run(driver, type_input):    # Correct signature
   ✓ element.send_keys(type_input)   # Use parameter directly
   
5. **Combined Actions Implementation**:
   ```python
   # Example: "type username and press Enter"
   def run(driver, type_input):
       import json
       from selenium.webdriver.common.keys import Keys
       
       # Load XPath from JSON
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       
       # Load dynamic variables from JSON
       dynamic_var_path = "json_info/dynamic_xpath.json"
       with open(dynamic_var_path, "r") as f:
           dynamic_info = json.load(f)
       values = dynamic_info["data"]
       
       # Format XPath with dynamic values
       xpath = xpath_json[element_name].format(*values)
       
       element = WebDriverWait(driver, 30).until(
           EC.visibility_of_element_located((By.XPATH, xpath))
       )
       element.clear()
       element.send_keys(type_input)      # Type action
       element.send_keys(Keys.ENTER)      # Press Enter - NOT commented out
   ```

6. **Calling Convention**:
   The function will be called externally with the actual value:
   - run(driver, "admin")
   - run(driver, "welcome#2025")
   - run(driver, vault_retrieved_value)

===============================================================================
🚫 PROHIBITED PATTERNS - NEVER DO THESE
===============================================================================
❌ **NEVER comment out user-requested actions:**
```python
# WRONG - Don't do this
def run(driver, type_input):
    element.send_keys(type_input)
    # element.send_keys(Keys.ENTER)  # Uncomment if you need to press Enter
```

❌ **NEVER make actions optional:**
```python
# WRONG - Don't do this
def run(driver, type_input):
    element.send_keys(type_input)
    # Optionally press Enter:
    # element.send_keys(Keys.ENTER)
```

❌ **NEVER add explanatory comments about what the user might want:**
```python
# WRONG - Don't do this
def run(driver, type_input):
    element.send_keys(type_input)
    # If you want to submit the form, uncomment below:
    # element.send_keys(Keys.ENTER)
```

✅ **ALWAYS implement what user requested:**
```python
# CORRECT - Do this
def run(driver, type_input):
    import json
    from selenium.webdriver.common.keys import Keys
    # ... load xpath ...
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.ENTER)  # User asked for it, so implement it
```

===============================================================================
🎯 IMPLEMENTATION CHECKLIST
===============================================================================
Before generating code, verify:
1. ✓ Read ALL actions mentioned in user requirement
2. ✓ Identify if it's a single action or combined actions
3. ✓ Plan to implement ALL mentioned actions
4. ✓ NO actions will be commented out
5. ✓ NO actions will be marked as optional
6. ✓ Correct function signature (with/without type_input)
7. ✓ All necessary imports included (Keys if keyboard action needed)
8. ✓ XPath loaded from JSON with dynamic variables
9. ✓ Code is executable without any modifications

**Remember: The code will be written directly to a .py file and executed. It must work as-is with ALL requested actions implemented.**

================================================================================
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
- Type Input Data: {type_input}

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
    element_name = "{var_name}"

    with open(json_path, "r") as f:
        xpath_json = json.load(f)

    xpath = xpath_json[element_name]

Always use the `xpath` variable for locating elements. Never hardcode any XPath.

===============================================================================
🧩 ACTION DETECTION RULES
===============================================================================
**CRITICAL: Execute ALL actions mentioned in the user requirement. Do NOT skip, comment out, or make optional any action explicitly requested by the user.**

Detect the action type from the description:
1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
- Standard click for buttons, links, any clickable element
- Wait for element to be clickable (30 sec max)

2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
- For text input fields
- Wait for element to be visible (30 sec max)
- **CRITICAL: Use the type_input parameter passed to the function**
- **NEVER hardcode the typing value in the function body**
- **The type_input parameter contains the exact data to type**
- Example implementations:
```python
  # ✓ CORRECT - Using the type_input parameter
  def run(driver, type_input):
      element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
      element.clear()
      element.send_keys(type_input)
  
  # ❌ WRONG - Hardcoding or using placeholder text
  element.send_keys("enter your username")  # DON'T DO THIS
  element.send_keys("type password here")   # DON'T DO THIS
  type_input = "hardcoded_value"           # DON'T DO THIS
```

3. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
- Scroll into view and hover
- Wait for element to be present (30 sec max)

4. **ELEMENT WAIT**: "wait for element", "check element", "element exists", "verify element"
- Check element presence only
- Return True/False status

5. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
- **Analyze Outer HTML first**:
    - If contains `<select>` → Use Select class
    - If custom dropdown (ui-select, div-based) → Click + wait + click option
- Extract option text from description (e.g., "select Declined" → "Declined")

6. **SCROLL ACTION**: "scroll to", "scroll into view"
- Scroll element into view
- Wait for element presence

7. **SCROLL + CLICK COMBINED ACTION**: "scroll to and click", "scroll and click", "scroll to element and click", "bring into view and click"
- **This is a COMBINED action requiring both scroll and click**
- Must perform in sequence: scroll → wait → click
- Use the pattern below:

**Implementation Pattern:**
```python
def run(driver):
    import json
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    xpath = xpath_json[element_name]
    
    # Wait for element presence
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    
    # Scroll element into view
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    
    # Wait for scroll to complete
    time.sleep(0.5)
    
    # Wait for element to be clickable and click
    clickable_element = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    clickable_element.click()
```

**Key Points for Scroll + Click:**
- Always use smooth scrolling with center alignment
- Add 0.5s delay after scroll for stability
- Re-verify element is clickable after scroll
- Use xpath variable from JSON (never hardcode)
- Import time module for sleep

8. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
- Wait for element visibility
- Return element text or value attribute

9. **CLEAR FIELD**: "clear", "empty", "delete content"
- Wait for element visibility
- Clear the input field

10. **PRESS ENTER/RETURN KEY**: "press enter", "hit enter", "press return", "hit return key", "submit with enter"
- Use Keys.ENTER or Keys.RETURN
- Import required: from selenium.webdriver.common.keys import Keys
- Implementation: element.send_keys(Keys.ENTER)

11. **COMBINED TYPE + ENTER ACTION**: When user mentions BOTH typing AND pressing enter:
- Examples: "type username and press enter", "enter password and hit return", "fill field and submit with enter"
- **ALWAYS implement BOTH actions in sequence**
- **NEVER comment out or make the enter key press optional**
- Pattern:
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.ENTER)
```

12. **COMBINED CLICK + TYPE ACTION**: When user mentions BOTH clicking AND typing:
- Examples: "click on field and type username", "click element and enter text"
- **ALWAYS implement BOTH actions in sequence**
- Pattern:
```python
def run(driver, type_input):
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # First click
    element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
    
    # Then type
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
```

13. **Other Actions**
- "vault", "from vault", "get from vault" → vault retrieval
- "save", "export", "write", "store", "download" → native file operations (Excel, CSV, JSON, text)
- "screenshot", "capture screen" → browser screenshot

===============================================================================
🚨 MULTI-ACTION RULES (CRITICAL)
===============================================================================
**MANDATORY: When the user requirement mentions multiple actions, ALL actions MUST be implemented.**

Examples of multi-action requirements:
- "type username and press enter" → Implement typing + enter key
- "click on search box and type query" → Implement click + type
- "enter password and hit return" → Implement typing + enter key
- "fill field and submit" → Implement typing + submission
- "scroll to element and click" → Implement scroll + click

**RULES:**
1. **NEVER comment out** any action mentioned by the user
2. **NEVER make any action optional** with comments like "uncomment if needed"
3. **ALWAYS execute all actions** in the sequence mentioned
4. **DO NOT add explanatory comments** suggesting the user might want to modify the code
5. The generated code must be **immediately runnable** without any modifications

**Correct Implementation Example:**
```python
# User says: "type password and press enter"
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.ENTER)  # ✓ Both actions implemented
```

**WRONG Implementation Example:**
```python
# ❌ NEVER DO THIS
def run(driver, type_input):
    element.send_keys(type_input)
    # element.send_keys(Keys.ENTER)  # Uncomment if you want to press enter
```

===============================================================================
🔐 VAULT HANDLING RULES
===============================================================================
If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
1. Extract the asset name (the word before "from vault").
2. Add these imports:
    import sys, os, requests
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
3. Retrieve from:
    vault_url = f"https://droidal.ai/app/project/asset/{userid}/{{asset_name}}/"
    response = requests.get(vault_url)
    vault_data = response.json()
    vault_keys = list(vault_data.keys())
    retrieved_value = vault_data[vault_keys[6]] if len(vault_keys) >= 7 else ""
4. Use retrieved_value for typing into the field.

**IMPORTANT**: The type_input parameter should contain the vault-retrieved value when calling the function.

===============================================================================
⚙️ IMPLEMENTATION RULES
===============================================================================
function_arg = {listvariable}
arg_con = "run(driver"
for list in function_arg:
    arg_con += ", " + list
# Add type_input parameter for TYPE actions
if action_is_type:
    arg_con += ", type_input"
arg_con += ")"
function_string = arg_con

1. **Function Signature Rules**:
   - For TYPE actions (including type+enter, type+click combinations): def run(driver, type_input):
   - For NON-TYPE actions: def run(driver):
   - Additional parameters from {listvariable} should be added as needed

2. Use the xpath on the code by below pattern:
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]

3. Do NOT hardcode the XPath anywhere in the code.  
    Always use the `xpath` variable loaded from the JSON file.

4. Dont miss the needed package import:
import json #must
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  # Add when enter key is needed

5. **Type Functionality (CRITICAL):**
    - **For TYPE actions, the function MUST accept type_input as a parameter**
    - **Function signature: def run(driver, type_input):**
    - **ALWAYS use the type_input parameter directly - DO NOT reassign or hardcode it**
    - **NEVER create a new variable type_input = "some_value" inside the function**
    
    Example:
```python
    # ✓ CORRECT - Using parameter
    def run(driver, type_input):
        import json
        json_path = "json_info/json_xpath.json"
        element_name = "{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]
        
        element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        element.clear()
        element.send_keys(type_input)  # Use the parameter directly
    
    # ❌ WRONG - Hardcoding inside function
    def run(driver, type_input):
        type_input = "hardcoded_value"  # DON'T DO THIS
        element.send_keys(type_input)
    
    # ❌ WRONG - Not accepting parameter
    def run(driver):
        type_input = "{type_input}"  # DON'T DO THIS
        element.send_keys(type_input)
```

6. Dropdown handling rules:
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

7. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

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

return table_data

===============================================================================
💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION FIXED)
===============================================================================
Dynamically detect both file path and format based on the user description.

🧩 Step 1: Path Detection
- If the description includes any of these patterns:
    "in this path", "to path", "save at", "save in", "write it in"
- Extract the full file path.
- If none found, default to "output.xlsx".

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

**For TYPE actions (including type+enter combinations):**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys  # Include if enter key is needed

def run(driver, type_input):
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Use type_input parameter directly - DO NOT reassign
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    # If enter key is requested, add this line (NO COMMENTS, just execute it):
    element.send_keys(Keys.ENTER)
```

**For NON-TYPE actions:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver):
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # ... rest of the logic
```

===============================================================================
NOTE: (MANDATORY)
===============================================================================
- All import statements must be placed inside the `run()` function block.
- The import statement `import json` is mandatory and must always be included.
- The xpath loading pattern must always follow the exact format shown above.
- **For TYPE actions**: 
  * Function signature MUST be: def run(driver, type_input):
  * ALWAYS use the type_input parameter directly
  * NEVER reassign type_input inside the function
  * NEVER hardcode typing values
- **For NON-TYPE actions**: Function signature is: def run(driver):
- **For MULTI-ACTION requirements**: Implement ALL actions without comments or optional code blocks
===============================================================================
💬 EXAMPLES
===============================================================================
- "select Declined from Bill Status dropdown" → def run(driver):
- "choose Completed from Status menu" → def run(driver):
- "type username from vault in username field" → def run(driver, type_input):
- "extract table and save to Excel" → def run(driver):
- "fetch table and export to CSV" → def run(driver):
- "click on Submit button" → def run(driver):
- "capture screenshot of current page" → def run(driver):
- "read div container and export as JSON" → def run(driver):
- "type password as welcome#2025" → def run(driver, type_input): # type_input="welcome#2025"
- "enter admin in username field" → def run(driver, type_input): # type_input="admin"
- "type username and press enter" → def run(driver, type_input): # Implements both type + enter
- "enter password and hit return key" → def run(driver, type_input): # Implements both type + return
- "click on search and type query" → def run(driver, type_input): # Implements both click + type
===============================================================================

================================================================================
🔴 CRITICAL TYPE ACTION RULES (READ CAREFULLY)
================================================================================
When generating code for TYPE actions:

1. **Function Signature**: MUST be def run(driver, type_input):

2. **Parameter Usage**:
   ✓ Use type_input parameter directly
   ✓ element.send_keys(type_input)
   
3. **What NOT to do**:
   ❌ type_input = "hardcoded_value"  # Never reassign
   ❌ type_input = "{type_input}"     # Never use f-string value
   ❌ element.send_keys("enter text") # Never use literals
   ❌ def run(driver):                # Never omit parameter
   
4. **What TO do**:
   ✓ def run(driver, type_input):    # Correct signature
   ✓ element.send_keys(type_input)   # Use parameter directly
   
5. **Example Implementation**:
```python
   def run(driver, type_input):
       import json
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       xpath = xpath_json[element_name]
       
       element = WebDriverWait(driver, 30).until(
           EC.visibility_of_element_located((By.XPATH, xpath))
       )
       element.clear()
       element.send_keys(type_input)  # Direct parameter usage
```

6. **Calling Convention**:
   The function will be called externally with the actual value:
   - run(driver, "admin")
   - run(driver, "welcome#2025")
   - run(driver, vault_retrieved_value)

7. **Priority Order**:
   a. If Type Input Data is provided → Pass it as type_input parameter
   b. If Type Input Data is empty AND vault mentioned → Retrieve from vault, then pass as parameter
   c. If both empty → Handle error or skip typing

================================================================================
🔴 CRITICAL MULTI-ACTION IMPLEMENTATION RULES (READ CAREFULLY)
================================================================================
When the user requirement contains multiple actions:

1. **ANALYZE the user requirement** for ALL mentioned actions
2. **IDENTIFY each distinct action**: type, click, enter, scroll, etc.
3. **IMPLEMENT every single action** mentioned - no exceptions
4. **NEVER comment out** any action
5. **NEVER add optional comments** like "uncomment if needed"
6. **EXECUTE actions in the order** mentioned by the user

**Common Multi-Action Patterns:**

Pattern 1: Type + Enter
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    element.send_keys(type_input)
    element.send_keys(Keys.ENTER)  # Both lines execute, no comments
```

Pattern 2: Click + Type
```python
def run(driver, type_input):
    element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.send_keys(type_input)  # Both actions execute
```

Pattern 3: Type + Click + Enter
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.send_keys(type_input)
    element.click()
    element.send_keys(Keys.ENTER)  # All three actions execute
```

**The code must run immediately without any user modifications.**

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

def fallback_code_correction(desc,xpath,file_path,var_name,driver,userid,add_info,error_info,type_input):
    dynamic_status=False
    if type_input==None:
        type_input=""
    if add_info["xpath_variables"] !="":
        dynamic_xpath_variables=add_info["xpath_variables"]
        dynamic_status=True
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    

    error_code=error_info["code"]
    error_file=error_info["file"]
    error_detail=error_info["error"]
    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - error_code: the previously generated Python code that encountered an error (string).
            - error_detail: the exception or error message that occurred when executing the code (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected, single, valid Python function definition named `run(driver)` that fixes the error and performs the described UI action using `pyautogui` for mouse and keyboard automation.
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
                3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{var_name}` key.
                5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                7. Include concise inline comments explaining key steps, imports, and assumptions.
                8. Address and fix the specific error from `{error_detail}`.
                9. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {desc} → the user's action description.
            - {error_code} → the previous code that failed.
            - {error_detail} → the error message to be fixed.
            - {var_name} → the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic according to {desc} and fix the error):
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

                coordinates_points = json_info.get(element_name)
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
            - Analyze the error in {error_detail} and ensure the corrected code addresses the root cause.
            - The coordinate order is always [x_axis, y_axis].
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
                ✅ Correct:   x_center, y_center = coordinates_points
                ❌ Incorrect: left, right, top, bottom = coordinates_points
            - Here assigning coordinates_points should be like below pattern only:
                element_name={var_name}
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get(element_name) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """


    elif img_status and not co_ordinates_status and not img_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP").
            - error_code: The previously generated Python code that encountered an error (string).
            - error_detail: The exception or error message that occurred when executing the code (string).
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected Python Citrix automation function using the pyautogui package to perform the described user action and fix the error.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            element_name = {var_name}
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
            4. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), generate only click code.
            - If the description implies a typing action (e.g., "type username as www"), generate only typing code — do not include click/extract logic.
            - If the description implies a text extraction action (e.g., "extract OTP from image"), generate only text extraction code — not click/type code.
            5. Do not use the description: {desc} inside the code. Create preferred logic based on analyzing the description.
            6. Use pyautogui.locateOnScreen(image_path, confidence=confidence) for image matching.
            7. Include proper error handling (e.g., image not found).
            8. Address and fix the specific error from {error_detail}.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for image click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                element_name = {var_name}
                image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
                time.sleep(1)
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is None:
                    print("Image not found on screen!")
                    return False
                x, y = pyautogui.center(location)
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                return True
            
            Notes / Constraints:
            - Analyze the error in {error_detail} and ensure the corrected code addresses the root cause.
            - Ensure element_name = {var_name} is used before accessing json_info.
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
            """

    elif region_status and not co_ordinates_status and not img_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            ===============================================================================
            ❌ PREVIOUS CODE & ERROR INFORMATION
            ===============================================================================
            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            **Task**: Analyze the error and generate corrected code that fixes the issue. DO NOT repeat the same error. Study the error carefully and implement the proper fix.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            bound_index = json_info[{var_name}]
            4. Extract coordinates from bound_index as [left, top, right, bottom] format.
            5. ALWAYS take a LIVE screenshot of the specified region from the current screen using pyautogui.screenshot().
            6. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), capture the region live and click the center.
            - If the description implies a typing action (e.g., "type username as www"), click the region center and type text.
            - If the description implies a text/table extraction action (e.g., "extract OTP", "extract table data"), capture the region live and use OCR to extract text.
            - If the description mentions scrolling (e.g., "scroll down", "scroll in table"), perform scroll actions within the region.
            - If the description mentions hover (e.g., "hover over element"), move mouse to the region center without clicking.
            - If the description mentions double-click, perform double-click at the region center.
            - If the description mentions right-click, perform right-click at the region center.
            - If the description mentions drag (e.g., "drag element"), perform drag operation from region center.
            7. Do not use the description: {desc} directly in the code. Create preferred logic by analyzing the description.
            8. For all actions, ALWAYS capture the live region first using the bounding box coordinates.
            9. For typing actions, extract the text to be typed from the description (e.g., "type username as admin" → type "admin").
            10. For extraction actions, return the extracted text as the function output.
            11. Include proper error handling (e.g., invalid coordinates, screenshot failure, OCR failure).
            12. Add appropriate time.sleep() delays between actions for stability.
            13. CRITICAL: If there was a previous error, carefully analyze it and fix the issue. Common errors to avoid:
                - ImportError: Ensure all required modules are imported (json, time, pyautogui, PIL, pytesseract)
                - KeyError: Validate that the var_name exists in json_info before accessing
                - ValueError: Check that bound_index has exactly 4 values before unpacking
                - TypeError: Ensure correct data types (integers for coordinates, strings for text)
                - AttributeError: Verify objects have the methods/attributes being called
                - IndexError: Validate list/array indices before accessing
                - NameError: Check all variables are defined before use
                - SyntaxError: Fix any syntax issues like missing colons, brackets, or quotes
            14. DO NOT repeat the same error from the previous code. Implement a different approach if needed.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for region click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for text/table extraction action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    extracted_text = pytesseract.image_to_string(region_screenshot).strip()
                    print(f"Extracted text: {{extracted_text}}")
                    return extracted_text
                except Exception as e:
                    print(f"Error: {{e}}")
                    return None

            Example reference (for typing action with text extraction from description):

            def run(driver=None):
                import json
                import time
                import pyautogui
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    time.sleep(0.3)
                    
                    pyautogui.typewrite("text_here", interval=0.1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for double-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.doubleClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for scroll action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.scroll(-3)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for hover action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for right-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.rightClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False
            """
    else:
        if dynamic_status:
            prompt = f"""
            Generate a **final Selenium-based Python automation code** for the following user requirement.

            ===============================================================================
            🧠 USER REQUIREMENT
            ===============================================================================
            {desc}

            ===============================================================================
            ❌ PREVIOUS CODE & ERROR INFORMATION
            ===============================================================================
            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            **Task**: Analyze the error and generate corrected code that fixes the issue.

            ===============================================================================
            🔍 PROVIDED ELEMENT INFORMATION (REFERENCE ONLY)
            ===============================================================================
            - XPath of the element (use EXACTLY this, do NOT modify): {xpath}
            - Outer HTML (context only): {outer_html}
            - Full Page HTML (context only): {html_content}
            - Variable name: {var_name}
            - Type Input Data: {type_input}

            **Note**: These are provided for context to help you understand the element structure.
            The XPath and dynamic variables must be loaded dynamically from JSON files (see below). 
            The outer HTML and full page HTML help you understand element type, attributes, and page 
            structure to generate correct logic.

            ===============================================================================
            🎯 PRIMARY OBJECTIVE
            ===============================================================================
            Generate **corrected, runnable Selenium + Python code** that:
            - Fixes the error from {error_detail}
            - Uses the provided `driver`
            - Loads the XPath and dynamic variables from JSON files (never hardcodes them)
            - Performs the required browser automation actions
            - Handles any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)
            - Does NOT create, modify, or alter any XPath
            - Must load the XPath and dynamic variables from JSON files using the exact pattern below:

                import json
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)

            Always use the `xpath` variable for locating elements. Never hardcode any XPath or dynamic variables.

            ===============================================================================
            🔄 MULTI-ACTION HANDLING RULES (CRITICAL - READ FIRST)
            ===============================================================================
            When the user description contains MULTIPLE actions in sequence:
            - "type and press enter", "click and type", "type and submit", "fill and click"
            - "enter text and press enter key", "input and hit enter", "type and click submit"
            - "type and hit return", "fill and press enter button", "input and submit"
            - "scroll and click and type", "click then type", "type then click button"

            **MANDATORY RULES - NO EXCEPTIONS**:
            1. ✓ Generate code for ALL actions mentioned - DO NOT comment out or omit any action
            2. ✓ DO NOT add comments like "uncomment if needed" or "optional step" or "if you want"
            3. ✓ DO NOT make decisions about which actions to include - implement exactly what user requests
            4. ✓ Execute actions in the order mentioned by the user
            5. ✓ Add appropriate waits between actions (time.sleep(0.5) between sequential actions)
            6. ✓ Import required modules: import time, from selenium.webdriver.common.keys import Keys

            **Example User Request**: "type username and press enter"

            ✓ CORRECT - Both actions implemented:
            ```python
            def run(driver, type_input):
                import json
                import time
                from selenium.webdriver.common.keys import Keys
                from datas.source_files.xpath_format import format_xpath
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                element.clear()
                element.send_keys(type_input)
                time.sleep(0.5)
                element.send_keys(Keys.RETURN)
            ```

            ❌ WRONG - Commenting out action:
            ```python
            element.send_keys(type_input)
            # element.send_keys(Keys.RETURN)  # Uncomment if you want to press Enter
            ```

            **Common Multi-Action Patterns**:

            1. **Type + Enter**:
               ```python
               element.send_keys(type_input)
               time.sleep(0.5)
               element.send_keys(Keys.RETURN)
               ```

            2. **Type + Click Submit** (requires two XPath variables):
               ```python
               # Type in field
               input_element = WebDriverWait(driver, 30).until(
                   EC.visibility_of_element_located((By.XPATH, xpath))
               )
               input_element.send_keys(type_input)
               time.sleep(0.5)
               
               # Click submit button (if different element)
               # Note: This requires submit button XPath to be loaded separately
               submit_element = WebDriverWait(driver, 30).until(
                   EC.element_to_be_clickable((By.XPATH, xpath_submit))
               )
               submit_element.click()
               ```

            3. **Click + Type**:
               ```python
               element = WebDriverWait(driver, 30).until(
                   EC.element_to_be_clickable((By.XPATH, xpath))
               )
               element.click()
               time.sleep(0.5)
               element.send_keys(type_input)
               ```

            4. **Scroll + Click**:
               ```python
               element = WebDriverWait(driver, 30).until(
                   EC.presence_of_element_located((By.XPATH, xpath))
               )
               driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
               time.sleep(0.5)
               clickable = WebDriverWait(driver, 30).until(
                   EC.element_to_be_clickable((By.XPATH, xpath))
               )
               clickable.click()
               ```

            **Required Imports for Multi-Actions**:
            ```python
            import time  # For delays between actions
            from selenium.webdriver.common.keys import Keys  # For Enter, Tab, Escape, etc.
            ```

            **Keys Available**:
            - Keys.RETURN or Keys.ENTER - Enter key
            - Keys.TAB - Tab key
            - Keys.ESCAPE - Escape key
            - Keys.SPACE - Space bar
            - Keys.BACKSPACE - Backspace
            - Keys.DELETE - Delete

            ===============================================================================
            🧩 ACTION DETECTION RULES
            ===============================================================================
            Detect the action type from the description:
            
            1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
            - Standard click for buttons, links, any clickable element
            - Wait for element to be clickable (30 sec max)

            2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
            - For text input fields
            - Wait for element to be visible (30 sec max)
            - **CRITICAL: Use the type_input parameter passed to the function**
            - **NEVER hardcode the typing value in the function body**
            - **The type_input parameter contains the exact data to type**
            - If previous error was typing-related, ensure parameter is used correctly
            - Example implementations:
            ```python
            # ✓ CORRECT - Using the type_input parameter
            def run(driver, type_input):
                element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                element.clear()
                element.send_keys(type_input)
            
            # ❌ WRONG - Hardcoding or using placeholder text
            element.send_keys("enter your username")  # DON'T DO THIS
            element.send_keys("type password here")   # DON'T DO THIS
            type_input = "hardcoded_value"           # DON'T DO THIS
            ```

            3. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
            - Scroll into view and hover
            - Wait for element to be present (30 sec max)

            4. **ELEMENT WAIT**: "wait for element", "check element", "element exists", "verify element"
            - Check element presence only
            - Return True/False status
            - Do not perform Click or Type action

            5. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
            - **Analyze Outer HTML first**:
                - If contains `<select>` → Use Select class
                - If custom dropdown (ui-select, div-based) → Click + wait + click option
            - Extract option text from description (e.g., "select Declined" → "Declined")

            6. **SCROLL ACTION**: "scroll to", "scroll into view"
            - Scroll element into view
            - Wait for element presence

            7. **SCROLL + CLICK COMBINED ACTION**: "scroll to and click", "scroll and click", "scroll to element and click", "bring into view and click"
            - **This is a COMBINED action requiring both scroll and click**
            - Must perform in sequence: scroll → wait → click
            - Use the pattern below:

            **Implementation Pattern:**
            ```python
            def run(driver):
                import json
                import time
                from datas.source_files.xpath_format import format_xpath
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                # Wait for element presence
                element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
                
                # Wait for scroll to complete
                time.sleep(0.5)
                
                # Wait for element to be clickable and click
                clickable_element = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                clickable_element.click()
            ```

            8. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
            - Wait for element visibility
            - Return element text or value attribute

            9. **CLEAR FIELD**: "clear", "empty", "delete content"
            - Wait for element visibility
            - Clear the input field

            10. **COMBINED ACTIONS**: "type and enter", "type and press enter", "click and type", "type and submit", "type and hit return", "fill and click button"
                - Detect multiple action keywords in single description
                - Generate code for ALL detected actions in sequence
                - Add time.sleep(0.5) between actions
                - Import: from selenium.webdriver.common.keys import Keys, import time
                - **NEVER comment out any action - implement all as requested**
                - **DO NOT add "uncomment if needed" notes**
                - **DO NOT make assumptions - implement exactly what user requests**

            11. **Other Actions**
                - "vault", "from vault", "get from vault" → vault retrieval
                - "save", "export", "write", "store", "download" → native file operations (Excel, CSV, JSON, text)
                - "screenshot", "capture screen" → browser screenshot

            ===============================================================================
            🔐 VAULT HANDLING RULES
            ===============================================================================
            If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
            1. Extract the asset name (the word before "from vault").
            2. Add these imports:
                import sys, os, requests
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            3. Retrieve from:
                vault_url = f"https://droidal.ai/app/project/asset/{userid}/{{asset_name}}/"
                response = requests.get(vault_url)
                vault_data = response.json()
                vault_keys = list(vault_data.keys())
                retrieved_value = vault_data[vault_keys[6]] if len(vault_keys) >= 7 else ""
            4. Use retrieved_value for typing into the field.

            **IMPORTANT**: The type_input parameter should contain the vault-retrieved value when calling the function.

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. **Function Signature Rules**:
            - For TYPE actions: def run(driver, type_input):
            - For NON-TYPE actions: def run(driver):
            - **Analyze the previous error** - if it was signature-related, ensure correct signature

            2. Use the xpath on the code by below pattern:
                import json
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)

            3. Do NOT hardcode the XPath or dynamic variables anywhere in the code.  
                Always use the `xpath` variable loaded from the JSON files with format_xpath function.

            4. Don't miss the needed package imports:
            import json #must
            from datas.source_files.xpath_format import format_xpath #must
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC
            # For multi-actions, also import:
            import time
            from selenium.webdriver.common.keys import Keys

            5. **Type Functionality (CRITICAL):**
                - **For TYPE actions, the function MUST accept type_input as a parameter**
                - **Function signature: def run(driver, type_input):**
                - **ALWAYS use the type_input parameter directly - DO NOT reassign or hardcode it**
                - **NEVER create a new variable type_input = "some_value" inside the function**
                - **If previous error was typing-related**, verify:
                * Function accepts type_input parameter
                * Parameter is used directly without reassignment
                * No hardcoded values in send_keys()
                
                Example:
                ```python
                # ✓ CORRECT - Using parameter
                def run(driver, type_input):
                    import json
                    from datas.source_files.xpath_format import format_xpath
                    
                    # Load XPath from JSON
                    json_path = "json_info/json_xpath.json"
                    element_name = "{var_name}"
                    with open(json_path, "r") as f:
                        xpath_json = json.load(f)
                    
                    # Load dynamic variables from JSON
                    dynamic_var_path = "json_info/dynamic_xpath.json"
                    with open(dynamic_var_path, "r") as f:
                        dynamic_info = json.load(f)
                    values = dynamic_info["data"]
                    
                    # Format XPath with dynamic values using format_xpath
                    xpath_pattern = xpath_json[element_name]
                    xpath = format_xpath(xpath_pattern, values)
                    
                    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                    element.clear()
                    element.send_keys(type_input)  # Use the parameter directly
                
                # ❌ WRONG - These cause errors
                def run(driver, type_input):
                    type_input = "hardcoded_value"  # DON'T DO THIS
                    element.send_keys(type_input)
                
                def run(driver):
                    type_input = "{type_input}"  # DON'T DO THIS
                    element.send_keys(type_input)
                ```

            6. Dropdown handling rules:
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

            7. **Address the specific error from {error_detail}** - analyze what went wrong and fix it.

            8. **Common Error Fixes**:
            - **"missing 1 required positional argument: 'type_input'"** → Function signature missing type_input parameter
            - **"takes 1 positional argument but 2 were given"** → Function should accept type_input for TYPE actions
            - **"element not found" or "timeout"** → Increase wait time, verify XPath loading
            - **"element not clickable"** → Add scroll into view, wait for clickability
            - **"stale element"** → Re-locate element after page changes
            - **"wrong text typed"** → Using hardcoded value instead of type_input parameter
            - **"send_keys failed"** → Verify element is visible, type_input has value, parameter exists
            - **"NameError: name 'type_input' is not defined"** → Add type_input as function parameter
            - **"KeyError" or "format" errors** → Check dynamic variable loading from JSON using format_xpath
            - **"format_xpath not found"** → Ensure import: from datas.source_files.xpath_format import format_xpath

            9. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

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

            return table_data

            ===============================================================================
            💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION FIXED)
            ===============================================================================
            Dynamically detect both file path and format based on the user description.

            🧩 Step 1: Path Detection
            - If the description includes any of these patterns:
                "in this path", "to path", "save at", "save in", "write it in"
            - Extract the full file path.
            - If none found, default to "output.xlsx".

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
            ⚠️ CODE GENERATION VALIDATION (PRE-OUTPUT CHECK)
            ===============================================================================
            Before outputting the final code, verify ALL of these conditions:
            
            1. ✓ All actions mentioned by user are implemented (NONE commented out)
            2. ✓ No "uncomment if needed" or "optional" comments added
            3. ✓ Action sequence matches user description exactly
            4. ✓ Appropriate delays added between multi-actions (time.sleep(0.5))
            5. ✓ Required imports present (Keys, time for multi-actions)
            6. ✓ Function signature matches action type (type_input parameter for TYPE actions)
            7. ✓ XPath loaded from JSON using format_xpath function (NEVER hardcoded)
            8. ✓ Dynamic variables loaded from JSON (NEVER hardcoded)
            9. ✓ No hardcoded typing values - type_input parameter used directly
            10. ✓ Specific error from {error_detail} is addressed and fixed
            
            **If ANY validation fails, regenerate the code correctly.**
            ===============================================================================

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            **For TYPE actions:**
            ```python
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC

            def run(driver, type_input):
                import json
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                # Use type_input parameter directly - DO NOT reassign
                element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                element.clear()
                element.send_keys(type_input)
            ```

            **For TYPE + ENTER actions:**
            ```python
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC

            def run(driver, type_input):
                import json
                import time
                from selenium.webdriver.common.keys import Keys
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                element.clear()
                element.send_keys(type_input)
                time.sleep(0.5)
                element.send_keys(Keys.RETURN)
            ```

            **For NON-TYPE actions:**
            ```python
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC

            def run(driver):
                import json
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                # Generated corrected logic here
            ```

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run()` function block.
            - The import statement `import json` is mandatory and must always be included.
            - The import statement `from datas.source_files.xpath_format import format_xpath` is mandatory and must always be included.
            - For multi-actions, `import time` and `from selenium.webdriver.common.keys import Keys` are mandatory.
            - The xpath formatting with dynamic variables must always follow the pattern:
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
            - This pattern is NON-NEGOTIABLE and must be present in every generated code.
            - Dynamic variables must ALWAYS be loaded from the JSON file and formatted using format_xpath, NEVER hardcoded.
            - **For TYPE actions**: 
            * Function signature MUST be: def run(driver, type_input):
            * ALWAYS use the type_input parameter directly
            * NEVER reassign type_input inside the function
            * NEVER hardcode typing values
            - **For NON-TYPE actions**: Function signature is: def run(driver):
            - **For MULTI-ACTIONS**: Implement ALL actions mentioned, NO commenting out, NO "optional" notes
            - Analyze the error from {error_detail} and ensure the corrected code addresses the root cause.
            - Use the outer HTML ({outer_html}) and full page HTML ({html_content}) as reference to understand:
                * Element type (input, select, div, button, etc.)
                * Element attributes (class, id, data-*, etc.)
                * Parent/child relationships
                * Whether it's a standard HTML element or custom component
            - The current element XPath ({xpath}) should guide you on element location strategy.
            - **If the previous error mentioned type_input issues**, ensure:
            * Function accepts type_input as parameter (for TYPE actions)
            * No hardcoded assignments like type_input = "value"
            * Direct usage: element.send_keys(type_input)
            - **If the previous error mentioned format or xpath issues**, ensure:
            * Import format_xpath function from datas.source_files.xpath_format
            * Use format_xpath(xpath_pattern, values) instead of .format(*values)
            - **If user requests multiple actions**, ensure:
            * ALL actions are implemented without any commenting
            * Proper delays between actions (time.sleep(0.5))
            * Required imports (Keys, time) are included
            
            ===============================================================================
            💬 EXAMPLES
            ===============================================================================
            - "select Declined from Bill Status dropdown" → def run(driver):
            - "choose Completed from Status menu" → def run(driver):
            - "type username from vault in username field" → def run(driver, type_input):
            - "extract table and save to Excel" → def run(driver):
            - "fetch table and export to CSV" → def run(driver):
            - "click on Submit button" → def run(driver):
            - "capture screenshot of current page" → def run(driver):
            - "read div container and export as JSON" → def run(driver):
            - "type password as welcome#2025" → def run(driver, type_input): # type_input="welcome#2025"
            - "enter admin in username field" → def run(driver, type_input): # type_input="admin"
            - "type admin and press enter" → def run(driver, type_input): # BOTH typing and Enter implemented
            - "fill username and click submit" → def run(driver, type_input): # BOTH filling and clicking implemented
            - "enter password and hit return key" → def run(driver, type_input): # BOTH entering and Return key implemented
            - "scroll to element and click it" → def run(driver): # BOTH scroll and click implemented
            - "click and then type text" → def run(driver, type_input): # BOTH click and type implemented
            
            ===============================================================================
            🔴 CRITICAL TYPE ACTION RULES (READ CAREFULLY)
            ===============================================================================
            When generating corrected code for TYPE actions:

            1. **Function Signature**: MUST be def run(driver, type_input):

            2. **Parameter Usage**:
            ✓ Use type_input parameter directly
            ✓ element.send_keys(type_input)
            
            3. **What NOT to do**:
            ❌ type_input = "hardcoded_value"  # Never reassign
            ❌ type_input = "{type_input}"     # Never use f-string value
            ❌ element.send_keys("enter text") # Never use literals
            ❌ def run(driver):                # Never omit parameter
            ❌ xpath = xpath_json[element_name].format(*values)  # Never use .format() directly
            
            4. **What TO do**:
            ✓ def run(driver, type_input):    # Correct signature
            ✓ element.send_keys(type_input)   # Use parameter directly
            ✓ from datas.source_files.xpath_format import format_xpath  # Import format_xpath
            ✓ xpath_pattern = xpath_json[element_name]  # Get pattern
            ✓ xpath = format_xpath(xpath_pattern, values)  # Use format_xpath function
            
            5. **Error Analysis for Typing**:
            - **"missing 1 required positional argument: 'type_input'"** 
                → Previous code: def run(driver):
                → Fixed code: def run(driver, type_input):
            
            - **"takes 1 positional argument but 2 were given"**
                → Previous code: def run(driver):
                → Fixed code: def run(driver, type_input):
            
            - **"NameError: name 'type_input' is not defined"**
                → Previous code had: element.send_keys(type_input) but no parameter
                → Fixed code: def run(driver, type_input): with element.send_keys(type_input)
            
            - **"wrong text typed" or "placeholder text appeared"**
                → Previous code had: type_input = "hardcoded" or element.send_keys("placeholder")
                → Fixed code: Use type_input parameter directly
            
            - **"send_keys failed"**
                → Verify element is visible, editable
                → Ensure type_input parameter exists and has value
                → Add element.clear() before send_keys()
            
            - **"format_xpath not found" or "module has no attribute 'format_xpath'"**
                → Previous code missing: from datas.source_files.xpath_format import format_xpath
                → Fixed code: Add the import at the beginning of the function

            6. **Example Fixed Code**:
```python
            # Previous error: "missing 1 required positional argument: 'type_input'"
            # Previous code:
            def run(driver):
                type_input = "{type_input}"
                element.send_keys(type_input)
            
            # FIXED code:
            def run(driver, type_input):
                import json
                from datas.source_files.xpath_format import format_xpath
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                element.clear()
                element.send_keys(type_input)  # Direct parameter usage
```

            7. **Calling Convention**:
            The function will be called externally with the actual value:
            - run(driver, "admin")
            - run(driver, "welcome#2025")
            - run(driver, vault_retrieved_value)

            8. **Priority Order**:
            a. Fix the specific error from {error_detail}
            b. Ensure correct function signature for action type
            c. Use type_input parameter correctly (no reassignment)
            d. Import and use format_xpath function correctly
            e. Verify XPath and dynamic variable loading pattern is correct
            f. Add proper waits and error handling
            
            9. **Multi-Action Type Rules**:
            When user requests "type and [action]":
            - Implement typing first using type_input parameter
            - Add time.sleep(0.5) delay
            - Implement second action (Enter, click, etc.)
            - Import required modules (Keys, time)
            - **NEVER comment out the second action**
            - **NEVER add "optional" or "uncomment if needed" notes**
            
            Example:
```python
            # User: "type username and press enter"
            # ✓ CORRECT - Both actions implemented:
            def run(driver, type_input):
                import json
                import time
                from selenium.webdriver.common.keys import Keys
                from datas.source_files.xpath_format import format_xpath
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Load XPath from JSON
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                # Load dynamic variables from JSON
                dynamic_var_path = "json_info/dynamic_xpath.json"
                with open(dynamic_var_path, "r") as f:
                    dynamic_info = json.load(f)
                values = dynamic_info["data"]
                
                # Format XPath with dynamic values using format_xpath
                xpath_pattern = xpath_json[element_name]
                xpath = format_xpath(xpath_pattern, values)
                
                element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                element.clear()
                element.send_keys(type_input)
                time.sleep(0.5)
                element.send_keys(Keys.RETURN)
            
            # ❌ WRONG - Second action commented:
            def run(driver, type_input):
                element.send_keys(type_input)
                # element.send_keys(Keys.RETURN)  # Uncomment if you want to press Enter
```
            
            ===============================================================================
            🎯 FINAL CHECKLIST BEFORE CODE OUTPUT
            ===============================================================================
            Verify ALL these points before generating final code:
            
            ✓ 1. Error from {error_detail} is analyzed and fixed
            ✓ 2. Function signature matches action type (type_input for TYPE actions)
            ✓ 3. All user-requested actions are implemented (NO commenting)
            ✓ 4. XPath loaded from JSON using format_xpath (NEVER hardcoded)
            ✓ 5. Dynamic variables loaded from JSON (NEVER hardcoded)
            ✓ 6. type_input parameter used directly (NEVER reassigned)
            ✓ 7. Required imports included (json, format_xpath, Keys/time for multi-actions)
            ✓ 8. Proper waits added (WebDriverWait with EC conditions)
            ✓ 9. Multi-actions have time.sleep(0.5) delays between steps
            ✓ 10. No explanatory text, markdown, or comments in output
            ✓ 11. Code is runnable Python that can be directly written to .py file
            ✓ 12. All actions execute in user-specified order
            
            **If ANY item fails, regenerate the code correctly.**
            
            ===============================================================================
            🚀 GENERATE CORRECTED CODE NOW
            ===============================================================================
            Based on all the rules above, generate the FINAL CORRECTED CODE that:
            - Fixes the error: {error_detail}
            - Implements the requirement: {desc}
            - Uses XPath from JSON: {var_name}
            - Follows all mandatory patterns and rules
            - Is immediately runnable without modifications
            
            Output only valid Python code, no explanations, no markdown formatting.
            """
        else:
            prompt = f"""
Generate a **final Selenium-based Python automation code** for the following user requirement.

===============================================================================
🧠 USER REQUIREMENT
===============================================================================
{desc}

===============================================================================
❌ PREVIOUS CODE & ERROR INFORMATION
===============================================================================
Previous Code:
{error_code}

Error Encountered:
{error_detail}

**Task**: Analyze the error and generate corrected code that fixes the issue.

===============================================================================
🔍 PROVIDED ELEMENT INFORMATION (REFERENCE ONLY)
===============================================================================
- XPath of the element (use EXACTLY this, do NOT modify): {xpath}
- Outer HTML (context only): {outer_html}
- Full Page HTML (context only): {html_content}
- Variable name: {var_name}
- Type Input Data: {type_input}

**Note**: These are provided for context to help you understand the element structure.
The XPath must be loaded dynamically from JSON (see below). The outer HTML and full page HTML
help you understand element type, attributes, and page structure to generate correct logic.

===============================================================================
🎯 PRIMARY OBJECTIVE
===============================================================================
Generate **corrected, runnable Selenium + Python code** that:
- Fixes the error from {error_detail}
- Uses the provided `driver`
- **For TYPE actions**: Function signature is `run(driver, type_input)` with 2 arguments
- **For NON-TYPE actions**: Function signature is `run(driver)` with 1 argument only
- **For COMBINED actions**: Follow user's EXACT action sequence without skipping or commenting out steps
- Loads the XPath dynamically from JSON (never hardcodes it)
- Performs the required browser automation actions
- Handles any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)
- Does NOT create, modify, or alter any XPath
- Must load the XPath dynamically from the JSON file using the exact pattern below:

    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"

    with open(json_path, "r") as f:
        xpath_json = json.load(f)

    xpath = xpath_json[element_name]

Always use the `xpath` variable for locating elements. Never hardcode any XPath.

===============================================================================
🔗 COMBINED/SEQUENTIAL ACTION DETECTION (PRIORITY CHECK)
===============================================================================
**CRITICAL**: Before applying single-action rules, check if the user requirement contains MULTIPLE actions.

Common multi-action patterns:
1. **"type ... and press Enter"** / **"type ... and hit Enter"** / **"type ... then Enter"**
2. **"type ... and click Submit"** / **"enter ... and click"**
3. **"click ... and type"** / **"click ... then type"**
4. **"type ... press Tab ... type"**
5. **"scroll ... and click"** / **"scroll ... then click"**
6. **"hover ... and click"** / **"hover ... then click"**

**Detection Keywords**:
- "and" / "then" / "after that" / "followed by"
- "press Enter" / "hit Enter" / "Enter key"
- "press Tab" / "Tab key"
- Multiple verbs: "type", "click", "press", "select", "scroll", "hover"

**MANDATORY RULES FOR COMBINED ACTIONS**:
1. **Execute ALL actions mentioned by the user in EXACT order**
2. **NEVER comment out or skip any action**
3. **NEVER add optional actions that user didn't request**
4. **NEVER decide on behalf of user what is "needed" or "not needed"**

===============================================================================
🎬 COMBINED ACTION IMPLEMENTATION PATTERNS
===============================================================================

**Pattern 1: TYPE + PRESS ENTER**
User says: "type username and press Enter"
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run(driver, type_input):  # ✓ 2 arguments (it's a TYPE action)
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Step 1: Type the input
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    
    # Step 2: Press Enter key (MANDATORY - user requested it)
    element.send_keys(Keys.RETURN)
```

**Pattern 2: TYPE + PRESS TAB**
User says: "type email and press Tab"
```python
from selenium.webdriver.common.keys import Keys

def run(driver, type_input):  # ✓ 2 arguments
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.TAB)  # MANDATORY - user requested Tab
```

**Pattern 3: CLICK + TYPE**
User says: "click the field and type the value"
```python
def run(driver, type_input):  # ✓ 2 arguments (overall is TYPE action)
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Step 1: Click the element (MANDATORY)
    element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
    
    # Step 2: Type the value (MANDATORY)
    element.clear()
    element.send_keys(type_input)
```

**Pattern 4: SCROLL + CLICK**
User says: "scroll to element and click it"
```python
import time

def run(driver):  # ✓ 1 argument (no typing involved)
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Step 1: Scroll into view (MANDATORY)
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    time.sleep(0.5)
    
    # Step 2: Click the element (MANDATORY)
    clickable_element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    clickable_element.click()
```

**Pattern 5: TYPE + CLICK ANOTHER ELEMENT**
User says: "type username and click the submit button"
**NOTE**: If two different elements are involved, this may need multi-step orchestration.
For single-element prompts, generate code for the primary element only and inform the user.

**Pattern 6: HOVER + CLICK**
User says: "hover over menu and click"
```python
from selenium.webdriver.common.action_chains import ActionChains

def run(driver):  # ✓ 1 argument
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Step 1: Hover (MANDATORY)
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    
    # Step 2: Click (MANDATORY)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
```

===============================================================================
⚡ CRITICAL RULES FOR MULTI-ACTION CODE GENERATION
===============================================================================
1. **DO NOT comment out any user-requested action**
   - ❌ BAD: `# element.send_keys(Keys.RETURN)  # Uncomment if needed`
   - ✓ GOOD: `element.send_keys(Keys.RETURN)`

2. **DO NOT add explanatory comments suggesting the action is optional**
   - ❌ BAD: `# Press Enter (optional based on your requirement)`
   - ✓ GOOD: Just execute the action

3. **DO NOT make assumptions about what user "actually needs"**
   - If user says "type and press Enter", you MUST include both actions
   - If user says "click and type", you MUST include both actions

4. **Import necessary modules for combined actions**:
   - For Enter/Tab keys: `from selenium.webdriver.common.keys import Keys`
   - For hover: `from selenium.webdriver.common.action_chains import ActionChains`
   - For delays: `import time`

5. **Function signature determination for combined actions**:
   - If ANY step involves typing → `def run(driver, type_input):`
   - If NO typing involved → `def run(driver):`

6. **Execute actions in EXACT order specified by user**:
   - "type then click" → type first, then click
   - "click then type" → click first, then type
   - "scroll and click" → scroll first, then click

===============================================================================
🧩 SINGLE ACTION DETECTION RULES (FALLBACK)
===============================================================================
If the requirement is a **single action** (no "and", "then", or multiple verbs), use these rules:

1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
- Standard click for buttons, links, any clickable element
- Wait for element to be clickable (30 sec max)
- **Function signature**: `def run(driver):`

2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
- For text input fields
- Wait for element to be visible (30 sec max)
- **Function signature**: `def run(driver, type_input):`
- **CRITICAL: Use the type_input parameter directly - it contains the exact data to type**
- **NEVER hardcode or use placeholder text**

3. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
- Scroll into view and hover
- Wait for element to be present (30 sec max)
- **Function signature**: `def run(driver):`

4. **ELEMENT WAIT**: "wait for element", "check element", "element exists", "verify element"
- Check element presence only
- Return True/False status
- **Function signature**: `def run(driver):`

5. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
- **Function signature**: `def run(driver):`
- **Analyze Outer HTML first**:
    - If contains `<select>` → Use Select class
    - If custom dropdown (ui-select, div-based) → Click + wait + click option

6. **SCROLL ACTION**: "scroll to", "scroll into view"
- Scroll element into view
- Wait for element presence
- **Function signature**: `def run(driver):`

7. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
- Wait for element visibility
- Return element text or value attribute
- **Function signature**: `def run(driver):`

8. **CLEAR FIELD**: "clear", "empty", "delete content"
- Wait for element visibility
- Clear the input field
- **Function signature**: `def run(driver):`

===============================================================================
🔐 VAULT HANDLING RULES (FOR TYPE ACTIONS)
===============================================================================
If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
1. This is still a TYPE action, so use `def run(driver, type_input):`
2. The type_input parameter will contain the vault-retrieved value (handled by caller)
3. Simply use the type_input parameter as-is

===============================================================================
⚙️ IMPLEMENTATION RULES
===============================================================================
1. **CRITICAL FUNCTION SIGNATURE RULES**:
   - **TYPE actions (or combined actions with typing)**: `def run(driver, type_input):`
   - **ALL OTHER actions**: `def run(driver):`
   
2. Use the xpath on the code by below pattern:
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]

3. Do NOT hardcode the XPath anywhere in the code.  
   Always use the `xpath` variable loaded from the JSON file.

4. Don't miss the needed package imports:
   import json #must
   from selenium.webdriver.common.by import By
   from selenium.webdriver.support.ui import WebDriverWait, Select
   from selenium.webdriver.support import expected_conditions as EC
   from selenium.webdriver.common.keys import Keys  # For Enter/Tab/etc.
   from selenium.webdriver.common.action_chains import ActionChains  # For hover

5. **Type Functionality (CRITICAL):**
   - Function signature: `def run(driver, type_input):`
   - **USE the type_input parameter directly - it's passed as an argument**
   - **NEVER hardcode text values in send_keys()**
   - **ALWAYS DO**: `element.send_keys(type_input)`

6. **Address the specific error from {error_detail}** - analyze what went wrong and fix it.

7. **Common Error Fixes**:
   - If error mentions "element not found" or "timeout" → Increase wait time, verify XPath loading
   - If error mentions "element not clickable" → Add scroll into view, wait for clickability
   - If error mentions "stale element" → Re-locate element after page changes
   - If error mentions typing issues → Ensure type_input parameter is used correctly
   - If error mentions "send_keys" → Verify function has 2 args and uses type_input parameter
   - If error mentions wrong argument count → Check if TYPE action has 2 args, others have 1 arg
   - If error mentions missing Keys → Import `from selenium.webdriver.common.keys import Keys`

8. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

===============================================================================
📊 TABLE / DIV-CONTAINER EXTRACTION RULES
===============================================================================
When the user requirement mentions:
- "extract table", "get table data", "read table", "fetch table contents"
- "extract grid", "extract div table", "extract container", or "get div data"

You must:
1. Use function signature: `def run(driver):`  # 1 argument
2. Locate the table or div container using the provided XPath.
3. Wait for it to be visible using WebDriverWait.
4. Extract all visible rows and cells into a structured list.
5. Normalize column counts to prevent pandas or Excel export errors.

===============================================================================
💾 NATIVE FILE OPERATION RULES
===============================================================================
Use function signature: `def run(driver):`  # 1 argument

Dynamically detect both file path and format based on the user description.

===============================================================================
✅ OUTPUT FORMAT (MANDATORY)
===============================================================================

**FOR TYPE ACTIONS (INCLUDING COMBINED TYPE + OTHER):**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # If Enter/Tab needed
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver, type_input):  # ✓ 2 arguments for TYPE action
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Execute ALL user-requested actions in order
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # ✓ Use the parameter
    # Additional actions if requested (e.g., element.send_keys(Keys.RETURN))
```

**FOR ALL OTHER ACTIONS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver):  # ✓ 1 argument for non-TYPE actions
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    # Execute ALL user-requested actions in order
```

===============================================================================
NOTE: (MANDATORY)
===============================================================================
- **PRIORITY 1**: Check for combined/multi-action requirements FIRST
- **PRIORITY 2**: If combined actions detected, execute ALL steps without commenting out
- **PRIORITY 3**: Import necessary modules (Keys, ActionChains, time) for combined actions
- **CRITICAL**: TYPE actions use `def run(driver, type_input):` with 2 arguments
- **CRITICAL**: All other actions use `def run(driver):` with 1 argument only
- **CRITICAL**: NEVER comment out user-requested actions with "uncomment if needed"
- **CRITICAL**: NEVER add optional actions user didn't request
- All import statements must be placed inside the `run()` function block.
- The import statement `import json` is mandatory and must always be included.
- The xpath loading pattern must always follow the exact format shown above.
- **For TYPE actions**: Use the type_input parameter - it's passed as an argument with the exact data
- **NEVER** hardcode text in send_keys() - always use the type_input parameter
- Analyze the error from {error_detail} and ensure the corrected code addresses the root cause.

===============================================================================
💬 EXAMPLES
===============================================================================

**Combined Action Examples:**

Example 1: "type username and press Enter"
```python
from selenium.webdriver.common.keys import Keys

def run(driver, type_input):  # 2 args
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.RETURN)  # ✓ MANDATORY - user requested
```

Example 2: "scroll to button and click it"
```python
import time

def run(driver):  # 1 arg
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    time.sleep(0.5)
    clickable = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    clickable.click()
```

Example 3: "click field and type the data"
```python
def run(driver, type_input):  # 2 args
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]
    
    element = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    element.click()
    element.clear()
    element.send_keys(type_input)
```

**Single Action Examples:**
```python
# "click Submit button"
def run(driver):
    # ... load xpath ...
    element.click()

# "type username"
def run(driver, type_input):
    # ... load xpath ...
    element.send_keys(type_input)
```

===============================================================================
🔴 CRITICAL REMINDERS
===============================================================================
1. **Multi-action detection is PRIORITY 1** - Check for "and", "then", multiple verbs
2. **Execute ALL actions user requests** - Never comment out or skip
3. **Never add actions user didn't request** - Don't assume needs
4. **Import Keys for Enter/Tab** - `from selenium.webdriver.common.keys import Keys`
5. **Import ActionChains for hover** - `from selenium.webdriver.common.action_chains import ActionChains`
6. **Correct function signature** - 2 args if typing involved, 1 arg otherwise
7. **No placeholder text** - Use type_input parameter for actual data
8. **Fix the specific error** - Address {error_detail} root cause

===============================================================================
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

def code_correction_text(desc,xpath,file_path,var_name,driver,userid):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
        

    # if region_status:
    #     from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run(driver)` that extracts text from the UI element at the specified coordinates and returns it.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
            3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{{var_name}}` key.
            5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
            6. Use `pyautogui` and `pyperclip` to:
            - Click on the element at the specified coordinates
            - Select the text (using appropriate keyboard shortcuts like Ctrl+A or triple-click)
            - Copy the text to clipboard (Ctrl+C)
            - Retrieve the text from clipboard using `pyperclip.paste()`
            - Return the extracted text as a string
            7. Include concise inline comments explaining key steps, imports, and assumptions.
            8. The function MUST return the extracted text as a string.
            9. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {{desc}} → will be replaced with the user's action description (always about extracting text from a UI element).
            - {{var_name}} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern exactly):

            def run(driver):
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Silence unused parameter
                _ = driver
                
                # Define JSON file path
                json_path = "json_info/json_xpath.json"
                
                # Validate JSON file existence
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"JSON file not found: {{json_path}}")
                
                # Load coordinate data from JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                # Retrieve coordinates using the provided key
                element_name = {{var_name}}
                coordinates_points = json_info.get(element_name)
                
                # Validate coordinate format
                if not isinstance(coordinates_points, (list, tuple)) or len(coordinates_points) != 2:
                    raise ValueError(f"Expected coordinate_index as a list of 2 integers for key: {{element_name}}")
                
                # Extract x and y coordinates
                x_center, y_center = map(int, coordinates_points)
                
                # Clear clipboard before operation
                pyperclip.copy("")
                
                # Move to the element and click to focus
                time.sleep(0.5)
                pyautogui.moveTo(x_center, y_center, duration=0.3)
                pyautogui.click()
                time.sleep(0.3)
                
                # Select all text in the focused element (Ctrl+A)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Copy selected text to clipboard (Ctrl+C)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                # Retrieve text from clipboard
                extracted_text = pyperclip.paste()
                
                # Return the extracted text
                return extracted_text

            Notes / Constraints:
            - The coordinate order is always [x_axis, y_axis].
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
            ✅ Correct: x_center, y_center = coordinates
            ❌ Incorrect: left, right, top, bottom = coordinates
            - The pattern for retrieving coordinates must be exactly:
            element_name = {{var_name}}
            coordinates_points = json_info.get(element_name)
            - The function MUST return the extracted text as a string.
            - Use `pyperclip` for reliable clipboard operations.
            - Include appropriate sleep delays to ensure UI actions complete.
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
            """


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "extract text from field", "get OTP from screen", "read value from label").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python Citrix automation function using pyautogui and pytesseract packages to extract text from the UI element identified by the image.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[{var_name}]}}"

            4. Use pyautogui.locateOnScreen(image_path, confidence=confidence) to find the element on screen.
            5. Take a screenshot of the located region using pyautogui.screenshot().
            6. Use pytesseract.image_to_string() to extract text from the screenshot.
            7. Clean and return the extracted text as a string.
            8. Include proper error handling for:
            - Image not found on screen
            - OCR extraction failures
            - Empty or invalid text extraction
            9. Do NOT include click or typing logic - only text extraction.
            10. Return the extracted text string, or None if extraction fails.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver=None):
                import json
                import time
                import pyautogui
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return None
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                confidence = 0.8
                
                time.sleep(1)
                
                # Locate the element on screen
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                except Exception as e:
                    print(f"Error locating image: {{e}}")
                    return None
                
                if location is None:
                    print("Image not found on screen!")
                    return None
                
                # Take screenshot of the located region
                screenshot = pyautogui.screenshot(region=location)
                
                # Extract text using OCR
                try:
                    extracted_text = pytesseract.image_to_string(screenshot)
                    extracted_text = extracted_text.strip()
                    
                    if not extracted_text:
                        print("No text could be extracted from the region")
                        return None
                    
                    return extracted_text
                    
                except Exception as e:
                    print(f"OCR extraction failed: {{e}}")
                    return None

            Notes:
            - The function always returns extracted text as a string, or None on failure.
            - Uses pytesseract for OCR (Optical Character Recognition).
            - Captures only the region where the element is located for better accuracy.
            - Includes error handling for all potential failure points.
            - The confidence parameter (default 0.8) can be adjusted if needed.
            - Do not generate click, type, or any other action code - only text extraction.
            """

    elif region_status and not co_ordinates_status and not img_status:
        prompt = f""""""
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
            Generate **runnable Selenium + Python code** that:
            - Uses the provided `driver`
            - Loads the XPath dynamically from JSON using the exact pattern below
            - Extracts text from the located element
            - Returns the extracted text as a string

            CRITICAL: Must load the XPath dynamically from the JSON file using this exact pattern:

                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]

            Always use the `xpath` variable for locating elements. Never hardcode any XPath.

            ===============================================================================
            🧩 TEXT EXTRACTION RULES
            ===============================================================================
            The user requirement is ALWAYS about extracting text from a web element.

            Implementation steps:
            1. Load XPath from JSON file using the pattern above
            2. Locate the element using WebDriverWait with the loaded XPath
            3. Extract text using `.text` attribute or `.get_attribute("textContent")`
            4. Clean and strip the extracted text
            5. Return the text as a string

            For different element types:
            - Regular elements: Use `element.text`
            - Input fields: Use `element.get_attribute("value")`
            - Hidden/whitespace text: Use `element.get_attribute("textContent")`
            - If `.text` returns empty, try `get_attribute("textContent")` or `get_attribute("innerText")`

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. The function name must be exactly `run(driver)`.
            2. Load XPath using this exact pattern:
                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                xpath = xpath_json[element_name]

            3. Do NOT hardcode the XPath anywhere in the code.
            4. Required imports (must be inside the function):
                import json  # MANDATORY
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

            5. Use WebDriverWait to ensure element is present before extraction
            6. Return the extracted text - do NOT print it
            7. Handle errors gracefully (return empty string or None on failure)
            8. Avoid any explanation, markdown, or comments — output must be valid runnable Python

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            def run(driver):
                import json
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]
                
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    
                    extracted_text = element.text.strip()
                    
                    if not extracted_text:
                        extracted_text = element.get_attribute("textContent").strip()
                    
                    if not extracted_text:
                        extracted_text = element.get_attribute("value")
                    
                    return extracted_text if extracted_text else ""
                    
                except Exception as e:
                    print(f"Error extracting text: {{e}}")
                    return ""

            MANDATORY CONDITION :
            - It should must returns the extracted text compulsory

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run(driver)` function block
            - The import statement `import json` is mandatory and must always be included
            - The function must RETURN the extracted text, not print it
            - Try multiple text extraction methods (.text, textContent, value) for robustness
            - Handle exceptions and return empty string on failure

            ===============================================================================
            💬 EXAMPLES OF USER REQUIREMENTS (ALL ABOUT TEXT EXTRACTION)
            ===============================================================================
            - "extract text from the label"
            - "get value from the input field"
            - "read text from the div element"
            - "fetch content from the span"
            - "retrieve text from the button"
            - "extract OTP from the code field"
            - "get username from the profile section"
            ===============================================================================
            """

    if not region_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""
import pandas as pd
import json
from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
def run(driver=None):
    desc="{desc}"
    json_path = "json_info/json_xpath.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    bound_index=json_info["{var_name}"]
    img_path=capture_region(bound_index)
    text=gemini_image_response(img_path,desc)
    return text
        """
    # Remove markdown code block markers
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()
    write_code(file_path,code_to_write)
    return code_to_write

def fallback_code_correction_text(desc,xpath,file_path,var_name,driver,userid,error_info):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    error_code=error_info["code"]
    error_file=error_info["file"]
    error_detail=error_info["error"]
    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string) - ALWAYS about extracting text from a UI element.
            - error_code: the previously generated Python code that encountered an error (string).
            - error_detail: the exception or error message that occurred when executing the code (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code that extracts text from the UI element.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected, single, valid Python function definition named `run(driver)` that fixes the error and extracts text from the UI element at the specified coordinates, returning the extracted text as a string.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
            3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{var_name}` key.
            5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
            6. Use `pyautogui` and `pyperclip` to:
            - Click on the element at the specified coordinates
            - Select the text (using appropriate keyboard shortcuts like Ctrl+A or triple-click)
            - Copy the text to clipboard (Ctrl+C)
            - Retrieve the text from clipboard using `pyperclip.paste()`
            - Return the extracted text as a string
            7. Include concise inline comments explaining key steps, imports, and assumptions.
            8. **CRITICAL**: Address and fix the specific error from `{error_detail}`. Analyze the root cause and implement a robust solution.
            9. The function MUST return the extracted text as a string.
            10. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {{desc}} → the user's action description (always about text extraction).
            - {{error_code}} → the previous code that failed.
            - {{error_detail}} → the error message to be fixed.
            - {{var_name}} → the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic to fix the error):

            def run(driver):
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Silence unused parameter
                _ = driver
                
                # Define JSON file path
                json_path = "json_info/json_xpath.json"
                
                # Validate JSON file existence
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"JSON file not found: {{json_path}}")
                
                # Load coordinate data from JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                # Retrieve coordinates using the provided key
                element_name = {{var_name}}
                coordinates_points = json_info.get(element_name)
                
                # Validate coordinate format
                if not isinstance(coordinates_points, (list, tuple)) or len(coordinates_points) != 2:
                    raise ValueError(f"Expected coordinate_index as a list of 2 integers for key: {{element_name}}")
                
                # Extract x and y coordinates
                x_center, y_center = map(int, coordinates_points)
                
                # Clear clipboard before operation
                pyperclip.copy("")
                
                # Move to the element and click to focus
                time.sleep(0.5)
                pyautogui.moveTo(x_center, y_center, duration=0.3)
                pyautogui.click()
                time.sleep(0.3)
                
                # Select all text in the focused element (Ctrl+A)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Copy selected text to clipboard (Ctrl+C)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                # Retrieve text from clipboard
                extracted_text = pyperclip.paste()
                
                # Return the extracted text
                return extracted_text

            Common Error Fixes to Consider:
            - **KeyError**: Ensure `element_name` exists in JSON; add proper error handling
            - **TypeError (coordinate unpacking)**: Validate coordinates are a list/tuple of 2 integers
            - **pyautogui.FailSafeException**: Add try-except blocks or disable failsafe if appropriate
            - **Empty clipboard**: Increase sleep delays, verify element is focusable, try alternative selection methods
            - **Import errors**: Ensure all required packages (pyautogui, pyperclip) are imported
            - **File not found**: Check JSON path exists before opening
            - **Attribute errors**: Validate JSON structure and data types before accessing

            Notes / Constraints:
            - Analyze the error in {{error_detail}} and ensure the corrected code addresses the root cause
            - The coordinate order is always [x_axis, y_axis]
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
            ✅ Correct: x_center, y_center = coordinates_points
            ❌ Incorrect: left, right, top, bottom = coordinates_points
            - The pattern for retrieving coordinates must be exactly:
            element_name = {{var_name}}
            coordinates_points = json_info.get(element_name)
            - The function MUST return the extracted text as a string
            - Use `pyperclip` for reliable clipboard operations
            - Include appropriate sleep delays to ensure UI actions complete
            - Add robust error handling based on the previous error
            - Keep the function self-contained and robust
            - Do not send any additional explanation or console text beyond the function definition itself
            """


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language - ALWAYS about extracting text from a UI element (e.g., "extract OTP from field", "get text from label", "read value from screen").
            - error_code: The previously generated Python code that encountered an error (string).
            - error_detail: The exception or error message that occurred when executing the code (string).
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code that extracts text from the UI element.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected Python Citrix automation function using pyautogui and pytesseract packages to extract text from the UI element identified by the image, and fix the error that occurred.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            element_name = {var_name}
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[element_name]}}"

            4. Use pyautogui.locateOnScreen(image_path, confidence=confidence) to find the element on screen.
            5. Take a screenshot of the located region using pyautogui.screenshot().
            6. Use pytesseract.image_to_string() to extract text from the screenshot.
            7. Clean and return the extracted text as a string.
            8. **CRITICAL**: Address and fix the specific error from {error_detail}. Analyze the root cause and implement a robust solution.
            9. Include proper error handling for:
            - Image not found on screen
            - OCR extraction failures
            - Empty or invalid text extraction
            - JSON file or key errors
            10. Do NOT include click or typing logic - only text extraction.
            11. Return the extracted text string, or None if extraction fails.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver=None):
                import json
                import time
                import pyautogui
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_info = json.load(f)
                except FileNotFoundError:
                    print(f"JSON file not found: {{json_path}}")
                    return None
                except json.JSONDecodeError:
                    print(f"Invalid JSON format in: {{json_path}}")
                    return None
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return None
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                confidence = 0.8
                
                time.sleep(1)
                
                # Locate the element on screen
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                except Exception as e:
                    print(f"Error locating image: {{e}}")
                    return None
                
                if location is None:
                    print("Image not found on screen!")
                    return None
                
                # Take screenshot of the located region
                try:
                    screenshot = pyautogui.screenshot(region=location)
                except Exception as e:
                    print(f"Error capturing screenshot: {{e}}")
                    return None
                
                # Extract text using OCR
                try:
                    extracted_text = pytesseract.image_to_string(screenshot)
                    extracted_text = extracted_text.strip()
                    
                    if not extracted_text:
                        print("No text could be extracted from the region")
                        return None
                    
                    return extracted_text
                    
                except Exception as e:
                    print(f"OCR extraction failed: {{e}}")
                    return None

            Common Error Fixes to Consider:
            - **FileNotFoundError**: Add try-except for JSON file loading; verify path exists
            - **KeyError**: Check if element_name exists in json_info before accessing; use .get() method
            - **pyautogui.ImageNotFoundException**: Handle case when image not found on screen; adjust confidence level
            - **pytesseract.TesseractNotFoundError**: Ensure Tesseract-OCR is installed; provide installation guidance in error message
            - **TypeError**: Validate location is not None before using it; check screenshot region validity
            - **AttributeError**: Ensure PIL Image object is valid before OCR; handle empty screenshots
            - **PermissionError**: Check file permissions for JSON and image files
            - **ValueError**: Validate confidence value is between 0 and 1
            - **Empty text extraction**: Try different OCR configurations (psm modes, preprocessing)

            Notes / Constraints:
            - **CRITICAL**: Analyze the error in {error_detail} carefully and ensure the corrected code addresses the root cause
            - Ensure `element_name = {var_name}` is assigned before accessing json_info
            - Use `json_info.get(element_name)` instead of `json_info[element_name]` to avoid KeyError
            - Add comprehensive try-except blocks for all potential failure points
            - The function always returns extracted text as a string, or None on failure
            - Uses pytesseract for OCR (Optical Character Recognition)
            - Captures only the region where the element is located for better accuracy
            - The confidence parameter (default 0.8) can be adjusted if image matching fails
            - Do not generate click, type, or any other action code - only text extraction
            - If the previous error was related to missing imports, ensure all required packages are imported
            - If the previous error was related to timing, add appropriate sleep delays
            - Keep the function self-contained and robust
            - Do not send any additional explanation or console text beyond the function definition itself
            """
    elif region_status and not co_ordinates_status and not img_status:
        prompt = f""""""
    else:
        prompt = f"""
            Generate a **final Selenium-based Python automation code** for the following user requirement.

            ===============================================================================
            🧠 USER REQUIREMENT
            ===============================================================================
            {desc}

            **Note**: The user requirement is ALWAYS about extracting text from a web element and returning it as a string.

            ===============================================================================
            ❌ PREVIOUS CODE & ERROR INFORMATION
            ===============================================================================
            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            **Task**: Analyze the error and generate corrected code that fixes the issue and successfully extracts text from the element.

            ===============================================================================
            🔍 PROVIDED ELEMENT INFORMATION (REFERENCE ONLY)
            ===============================================================================
            - XPath of the element (use EXACTLY this, do NOT modify): {xpath}
            - Outer HTML (context only): {outer_html}
            - Full Page HTML (context only): {html_content}
            - Variable name: {var_name}

            **Note**: These are provided for context to help you understand the element structure.
            The XPath must be loaded dynamically from JSON (see below). The outer HTML and full page HTML
            help you understand element type, attributes, and page structure to generate correct text extraction logic.

            ===============================================================================
            🎯 PRIMARY OBJECTIVE
            ===============================================================================
            Generate **corrected, runnable Selenium + Python code** that:
            - **CRITICAL**: Fixes the error from {error_detail}
            - Uses the provided `driver`
            - Loads the XPath dynamically from JSON (never hardcodes it)
            - Extracts text from the located element
            - Returns the extracted text as a string
            - Does NOT create, modify, or alter any XPath
            - Must load the XPath dynamically from the JSON file using the exact pattern below:

                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]

            Always use the `xpath` variable for locating elements. Never hardcode any XPath.

            ===============================================================================
            🧩 TEXT EXTRACTION RULES
            ===============================================================================
            The user requirement is ALWAYS about extracting text from a web element.

            Implementation steps:
            1. Load XPath from JSON file using the pattern above
            2. Locate the element using WebDriverWait with the loaded XPath
            3. Extract text using the appropriate method based on element type:
            - Regular elements: Use `element.text`
            - Input/textarea fields: Use `element.get_attribute("value")`
            - Hidden/whitespace text: Use `element.get_attribute("textContent")` or `element.get_attribute("innerText")`
            - If `.text` returns empty, try `get_attribute("textContent")`, then `get_attribute("innerText")`, then `get_attribute("value")`
            4. Clean and strip the extracted text
            5. Return the text as a string

            For different element types (use outer HTML as reference):
            - `<input>`, `<textarea>`: Use `.get_attribute("value")`
            - `<div>`, `<span>`, `<p>`, `<label>`: Use `.text` first, fallback to `.get_attribute("textContent")`
            - `<button>`: Use `.text`
            - `<select>`: Use `Select(element).first_selected_option.text`
            - Hidden elements: Use `.get_attribute("textContent")` or `.get_attribute("innerText")`

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. The function name must be exactly `run(driver)`.
            2. Load XPath using this exact pattern:
                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                xpath = xpath_json[element_name]

            3. Do NOT hardcode the XPath anywhere in the code.
            4. Required imports (must be inside the function):
                import json  # MANDATORY
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

            5. Use WebDriverWait to ensure element is present before extraction
            6. **CRITICAL**: Return the extracted text - do NOT print it
            7. Handle errors gracefully (return empty string or None on failure)
            8. **CRITICAL**: Address the specific error from {error_detail} - analyze what went wrong and fix it
            9. Avoid any explanation, markdown, or comments — output must be valid runnable Python

            ===============================================================================
            🔧 COMMON ERROR FIXES TO CONSIDER
            ===============================================================================
            Based on the error in {error_detail}, consider these common issues:

            - **KeyError / 'element_name' not found**: 
            - Ensure element_name is assigned before accessing xpath_json
            - Use xpath_json.get(element_name) with a default value
            
            - **NoSuchElementException / TimeoutException**:
            - Increase WebDriverWait timeout
            - Verify XPath is correct and element exists
            - Wait for element to be visible/clickable, not just present
            
            - **StaleElementReferenceException**:
            - Re-locate the element after page changes
            - Add explicit waits before accessing element
            
            - **Empty text returned**:
            - Try multiple extraction methods (.text, textContent, innerText, value)
            - Check if element is hidden or has CSS visibility issues
            - Use get_attribute for input fields
            
            - **AttributeError**:
            - Verify element is found before calling methods
            - Check if element is None
            
            - **TypeError**:
            - Validate data types before operations
            - Ensure extracted text is string type
            
            - **FileNotFoundError**:
            - Verify JSON file path exists
            - Add try-except for file operations
            
            - **IndexError / List index out of range**:
            - Validate list/collection is not empty before accessing
            - Use proper bounds checking

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            def run(driver):
                import json
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]
                
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    
                    # Extract text based on element type
                    extracted_text = element.text.strip()
                    
                    # Fallback for empty text
                    if not extracted_text:
                        extracted_text = element.get_attribute("textContent")
                        if extracted_text:
                            extracted_text = extracted_text.strip()
                    
                    # Fallback for input fields
                    if not extracted_text:
                        extracted_text = element.get_attribute("value")
                        if extracted_text:
                            extracted_text = extracted_text.strip()
                    
                    # Fallback for innerText
                    if not extracted_text:
                        extracted_text = element.get_attribute("innerText")
                        if extracted_text:
                            extracted_text = extracted_text.strip()
                    
                    return extracted_text if extracted_text else ""
                    
                except Exception as e:
                    print(f"Error extracting text: {{e}}")
                    return ""

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run(driver)` function block
            - The import statement `import json` is mandatory and must always be included
            - **CRITICAL**: Analyze the error from {error_detail} and ensure the corrected code addresses the root cause
            - Use the outer HTML ({outer_html}) and full page HTML ({html_content}) as reference to understand:
                * Element type (input, select, div, button, span, etc.)
                * Element attributes (class, id, name, value, etc.)
                * Whether text is in .text property or attributes
                * If element might be hidden or have special rendering
            - For any actions involving table extraction, if pagination is present, you must extract all data from all pages refer the Outer HTML  
            - The current element XPath ({xpath}) should guide you on element location strategy
            - The function MUST return the extracted text as a string
            - Try multiple text extraction methods (.text, textContent, innerText, value) for robustness
            - Handle exceptions and return empty string on failure
            - Do NOT include any click, type, select, or other actions - ONLY text extraction
            - Focus on fixing the specific error while maintaining text extraction functionality

            ===============================================================================
            💬 EXAMPLES OF USER REQUIREMENTS (ALL ABOUT TEXT EXTRACTION)
            ===============================================================================
            - "extract text from the label"
            - "get value from the input field"
            - "read text from the div element"
            - "fetch content from the span"
            - "retrieve text from the button"
            - "extract OTP from the code field"
            - "get username from the profile section"
            - "read error message from alert"
            ===============================================================================
            """



    if not region_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""
import pandas as pd
import json
from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
def run(driver=None):
    desc="{desc}"
    json_path = "json_info/json_xpath.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    bound_index=json_info["{var_name}"]
    img_path=capture_region(bound_index)
    text=gemini_image_response(img_path,desc)
    return text
        """

    # Remove markdown code block markers
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()
    write_code(file_path,code_to_write)
    return code_to_write

def code_correction_element_exist(desc,xpath,file_path,var_name,driver,userid):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run(driver)` that extracts text from the UI element at the specified coordinates and returns it.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
            3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{{var_name}}` key.
            5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
            6. Use `pyautogui` and `pyperclip` to:
            - Click on the element at the specified coordinates
            - Select the text (using appropriate keyboard shortcuts like Ctrl+A or triple-click)
            - Copy the text to clipboard (Ctrl+C)
            - Retrieve the text from clipboard using `pyperclip.paste()`
            - Return the extracted text as a string
            7. Include concise inline comments explaining key steps, imports, and assumptions.
            8. The function MUST return the extracted text as a string.
            9. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {{desc}} → will be replaced with the user's action description (always about extracting text from a UI element).
            - {{var_name}} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern exactly):

            def run(driver):
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Silence unused parameter
                _ = driver
                
                # Define JSON file path
                json_path = "json_info/json_xpath.json"
                
                # Validate JSON file existence
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"JSON file not found: {{json_path}}")
                
                # Load coordinate data from JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                # Retrieve coordinates using the provided key
                element_name = {{var_name}}
                coordinates_points = json_info.get(element_name)
                
                # Validate coordinate format
                if not isinstance(coordinates_points, (list, tuple)) or len(coordinates_points) != 2:
                    raise ValueError(f"Expected coordinate_index as a list of 2 integers for key: {{element_name}}")
                
                # Extract x and y coordinates
                x_center, y_center = map(int, coordinates_points)
                
                # Clear clipboard before operation
                pyperclip.copy("")
                
                # Move to the element and click to focus
                time.sleep(0.5)
                pyautogui.moveTo(x_center, y_center, duration=0.3)
                pyautogui.click()
                time.sleep(0.3)
                
                # Select all text in the focused element (Ctrl+A)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Copy selected text to clipboard (Ctrl+C)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                # Retrieve text from clipboard
                extracted_text = pyperclip.paste()
                
                # Return the extracted text
                return extracted_text

            Notes / Constraints:
            - The coordinate order is always [x_axis, y_axis].
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
            ✅ Correct: x_center, y_center = coordinates
            ❌ Incorrect: left, right, top, bottom = coordinates
            - The pattern for retrieving coordinates must be exactly:
            element_name = {{var_name}}
            coordinates_points = json_info.get(element_name)
            - The function MUST return the extracted text as a string.
            - Use `pyperclip` for reliable clipboard operations.
            - Include appropriate sleep delays to ensure UI actions complete.
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
            """


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "check if element exists", "verify button is present", "validate field visibility").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python Citrix automation function using pyautogui package to check if a UI element exists on screen.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver` as parameter: def run(driver):
            3. All code logic must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[{var_name}]}}"

            5. Use pyautogui.locateOnScreen(image_path, confidence=confidence) to find the element on screen.
            6. Return True if the element is found on screen.
            7. Return False if the element is not found on screen.
            8. Include proper error handling for:
            - Image file not found in JSON
            - Image file path errors
            - Screen location failures
            9. Do NOT include click, typing, or OCR logic - only element existence check.
            10. Return boolean value: True if element exists, False if it doesn't.
            11. All imports and logic must be inside the run function body.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver):
                import json
                import time
                import pyautogui
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_info = json.load(f)
                except Exception as e:
                    print(f"Error loading JSON file: {{e}}")
                    return False
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return False
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                confidence = 0.8
                
                time.sleep(1)
                
                # Check if the element exists on screen
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                    
                    if location is None:
                        print("Element not found on screen")
                        return False
                    
                    print("Element found on screen")
                    return True
                    
                except Exception as e:
                    print(f"Error checking element existence: {{e}}")
                    return False

            Notes:
            - The function signature must be: def run(driver):
            - All imports must be inside the run function.
            - All code logic must be inside the run function body.
            - The function always returns a boolean value: True or False.
            - Returns True if the element image is found on screen.
            - Returns False if the element image is not found or any error occurs.
            - Uses pyautogui.locateOnScreen() for image matching.
            - The confidence parameter (default 0.8) can be adjusted if needed.
            - Do not generate click, type, OCR, or any other action code - only existence check.
            - Simple and efficient for element validation in automation workflows.
            """

    elif region_status and not co_ordinates_status and not img_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            bound_index = json_info[{var_name}]
            4. Extract coordinates from bound_index as [left, top, right, bottom] format.
            5. ALWAYS take a LIVE screenshot of the specified region from the current screen using pyautogui.screenshot().
            6. CRITICAL: Save the captured region screenshot temporarily and use pyautogui.locateOnScreen() to find the exact location of the captured image on screen.
            7. NEVER directly use calculated coordinates (center_x, center_y) for clicking. ALWAYS locate the image on screen first.
            8. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), capture the region, locate it on screen using the captured image, then click.
            - If the description implies a typing action (e.g., "type username as www"), locate the region image on screen, click it, then type text.
            - If the description implies a text/table extraction action (e.g., "extract OTP", "extract table data"), capture the region live and use OCR to extract text.
            - If the description mentions scrolling (e.g., "scroll down", "scroll in table"), locate the region image and scroll within it.
            - If the description mentions hover (e.g., "hover over element"), locate the region image and move mouse to its center.
            - If the description mentions double-click, locate the region image and perform double-click.
            - If the description mentions right-click, locate the region image and perform right-click.
            - If the description mentions drag (e.g., "drag element"), locate the region image and perform drag operation.
            9. Do not use the description: {desc} directly in the code. Create preferred logic by analyzing the description.
            10. For all click-based actions, the workflow must be: Capture region → Save as temp image → Locate image on screen → Click the located position.
            11. For typing actions, extract the text to be typed from the description (e.g., "type username as admin" → type "admin").
            12. For extraction actions, return the extracted text as the function output.
            13. Include proper error handling (e.g., invalid coordinates, screenshot failure, image not found on screen, OCR failure).
            14. Add appropriate time.sleep() delays between actions for stability.
            15. Use confidence parameter (0.8 or 0.9) for image matching to handle minor variations.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for region click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for text/table extraction action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    extracted_text = pytesseract.image_to_string(region_screenshot).strip()
                    print(f"Extracted text: {{extracted_text}}")
                    return extracted_text if extracted_text else ""
                except Exception as e:
                    print(f"Error: {{e}}")
                    return ""

            Example reference (for typing action with text extraction from description):

            def run(driver=None):
                import json
                import time
                import pyautogui
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    time.sleep(0.3)
                    
                    pyautogui.typewrite("text_here", interval=0.1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for double-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.doubleClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for scroll action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.scroll(-3)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for hover action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for right-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    temp_image_path = "temp_region.png"
                    region_screenshot.save(temp_image_path)
                    
                    time.sleep(0.3)
                    location = pyautogui.locateOnScreen(temp_image_path, confidence=0.8)
                    
                    if location is None:
                        print("Image not found on screen!")
                        return False
                    
                    center_x, center_y = pyautogui.center(location)
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.rightClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False
            """
    else:
        prompt = f"""
            Generate a **final Selenium-based Python automation code** for the following user requirement.

            ===============================================================================
            🧠 USER REQUIREMENT
            ===============================================================================
            {desc}s

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
            Generate **runnable Selenium + Python code** that:
            - Uses the provided `driver`
            - Loads the XPath dynamically from JSON using the exact pattern below
            - Checks if the element exists on the page
            - Returns True if element exists, False if it doesn't

            CRITICAL: Must load the XPath dynamically from the JSON file using this exact pattern:

                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]

            Always use the `xpath` variable for locating elements. Never hardcode any XPath.

            ===============================================================================
            🧩 ELEMENT EXISTS CHECK RULES
            ===============================================================================
            The user requirement is about checking if an element exists on the page.

            Implementation steps:
            1. Load XPath from JSON file using the pattern above
            2. Try to locate the element using WebDriverWait with the loaded XPath
            3. If element is found, return True
            4. If element is not found (timeout or not present), return False
            5. Handle all exceptions and return False on any error

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. The function name must be exactly `run(driver)`.
            2. Load XPath using this exact pattern:
                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                xpath = xpath_json[element_name]

            3. Do NOT hardcode the XPath anywhere in the code.
            4. Required imports (must be inside the function):
                import json  # MANDATORY
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException

            5. Use WebDriverWait to check if element is present
            6. Return boolean value: True if exists, False if not
            7. Handle all exceptions gracefully (return False on any error)
            8. Avoid any explanation, markdown, or comments — output must be valid runnable Python

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            def run(driver):
                import json
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException
                
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                
                try:
                    with open(json_path, "r") as f:
                        xpath_json = json.load(f)
                except Exception as e:
                    print(f"Error loading JSON file: {{e}}")
                    return False
                
                xpath = xpath_json.get(element_name)
                
                if not xpath:
                    print(f"XPath for '{{element_name}}' not found in JSON")
                    return False
                
                try:
                    element = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    
                    if element:
                        print("Element found on page")
                        return True
                    else:
                        print("Element not found on page")
                        return False
                    
                except (TimeoutException, NoSuchElementException) as e:
                    print(f"Element not found: {{e}}")
                    return False
                    
                except Exception as e:
                    print(f"Error checking element existence: {{e}}")
                    return False

            MANDATORY CONDITION :
            - It must return a boolean value (True or False) compulsory
            - Return True if element exists
            - Return False if element does not exist or any error occurs

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run(driver)` function block
            - The import statement `import json` is mandatory and must always be included
            - The function must RETURN boolean (True/False), not print it
            - Use WebDriverWait with appropriate timeout (10 seconds recommended)
            - Handle TimeoutException and NoSuchElementException specifically
            - Return False for any exceptions or errors

            ===============================================================================
            💬 EXAMPLES OF USER REQUIREMENTS (ALL ABOUT ELEMENT EXISTS CHECK)
            ===============================================================================
            - "check if element exists"
            - "verify button is present"
            - "validate field visibility"
            - "check if login button is available"
            - "verify element is on the page"
            - "check element presence"
            - "validate element exists on screen"
            ===============================================================================
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

def fallback_code_correction_element_exist(desc,xpath,file_path,var_name,driver,userid,error_info):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    error_code=error_info["code"]
    error_file=error_info["file"]
    error_detail=error_info["error"]
    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string) - ALWAYS about extracting text from a UI element.
            - error_code: the previously generated Python code that encountered an error (string).
            - error_detail: the exception or error message that occurred when executing the code (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code that extracts text from the UI element.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected, single, valid Python function definition named `run(driver)` that fixes the error and extracts text from the UI element at the specified coordinates, returning the extracted text as a string.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run(driver):` and its body. Do NOT include any function calls, test examples, or extra output.
            3. The `driver` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_xpath.json"` using the provided `{var_name}` key.
            5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
            6. Use `pyautogui` and `pyperclip` to:
            - Click on the element at the specified coordinates
            - Select the text (using appropriate keyboard shortcuts like Ctrl+A or triple-click)
            - Copy the text to clipboard (Ctrl+C)
            - Retrieve the text from clipboard using `pyperclip.paste()`
            - Return the extracted text as a string
            7. Include concise inline comments explaining key steps, imports, and assumptions.
            8. **CRITICAL**: Address and fix the specific error from `{error_detail}`. Analyze the root cause and implement a robust solution.
            9. The function MUST return the extracted text as a string.
            10. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {{desc}} → the user's action description (always about text extraction).
            - {{error_code}} → the previous code that failed.
            - {{error_detail}} → the error message to be fixed.
            - {{var_name}} → the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic to fix the error):

            def run(driver):
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Silence unused parameter
                _ = driver
                
                # Define JSON file path
                json_path = "json_info/json_xpath.json"
                
                # Validate JSON file existence
                if not os.path.exists(json_path):
                    raise FileNotFoundError(f"JSON file not found: {{json_path}}")
                
                # Load coordinate data from JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                
                # Retrieve coordinates using the provided key
                element_name = {{var_name}}
                coordinates_points = json_info.get(element_name)
                
                # Validate coordinate format
                if not isinstance(coordinates_points, (list, tuple)) or len(coordinates_points) != 2:
                    raise ValueError(f"Expected coordinate_index as a list of 2 integers for key: {{element_name}}")
                
                # Extract x and y coordinates
                x_center, y_center = map(int, coordinates_points)
                
                # Clear clipboard before operation
                pyperclip.copy("")
                
                # Move to the element and click to focus
                time.sleep(0.5)
                pyautogui.moveTo(x_center, y_center, duration=0.3)
                pyautogui.click()
                time.sleep(0.3)
                
                # Select all text in the focused element (Ctrl+A)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Copy selected text to clipboard (Ctrl+C)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                # Retrieve text from clipboard
                extracted_text = pyperclip.paste()
                
                # Return the extracted text
                return extracted_text

            Common Error Fixes to Consider:
            - **KeyError**: Ensure `element_name` exists in JSON; add proper error handling
            - **TypeError (coordinate unpacking)**: Validate coordinates are a list/tuple of 2 integers
            - **pyautogui.FailSafeException**: Add try-except blocks or disable failsafe if appropriate
            - **Empty clipboard**: Increase sleep delays, verify element is focusable, try alternative selection methods
            - **Import errors**: Ensure all required packages (pyautogui, pyperclip) are imported
            - **File not found**: Check JSON path exists before opening
            - **Attribute errors**: Validate JSON structure and data types before accessing

            Notes / Constraints:
            - Analyze the error in {{error_detail}} and ensure the corrected code addresses the root cause
            - The coordinate order is always [x_axis, y_axis]
            - Do NOT calculate centers from bounding boxes — use the coordinates directly:
            ✅ Correct: x_center, y_center = coordinates_points
            ❌ Incorrect: left, right, top, bottom = coordinates_points
            - The pattern for retrieving coordinates must be exactly:
            element_name = {{var_name}}
            coordinates_points = json_info.get(element_name)
            - The function MUST return the extracted text as a string
            - Use `pyperclip` for reliable clipboard operations
            - Include appropriate sleep delays to ensure UI actions complete
            - Add robust error handling based on the previous error
            - Keep the function self-contained and robust
            - Do not send any additional explanation or console text beyond the function definition itself
            """


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language - ALWAYS about checking if a UI element exists (e.g., "check if element exists", "verify button is present", "validate field visibility").
            - error_code: The previously generated Python code that encountered an error (string).
            - error_detail: The exception or error message that occurred when executing the code (string).
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code that checks if the UI element exists on screen.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected Python Citrix automation function using pyautogui package to check if a UI element exists on screen, and fix the error that occurred.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver` as parameter: def run(driver):
            3. All code logic and imports must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            element_name = {var_name}
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[element_name]}}"

            5. Use pyautogui.locateOnScreen(image_path, confidence=confidence) to find the element on screen.
            6. Return True if the element is found on screen.
            7. Return False if the element is not found on screen.
            8. **CRITICAL**: Address and fix the specific error from {error_detail}. Analyze the root cause and implement a robust solution.
            9. Include proper error handling for:
            - Image file not found in JSON
            - JSON file or key errors
            - Image file path errors
            - Screen location failures
            - Any other exceptions
            10. Do NOT include click, typing, or OCR logic - only element existence check.
            11. Return boolean value: True if element exists, False if it doesn't.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver):
                import json
                import time
                import pyautogui
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_info = json.load(f)
                except FileNotFoundError:
                    print(f"JSON file not found: {{json_path}}")
                    return False
                except json.JSONDecodeError:
                    print(f"Invalid JSON format in: {{json_path}}")
                    return False
                except Exception as e:
                    print(f"Error loading JSON: {{e}}")
                    return False
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return False
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                confidence = 0.8
                
                time.sleep(1)
                
                # Check if the element exists on screen
                try:
                    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                    
                    if location is None:
                        print("Element not found on screen")
                        return False
                    
                    print("Element found on screen")
                    return True
                    
                except FileNotFoundError:
                    print(f"Image file not found: {{image_path}}")
                    return False
                except Exception as e:
                    print(f"Error checking element existence: {{e}}")
                    return False

            Common Error Fixes to Consider:
            - **FileNotFoundError**: Add try-except for JSON and image file loading; verify paths exist
            - **KeyError**: Check if element_name exists in json_info before accessing; use .get() method
            - **pyautogui.ImageNotFoundException**: Handle case when image not found on screen; adjust confidence level
            - **TypeError**: Validate location is not None before using it
            - **AttributeError**: Ensure all objects are properly initialized
            - **PermissionError**: Check file permissions for JSON and image files
            - **ValueError**: Validate confidence value is between 0 and 1
            - **OSError**: Handle file system errors gracefully
            - **ImportError**: Ensure all required packages are imported inside the function
            - **NameError**: Ensure all variables are defined before use
            - **Timeout issues**: Add appropriate sleep delays if needed
            - **Path issues**: Verify the image path construction is correct

            Notes / Constraints:
            - **CRITICAL**: Analyze the error in {error_detail} carefully and ensure the corrected code addresses the root cause
            - The function signature must be: def run(driver):
            - All imports must be inside the run function
            - All code logic must be inside the run function body
            - Ensure `element_name = {var_name}` is assigned before accessing json_info
            - Use `json_info.get(element_name)` instead of `json_info[element_name]` to avoid KeyError
            - Add comprehensive try-except blocks for all potential failure points
            - The function always returns a boolean value: True or False
            - Returns True if the element image is found on screen
            - Returns False if the element image is not found or any error occurs
            - Uses pyautogui.locateOnScreen() for image matching
            - The confidence parameter (default 0.8) can be adjusted if image matching fails
            - Do not generate click, type, OCR, or any other action code - only existence check
            - If the previous error was related to missing imports, ensure all required packages are imported inside the function
            - If the previous error was related to timing, add appropriate sleep delays
            - If the previous error was related to file paths, add validation for file existence
            - Keep the function self-contained and robust
            - Simple and efficient for element validation in automation workflows
            - Do not send any additional explanation or console text beyond the function definition itself
            """
    elif region_status and not co_ordinates_status and not img_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            ===============================================================================
            ❌ PREVIOUS CODE & ERROR INFORMATION
            ===============================================================================
            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            **Task**: Analyze the error and generate corrected code that fixes the issue. DO NOT repeat the same error. Study the error carefully and implement the proper fix.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver=None` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            bound_index = json_info[{var_name}]
            4. Extract coordinates from bound_index as [left, top, right, bottom] format.
            5. ALWAYS take a LIVE screenshot of the specified region from the current screen using pyautogui.screenshot().
            6. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
            - If the description implies a click (e.g., "click login button"), capture the region live and click the center.
            - If the description implies a typing action (e.g., "type username as www"), click the region center and type text.
            - If the description implies a text/table extraction action (e.g., "extract OTP", "extract table data"), capture the region live and use OCR to extract text.
            - If the description mentions scrolling (e.g., "scroll down", "scroll in table"), perform scroll actions within the region.
            - If the description mentions hover (e.g., "hover over element"), move mouse to the region center without clicking.
            - If the description mentions double-click, perform double-click at the region center.
            - If the description mentions right-click, perform right-click at the region center.
            - If the description mentions drag (e.g., "drag element"), perform drag operation from region center.
            7. Do not use the description: {desc} directly in the code. Create preferred logic by analyzing the description.
            8. For all actions, ALWAYS capture the live region first using the bounding box coordinates.
            9. For typing actions, extract the text to be typed from the description (e.g., "type username as admin" → type "admin").
            10. For extraction actions, return the extracted text as the function output.
            11. Include proper error handling (e.g., invalid coordinates, screenshot failure, OCR failure).
            12. Add appropriate time.sleep() delays between actions for stability.
            13. CRITICAL: If there was a previous error, carefully analyze it and fix the issue. Common errors to avoid:
                - ImportError: Ensure all required modules are imported (json, time, pyautogui, PIL, pytesseract)
                - KeyError: Validate that the var_name exists in json_info before accessing
                - ValueError: Check that bound_index has exactly 4 values before unpacking
                - TypeError: Ensure correct data types (integers for coordinates, strings for text)
                - AttributeError: Verify objects have the methods/attributes being called
                - IndexError: Validate list/array indices before accessing
                - NameError: Check all variables are defined before use
                - SyntaxError: Fix any syntax issues like missing colons, brackets, or quotes
            14. DO NOT repeat the same error from the previous code. Implement a different approach if needed.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference (for region click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for text/table extraction action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    extracted_text = pytesseract.image_to_string(region_screenshot).strip()
                    print(f"Extracted text: {{extracted_text}}")
                    return extracted_text
                except Exception as e:
                    print(f"Error: {{e}}")
                    return None

            Example reference (for typing action with text extraction from description):

            def run(driver=None):
                import json
                import time
                import pyautogui
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.click()
                    time.sleep(0.3)
                    
                    pyautogui.typewrite("text_here", interval=0.1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for double-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.doubleClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for scroll action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.scroll(-3)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for hover action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False

            Example reference (for right-click action):

            def run(driver=None):
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/json_xpath.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                bound_index = json_info[{var_name}]
                
                try:
                    left, top, right, bottom = bound_index
                    width = right - left
                    height = bottom - top
                    
                    time.sleep(0.5)
                    region_screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.2)
                    pyautogui.rightClick()
                    return True
                except Exception as e:
                    print(f"Error: {{e}}")
                    return False
            """
    else:
        prompt = f"""
            Generate a **final Selenium-based Python automation code** for the following user requirement.

            ===============================================================================
            🧠 USER REQUIREMENT
            ===============================================================================
            {desc}

            **Note**: The user requirement is ALWAYS about checking if a web element exists on the page and returning a boolean value.

            ===============================================================================
            ❌ PREVIOUS CODE & ERROR INFORMATION
            ===============================================================================
            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            **Task**: Analyze the error and generate corrected code that fixes the issue and successfully checks if the element exists on the page.

            ===============================================================================
            🔍 PROVIDED ELEMENT INFORMATION (REFERENCE ONLY)
            ===============================================================================
            - XPath of the element (use EXACTLY this, do NOT modify): {xpath}
            - Outer HTML (context only): {outer_html}
            - Full Page HTML (context only): {html_content}
            - Variable name: {var_name}

            **Note**: These are provided for context to help you understand the element structure.
            The XPath must be loaded dynamically from JSON (see below). The outer HTML and full page HTML
            help you understand element type, attributes, and page structure to generate correct element existence check logic.

            ===============================================================================
            🎯 PRIMARY OBJECTIVE
            ===============================================================================
            Generate **corrected, runnable Selenium + Python code** that:
            - **CRITICAL**: Fixes the error from {error_detail}
            - Uses the provided `driver`
            - Loads the XPath dynamically from JSON (never hardcodes it)
            - Checks if the element exists on the page
            - Returns True if element exists, False if it doesn't
            - Does NOT create, modify, or alter any XPath
            - Must load the XPath dynamically from the JSON file using the exact pattern below:

                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]

            Always use the `xpath` variable for locating elements. Never hardcode any XPath.

            ===============================================================================
            🧩 ELEMENT EXISTS CHECK RULES
            ===============================================================================
            The user requirement is ALWAYS about checking if an element exists on the page.

            Implementation steps:
            1. Load XPath from JSON file using the pattern above
            2. Try to locate the element using WebDriverWait with the loaded XPath
            3. If element is found (no exception), return True
            4. If element is not found (TimeoutException or NoSuchElementException), return False
            5. Handle all exceptions gracefully and return False on any error

            Element existence strategies:
            - Use `EC.presence_of_element_located` to check if element exists in DOM
            - Use `EC.visibility_of_element_located` to check if element is visible
            - Set appropriate timeout (recommended: 10 seconds)
            - Catch `TimeoutException` when element is not found
            - Return boolean value based on element presence

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. The function name must be exactly `run(driver)`.
            2. Load XPath using this exact pattern:
                import json
                json_path = "json_info/json_xpath.json"
                element_name = {var_name}
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                xpath = xpath_json[element_name]

            3. Do NOT hardcode the XPath anywhere in the code.
            4. Required imports (must be inside the function):
                import json  # MANDATORY
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException

            5. Use WebDriverWait to check if element is present
            6. **CRITICAL**: Return boolean value (True/False) - do NOT print it
            7. Handle errors gracefully (return False on any failure)
            8. **CRITICAL**: Address the specific error from {error_detail} - analyze what went wrong and fix it
            9. Avoid any explanation, markdown, or comments — output must be valid runnable Python

            ===============================================================================
            🔧 COMMON ERROR FIXES TO CONSIDER
            ===============================================================================
            Based on the error in {error_detail}, consider these common issues:

            - **KeyError / 'element_name' not found**: 
            - Ensure element_name is assigned before accessing xpath_json
            - Use xpath_json.get(element_name) with a default value
            - Add validation to check if element_name exists in JSON
            
            - **NoSuchElementException / TimeoutException**:
            - This is EXPECTED when element doesn't exist - catch it and return False
            - Don't treat this as an error - it's the normal flow for "element not found"
            - Increase timeout if needed for slow-loading pages
            
            - **StaleElementReferenceException**:
            - Re-locate the element after page changes
            - Add explicit waits before checking element
            
            - **AttributeError**:
            - Verify element is found before calling methods
            - Check if element is None before operations
            
            - **TypeError**:
            - Validate data types before operations
            - Ensure proper boolean return type
            
            - **FileNotFoundError**:
            - Verify JSON file path exists
            - Add try-except for file operations
            - Return False if JSON file is missing
            
            - **IndexError / List index out of range**:
            - Validate list/collection is not empty before accessing
            - Use proper bounds checking
            
            - **ImportError / ModuleNotFoundError**:
            - Ensure all imports are inside the function
            - Verify Selenium is properly installed
            
            - **WebDriverException**:
            - Check if driver is valid and browser is running
            - Add error handling for driver issues

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            def run(driver):
                import json
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException
                
                json_path = "json_info/json_xpath.json"
                element_name = "{var_name}"
                
                try:
                    with open(json_path, "r") as f:
                        xpath_json = json.load(f)
                except FileNotFoundError:
                    print(f"JSON file not found: {{json_path}}")
                    return False
                except json.JSONDecodeError:
                    print(f"Invalid JSON format in: {{json_path}}")
                    return False
                except Exception as e:
                    print(f"Error loading JSON: {{e}}")
                    return False
                
                xpath = xpath_json.get(element_name)
                
                if not xpath:
                    print(f"XPath for '{{element_name}}' not found in JSON")
                    return False
                
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    
                    if element:
                        print("Element found on page")
                        return True
                    else:
                        print("Element not found on page")
                        return False
                    
                except (TimeoutException, NoSuchElementException) as e:
                    print(f"Element not found: {{e}}")
                    return False
                    
                except Exception as e:
                    print(f"Error checking element existence: {{e}}")
                    return False

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run(driver)` function block
            - The import statement `import json` is mandatory and must always be included
            - **CRITICAL**: Analyze the error from {error_detail} and ensure the corrected code addresses the root cause
            - Use the outer HTML ({outer_html}) and full page HTML ({html_content}) as reference to understand:
                * Element type and structure
                * Element attributes (class, id, name, etc.)
                * Whether element might be dynamically loaded
                * If element might be hidden or have special rendering
            - The current element XPath ({xpath}) should guide you on element location strategy
            - The function MUST return a boolean value (True or False)
            - Return True if element exists on the page
            - Return False if element does not exist or any error occurs
            - Handle TimeoutException and NoSuchElementException specifically - these are expected for non-existent elements
            - Use WebDriverWait with appropriate timeout (10 seconds recommended)
            - Do NOT include any click, type, select, text extraction, or other actions - ONLY existence check
            - Focus on fixing the specific error while maintaining element existence check functionality
            - Use `.get()` method for JSON dictionary access to avoid KeyError
            - Add proper file handling with try-except blocks

            ===============================================================================
            💬 EXAMPLES OF USER REQUIREMENTS (ALL ABOUT ELEMENT EXISTS CHECK)
            ===============================================================================
            - "check if element exists"
            - "verify button is present"
            - "validate field visibility"
            - "check if login button is available"
            - "verify element is on the page"
            - "check element presence"
            - "validate element exists on screen"
            - "confirm element is displayed"
            - "check if error message appears"
            ===============================================================================
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

def code_correction_table_extract(desc,xpath,file_path,var_name,driver,userid):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    xpath_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
        

    # if region_status:
    #     from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
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


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's requirement describing the table extraction task (e.g., "extract table from invoice", "get data table from screenshot").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python function that extracts table data from an image and returns it as a pandas DataFrame.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver` as parameter: def run(driver):
            3. All code logic must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[{var_name}]}}"

            5. Use appropriate OCR/table extraction library (e.g., pytesseract, easyocr, or paddleocr) to extract table from the image.
            6. Parse the extracted text into structured table format.
            7. Always return a pandas DataFrame containing the extracted table data.
            8. If extraction fails, return an empty DataFrame with appropriate error logging.
            9. Include proper error handling for:
            - Image file not found in JSON
            - Image file path errors
            - OCR extraction failures
            - Table parsing errors
            10. All imports and logic must be inside the run function body.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver):
                import json
                import pandas as pd
                import cv2
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_info = json.load(f)
                except Exception as e:
                    print(f"Error loading JSON file: {{e}}")
                    return pd.DataFrame()
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return pd.DataFrame()
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                
                try:
                    # Load image
                    image = Image.open(image_path)
                    
                    # Extract text using OCR
                    ocr_text = pytesseract.image_to_string(image)
                    
                    # Parse text into table format
                    lines = [line.strip() for line in ocr_text.split('\\n') if line.strip()]
                    
                    # Split lines into columns (adjust delimiter as needed)
                    table_data = []
                    for line in lines:
                        row = [cell.strip() for cell in line.split('  ') if cell.strip()]
                        if row:
                            table_data.append(row)
                    
                    # Create DataFrame
                    if table_data:
                        df = pd.DataFrame(table_data[1:], columns=table_data[0])
                        print(f"Successfully extracted table with {{len(df)}} rows and {{len(df.columns)}} columns")
                        return df
                    else:
                        print("No table data found in image")
                        return pd.DataFrame()
                        
                except Exception as e:
                    print(f"Error extracting table from image: {{e}}")
                    return pd.DataFrame()

            Notes:
            - The function signature must be: def run(driver):
            - All imports must be inside the run function.
            - All code logic must be inside the run function body.
            - The function always returns a pandas DataFrame.
            - Returns populated DataFrame if table extraction succeeds.
            - Returns empty DataFrame if extraction fails or errors occur.
            - Uses OCR library (pytesseract/easyocr/paddleocr) for text extraction.
            - Parses extracted text into structured table format.
            - Handles various table formats and delimiters.
            - Adjust parsing logic based on table structure in the image.
            """

    elif region_status and not co_ordinates_status and not img_status:
        prompt = """"""
    else:
        xpath_status=True
        code = f"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def run(driver):
    import json
    json_path="json_info/json_xpath.json"    
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath_info = xpath_json[element_name]
    ifrmae_flag=False
    if type(xpath_info)==dict:
        table_xpath=xpath_info["xpath"]
        if "iframe" in xpath_info:
            iframe_data=xpath_info["iframe"]
            iframe_flag=True
            if type(iframe_data) in list:
                for i in iframe_data:
                    driver.switch_to.frame(i)
    else:
        table_xpath=xpath_info

    element = driver.find_element(By.XPATH, table_xpath)
    html = element.get_attribute("outerHTML")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table:
        headers = []
        rows_data = []

        thead = table.find("thead")
        if thead!=None:
            table_fd=True
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]

        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:
                rows_data.append(row_data)
        

        if headers and rows_data and len(headers) == len(rows_data[0]):
            return pd.DataFrame(rows_data, columns=headers)
        return pd.DataFrame(rows_data)

    headers = []
    rows_data = []

    # Header divs (common patterns)
    header_divs = soup.select(
        "div.header div, div.thead div, div.header div.col"
    )

    if header_divs:
        headers = [h.get_text(strip=True) for h in header_divs]

    # Row divs
    row_divs = soup.select(
        "div.row, div.tr"
    )

    for row in row_divs:
        cell_divs = row.select("div.cell, div.col, div.td")
        row_data = [cell.get_text(strip=True) for cell in cell_divs]
        if row_data:
            rows_data.append(row_data)

    if headers and rows_data and len(headers) == len(rows_data[0]):
        return pd.DataFrame(rows_data, columns=headers)

    return pd.DataFrame(rows_data)
"""
        
    if not region_status:
        code_to_write = code
    else:
        code_to_write=f"""
import pandas as pd
import json
from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
def run(driver=None):
    desc="{desc}"
    json_path = "json_info/json_xpath.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    bound_index=json_info["{var_name}"]
    img_path=capture_region(bound_index)
    list_dict=gemini_image_response(img_path,desc)
    df = pd.DataFrame(list_dict[0])
    return df
        """

    # Remove markdown code block markers
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()
    write_code(file_path,code_to_write)
    return code_to_write

def fallback_code_correction_table_extract(desc,xpath,file_path,var_name,driver,userid,error_info):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    error_code=error_info["code"]
    error_file=error_info["file"]
    error_detail=error_info["error"]
    co_ordinates_status=False
    img_status=False
    xpath_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
    
    # if region_status:
    #     from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status and not region_status:
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


    elif img_status and not co_ordinates_status and not region_status:
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language - about extracting table data from an image (e.g., "extract table from screenshot", "get table data from image", "scrape table from invoice image").
            - error_code: The previously generated Python code that encountered an error (string).
            - error_detail: The exception or error message that occurred when executing the code (string).
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Context:
            For the user requirement "{desc}", an agent previously created code that resulted in an error. Your task is to analyze the error and generate a corrected version of the code that extracts table data from an image and returns a pandas DataFrame.

            Previous Code:
            {error_code}

            Error Encountered:
            {error_detail}

            Task:
            Generate a corrected Python function that extracts table data from an image and returns a pandas DataFrame, fixing the error that occurred in the previous code.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `driver` as parameter: def run(driver):
            3. All code logic and imports must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/json_xpath.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            element_name = {var_name}
            image_path = f"{{proj_fol}}/{{task_fol}}/images/{{json_info[element_name]}}"

            5. Use appropriate OCR/table extraction library (e.g., pytesseract, easyocr, paddleocr, or cv2) to extract table from the image.
            6. Parse the extracted text into structured table format with proper rows and columns.
            7. Always return a pandas DataFrame containing the extracted table data.
            8. **CRITICAL**: Address and fix the specific error from {error_detail}. Analyze the root cause and implement a robust solution.
            9. Include proper error handling for:
            - Image file not found in JSON
            - JSON file or key errors
            - Image file path errors
            - OCR extraction failures
            - Table parsing errors
            - DataFrame creation errors
            - Any other exceptions
            10. If extraction fails, return an empty DataFrame with appropriate error logging.
            11. All imports and logic must be inside the run function body.

            Output:
            Return only the complete Python function code — no extra text, explanation, or commentary.

            Example reference format:

            def run(driver):
                import json
                import pandas as pd
                import cv2
                import pytesseract
                from PIL import Image
                import numpy as np
                
                # Load image path from JSON
                json_path = "json_info/json_xpath.json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_info = json.load(f)
                except FileNotFoundError:
                    print(f"JSON file not found: {{json_path}}")
                    return pd.DataFrame()
                except json.JSONDecodeError:
                    print(f"Invalid JSON format in: {{json_path}}")
                    return pd.DataFrame()
                except Exception as e:
                    print(f"Error loading JSON: {{e}}")
                    return pd.DataFrame()
                
                element_name = {var_name}
                image_filename = json_info.get(element_name)
                if not image_filename:
                    print(f"Image key '{{element_name}}' not found in JSON")
                    return pd.DataFrame()
                
                image_path = f"{{proj_fol}}/{{task_fol}}/images/{{image_filename}}"
                
                try:
                    # Load image
                    try:
                        image = Image.open(image_path)
                    except FileNotFoundError:
                        print(f"Image file not found: {{image_path}}")
                        return pd.DataFrame()
                    except Exception as e:
                        print(f"Error loading image: {{e}}")
                        return pd.DataFrame()
                    
                    # Preprocess image for better OCR (optional)
                    try:
                        img_cv = cv2.imread(image_path)
                        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                    except Exception as e:
                        print(f"Image preprocessing warning: {{e}}")
                        # Continue with original image if preprocessing fails
                    
                    # Extract text using OCR
                    try:
                        ocr_text = pytesseract.image_to_string(image)
                        if not ocr_text or not ocr_text.strip():
                            print("No text extracted from image")
                            return pd.DataFrame()
                    except Exception as e:
                        print(f"OCR extraction error: {{e}}")
                        return pd.DataFrame()
                    
                    # Parse text into table format
                    try:
                        lines = [line.strip() for line in ocr_text.split('\\n') if line.strip()]
                        
                        if not lines:
                            print("No valid lines found in extracted text")
                            return pd.DataFrame()
                        
                        # Split lines into columns (adjust delimiter as needed)
                        table_data = []
                        for line in lines:
                            # Try multiple delimiters
                            if '|' in line:
                                row = [cell.strip() for cell in line.split('|') if cell.strip()]
                            elif '\\t' in line:
                                row = [cell.strip() for cell in line.split('\\t') if cell.strip()]
                            else:
                                # Split by multiple spaces
                                row = [cell.strip() for cell in line.split('  ') if cell.strip()]
                            
                            if row:
                                table_data.append(row)
                        
                        if not table_data:
                            print("No table data could be parsed from text")
                            return pd.DataFrame()
                    except Exception as e:
                        print(f"Error parsing table data: {{e}}")
                        return pd.DataFrame()
                    
                    # Create DataFrame
                    try:
                        # Check if first row can be headers
                        if len(table_data) > 1:
                            # Ensure all rows have same number of columns
                            max_cols = max(len(row) for row in table_data)
                            normalized_data = []
                            for row in table_data:
                                if len(row) < max_cols:
                                    row.extend([''] * (max_cols - len(row)))
                                elif len(row) > max_cols:
                                    row = row[:max_cols]
                                normalized_data.append(row)
                            
                            # Use first row as headers
                            df = pd.DataFrame(normalized_data[1:], columns=normalized_data[0])
                        else:
                            df = pd.DataFrame(table_data)
                        
                        if df.empty:
                            print("Created DataFrame is empty")
                            return pd.DataFrame()
                        
                        print(f"Successfully extracted table with {{len(df)}} rows and {{len(df.columns)}} columns")
                        return df
                        
                    except Exception as e:
                        print(f"Error creating DataFrame: {{e}}")
                        return pd.DataFrame()
                    
                except Exception as e:
                    print(f"Unexpected error during table extraction: {{e}}")
                    return pd.DataFrame()

            Common Error Fixes to Consider:
            - **FileNotFoundError**: Add try-except for JSON and image file loading; verify paths exist before accessing
            - **KeyError**: Check if element_name exists in json_info before accessing; use .get() method with default value
            - **json.JSONDecodeError**: Handle invalid JSON format; check file encoding
            - **PIL.UnidentifiedImageError**: Verify image file is valid and not corrupted; check file format
            - **pytesseract.TesseractNotFoundError**: Ensure Tesseract is installed; set tesseract path if needed
            - **TypeError**: Validate all variables are correct type before operations; check None values
            - **AttributeError**: Ensure all objects are properly initialized; check method existence
            - **ValueError**: Validate data types and ranges; handle empty data gracefully
            - **IndexError**: Check list/array bounds before accessing; handle empty collections
            - **UnicodeDecodeError**: Specify correct encoding (utf-8) when reading files
            - **PermissionError**: Check file permissions for JSON and image files
            - **OSError**: Handle file system errors; check disk space and file access
            - **ImportError**: Ensure all required packages are imported inside the function
            - **NameError**: Ensure all variables are defined before use
            - **pandas.errors.EmptyDataError**: Handle empty data before DataFrame creation
            - **cv2.error**: Handle OpenCV errors in image processing; validate image format
            - **Memory errors**: Handle large images; consider image resizing if needed
            - **Empty string/list errors**: Validate data exists before processing
            - **Column mismatch errors**: Normalize row lengths before DataFrame creation
            - **Delimiter detection**: Try multiple delimiters (tabs, pipes, spaces) for parsing

            Notes / Constraints:
            - **CRITICAL**: Analyze the error in {error_detail} carefully and ensure the corrected code addresses the root cause
            - The function signature must be: def run(driver):
            - All imports must be inside the run function (json, pandas, cv2, pytesseract, PIL, numpy)
            - All code logic must be inside the run function body
            - Ensure `element_name = {var_name}` is assigned before accessing json_info
            - Use `json_info.get(element_name)` instead of `json_info[element_name]` to avoid KeyError
            - Add comprehensive try-except blocks for all potential failure points
            - The function always returns a pandas DataFrame (empty or populated)
            - Returns populated DataFrame if table extraction succeeds
            - Returns empty DataFrame (pd.DataFrame()) if extraction fails or any error occurs
            - Handle various image formats (PNG, JPG, BMP, TIFF)
            - Handle various table formats and structures
            - Try multiple text delimiters (pipes |, tabs \\t, multiple spaces)
            - Normalize row lengths before creating DataFrame
            - Use first row as headers when appropriate
            - Clean extracted text (strip whitespace, remove empty values)
            - If OCR quality is poor, consider image preprocessing (grayscale, thresholding)
            - If the previous error was related to missing imports, ensure all required packages are imported
            - If the previous error was related to file paths, add validation for file existence
            - If the previous error was related to empty data, add checks before processing
            - If the previous error was related to column mismatches, normalize data structure
            - If the previous error was related to encoding, specify utf-8 encoding
            - If the previous error was related to Tesseract, add path configuration or alternative OCR
            - Keep the function self-contained and robust
            - Do not send any additional explanation or console text beyond the function definition itself

            Additional OCR Libraries (if pytesseract fails):
            - **easyocr**: Good for multilingual text
            ```python
            import easyocr
            reader = easyocr.Reader(['en'])
            result = reader.readtext(image_path)
            ```
            - **paddleocr**: Fast and accurate
            ```python
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            result = ocr.ocr(image_path)
            ```

            Alternative Table Extraction Methods:
            - Use pytesseract with image_to_data for better structure
            - Use cv2 for table line detection
            - Use pandas.read_html for HTML-based tables (if applicable)
            - Use camelot or tabula for PDF tables (if source is PDF)
            """
    elif region_status and not co_ordinates_status and not img_status:
        prompt = f""""""
    else:
        xpath_status=True



    if not region_status and not xpath_status:   
        response = chat.send_message(prompt)
        code_to_write = response.text
    elif xpath_status:
        code_to_write=f"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def run(driver):
    import json
    json_path="json_info/json_xpath.json"    
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath_info = xpath_json[element_name]
    ifrmae_flag=False
    if type(xpath_info)==dict:
        table_xpath=xpath_info["xpath"]
        if "iframe" in xpath_info:
            iframe_data=xpath_info["iframe"]
            iframe_flag=True
            if type(iframe_data) == list:
                for i in iframe_data:
                    driver.switch_to.frame(i)
    else:
        table_xpath=xpath_info

    element = driver.find_element(By.XPATH, table_xpath)
    html = element.get_attribute("outerHTML")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table:
        headers = []
        rows_data = []

        thead = table.find("thead")
        if thead!=None:
            table_fd=True
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]

        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:
                rows_data.append(row_data)
        

        if headers and rows_data and len(headers) == len(rows_data[0]):
            return pd.DataFrame(rows_data, columns=headers)
        return pd.DataFrame(rows_data)

    headers = []
    rows_data = []

    # Header divs (common patterns)
    header_divs = soup.select(
        "div.header div, div.thead div, div.header div.col"
    )

    if header_divs:
        headers = [h.get_text(strip=True) for h in header_divs]

    # Row divs
    row_divs = soup.select(
        "div.row, div.tr"
    )

    for row in row_divs:
        cell_divs = row.select("div.cell, div.col, div.td")
        row_data = [cell.get_text(strip=True) for cell in cell_divs]
        if row_data:
            rows_data.append(row_data)

    if headers and rows_data and len(headers) == len(rows_data[0]):
        return pd.DataFrame(rows_data, columns=headers)

    return pd.DataFrame(rows_data)
"""
    elif region_status:
        code_to_write=f"""
import pandas as pd
import json
from datas.supporting_files.region_img_table_extract import gemini_image_response,capture_region
def run(driver=None):
    desc="{desc}"
    json_path = "json_info/json_xpath.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    bound_index=json_info["{var_name}"]
    img_path=capture_region(bound_index)
    list_dict=gemini_image_response(img_path,desc)
    df = pd.DataFrame(list_dict[0])
    return df
        """
    # Remove markdown code block markers
    if code_to_write.startswith("```"):
        lines = code_to_write.strip().split("\n")
        code_to_write = "\n".join(lines[1:-1])

    code_to_write = code_to_write.rstrip()
    if code_to_write.endswith("```"):
        code_to_write = code_to_write[:-3].rstrip()
    write_code(file_path,code_to_write)
    return code_to_write

def code_correction_pageination_table(desc,xpath,file_path,var_name,driver,userid):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
    if isinstance(xpath, str):
        if xpath.lower().endswith(".png"):
            img_status = True
    html_content=""
    outer_html=""
    # WebDriverWait(driver, 20).until(
    #     lambda d: d.execute_script("return document.readyState") == "complete"
    # )
    # html_content = driver.execute_script("return document.documentElement.outerHTML;")
    # with open("page_content.html", "w", encoding="utf-8") as f:
    #     f.write(html_content)
    # xpath=screenshot_xpath.get_xpath(driver,desc,html_content)
    # genai.configure(api_key=config.API_KEY)
    # model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    # chat = model.start_chat()
    # result=table_dropdown_find(desc)
    # dropdown_selection=False
    # table_extraction=False
    # if len(result)>0:
    #     if result["result"]=="dropdown_selection":
    #         dropdown_selection=True
    #     elif result["result"]=="table_extraction":
    #         table_extraction=True
    if not co_ordinates_status and not img_status:
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
    nxt_btn_element=f"{var_name}_nxt_btn"
    dis_btn_element=f"{var_name}_dis_btn"


    code_to_write = f"""
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox


def run(driver):
    import json
    json_path="json_info/json_xpath.json"
    table_element="{var_name}"
    nxt_btn_element="{nxt_btn_element}"
    dis_btn_element="{dis_btn_element}"

    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    table_xpath=xpath_json[table_element]
    nxt_btn_xpath=xpath_json[nxt_btn_element]
    dis_btn_xpath=xpath_json[dis_btn_element]

    all_rows = []
    headers = None
    last_first_row = None

    flag = False

    while True:
        try:

            if nxt_btn_xpath == dis_btn_xpath:
                try:
                    WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, nxt_btn_xpath))
                    )
                    flag = False
                except:
                    flag = True

                if flag:
                    print("Reached last page (Next not clickable).")
                    break

            else:
                # Different element → use original disabled detection
                try:
                    disable_btn = driver.find_element(By.XPATH, dis_btn_xpath)
                    disabled_attr = (
                        disable_btn.get_attribute("disabled")
                        or disable_btn.get_attribute("class")
                        or ""
                    )
                    if "disabled" in disabled_attr or disabled_attr == "true":
                        print("Reached last page (Disabled button detected).")
                        break
                except NoSuchElementException:
                    pass

            # Table extraction logic
            table_el = driver.find_element(By.XPATH, table_xpath)
            soup = BeautifulSoup(table_el.get_attribute("outerHTML"), "html.parser")
            table = soup.find("table")

            if headers is None:
                header_rows = table.select("thead tr")
                headers = []
                for tr in header_rows:
                    for th in tr.find_all("th"):
                        text = th.get_text(strip=True)
                        colspan = int(th.get("colspan", 1))
                        headers.extend([text] * colspan)

            col_count = len(headers)

            page_rows = []
            for tr in table.select("tbody tr"):
                cells = tr.find_all("td")
                row = [td.get_text(strip=True) for td in cells]

                if len(row) > col_count:
                    row = row[:col_count]
                elif len(row) < col_count:
                    row.extend([""] * (col_count - len(row)))

                all_rows.append(row)
                page_rows.append(row)

            if not page_rows:
                break

            current_first_row = tuple(page_rows[0])
            if current_first_row == last_first_row:
                break

            last_first_row = current_first_row

            # Click Next
            next_btn = driver.find_element(By.XPATH, nxt_btn_xpath)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(10)

        except StaleElementReferenceException:
            time.sleep(1)
            continue

        except NoSuchElementException:
            break

    return pd.DataFrame(all_rows, columns=headers)

   """

    # Remove markdown code block markers
    # if code_to_write.startswith("```"):
    #     lines = code_to_write.strip().split("\n")
    #     code_to_write = "\n".join(lines[1:-1])

    # code_to_write = code_to_write.rstrip()
    # if code_to_write.endswith("```"):
    #     code_to_write = code_to_write[:-3].rstrip()
    write_code(file_path,code_to_write)
    return code_to_write


def fallback_pagenination_extract(desc,xpath,file_path,var_name,driver,userid,error_info):
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]
    error_code=error_info["code"]
    error_file=error_info["file"]
    error_detail=error_info["error"]
    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
    if isinstance(xpath, str):
        if xpath.lower().endswith(".png"):
            img_status = True
    html_content=""
    outer_html=""
    # WebDriverWait(driver, 20).until(
    #     lambda d: d.execute_script("return document.readyState") == "complete"
    # )
    # html_content = driver.execute_script("return document.documentElement.outerHTML;")
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
        try:
            element = driver.find_element(By.XPATH, xpath)
            outer_html = element.get_attribute("outerHTML")
        except:
            outer_html=""
    nxt_btn_element=f"{var_name}_nxt_btn"
    dis_btn_element=f"{var_name}_dis_btn"
    prompt = f"""
    Generate a complete Python function to extract data from a paginated HTML table using Selenium WebDriver with robust pagination handling.

    **IMPORTANT - This is a RETRY attempt:**
    Previous code generation failed with the following error:
    {error_detail}

    Previously generated code that failed:
    {error_code}

    **CRITICAL: Analyze the error and previous code to:**
    1. Identify the root cause of the failure
    2. Implement specific fixes to prevent the same error
    3. Add additional error handling for similar issues
    4. Improve the logic that caused the failure
    5. DO NOT repeat the same mistakes or approach that failed

    **Available Data:**
    - Main table XPath: {xpath}
    - Table outer HTML structure: {outer_html}
    - Next button XPath variable name: {nxt_btn_element}
    - Disabled next button XPath variable name: {dis_btn_element}
    - User requirement: {desc}

    **Table Structure Analysis:**
    Analyze the provided outer HTML ({outer_html}) to understand:
    - Table headers (thead/th elements)
    - Table body structure (tbody/tr/td elements)
    - Number of columns
    - Data types in each column
    - Any nested elements within cells

    **Pagination Logic Requirements:**

    1. **Initial Setup:**
    - Wait for the table to be fully loaded before extraction
    - Use explicit waits (WebDriverWait) with appropriate timeouts
    - Verify table element is present and visible

    2. **Data Extraction Per Page:**
    - Locate all rows in the table body (excluding headers)
    - Extract text from each cell in every row
    - Handle empty cells gracefully
    - Preserve data structure and column order
    - Store extracted data in a list or appropriate data structure

    3. **Pagination Control:**
    - After extracting data from current page, check for next button availability
    - Use the disabled button XPath ({dis_btn_element}) to determine if pagination is complete
    - Methods to check:
        a. Check if disabled button XPath element exists (indicates last page)
        b. Check if next button is clickable/enabled
        c. Handle StaleElementReferenceException during pagination
    - If next button is available and enabled:
        - Click the next button using {nxt_btn_element} XPath
        - Wait for page to load (wait for table to refresh or use explicit wait)
        - Continue extraction from new page
    - If disabled button exists or next button is not clickable:
        - Stop pagination loop

    4. **Robust Error Handling:**
    - Handle NoSuchElementException if buttons or table elements not found
    - Handle TimeoutException if page loading takes too long
    - Handle StaleElementReferenceException during pagination
    - Implement retry logic for intermittent failures
    - Add appropriate waits between page transitions

    5. **Data Consolidation:**
    - Combine data from all pages into a single pandas DataFrame
    - Ensure column names match table headers
    - Remove duplicate rows if any
    - Handle data type conversions appropriately

    **XPath Loading Pattern:**
    ```python
    json_path = "json_info/json_xpath.json"

    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)

    table_element = "{var_name}"
    nxt_btn_element = "{nxt_btn_element}"
    dis_btn_element = "{dis_btn_element}"

    table_element_xpath = json_info[table_element]
    nxt_btn_xpath = json_info[nxt_btn_element]
    disable_btn_xpath = json_info[dis_btn_element]
    ```

    **User Requirement Handling ({desc}):**
    - If {desc} mentions writing to Excel/CSV:
    - Extract the file path from the requirement
    - Write DataFrame to specified path using pandas (to_excel or to_csv)
    - Create directories if they don't exist
    - Handle file write errors gracefully
    - If {desc} mentions specific columns or filtering:
    - Apply filters after extracting all data
    - Select only required columns
    - If {desc} mentions data transformation:
    - Apply transformations after extraction
    - ALWAYS return the final DataFrame regardless of other operations

    **Required Code Structure:**
    ```python
    def run(driver):
        import pandas as pd
        import json
        import time
        import os
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
        
        # Load XPath configuration
        json_path = "json_info/json_xpath.json"
        with open(json_path, "r", encoding="utf-8") as f:
            json_info = json.load(f)
        
        table_element = "{var_name}"
        nxt_btn_element = "{nxt_btn_element}"
        dis_btn_element = "{dis_btn_element}"
        
        table_element_xpath = json_info[table_element]
        nxt_btn_xpath = json_info[nxt_btn_element]
        disable_btn_xpath = json_info[dis_btn_element]
        
        all_data = []
        page_number = 1
        
        while True:
            # Wait for table to load
            # Extract headers (only on first page)
            # Extract all rows from current page
            # Add to all_data list
            
            # Check for next page
            try:
                # Check if disabled button exists (indicates last page)
                # OR check if next button is clickable
                # If last page, break loop
                # Otherwise, click next button and wait for new page
            except:
                # Handle exceptions
                break
            
            page_number += 1
        
        # Create DataFrame from all_data
        df = pd.DataFrame(all_data)
        
        # Handle user requirement: {desc}
        # If file write is required, write the file
        
        return df
    ```

    **Critical Implementation Rules:**
    1. Function name MUST be `run` with exactly one parameter `driver`
    2. ALL imports MUST be inside the function
    3. Use explicit waits (WebDriverWait) instead of time.sleep() where possible
    4. Always return pandas DataFrame as the final statement
    5. Do NOT call the function within the code
    6. Do NOT include any explanatory text outside the function
    7. Handle pagination loop with proper termination conditions
    8. Check for disabled button OR non-clickable next button to stop pagination
    9. Implement proper exception handling for robust execution
    10. Preserve data integrity across all pages

    **Expected Output:**
    Provide ONLY the complete, executable Python function code with:
    - Proper pagination loop
    - Data extraction from each page
    - Termination condition based on disabled button or next button state
    - DataFrame creation and return
    - File writing if specified in {desc}
    - No comments, explanations, or text outside the function
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

def iframe_element_exist(desc,xpath,file_path,var_name,iframe_id,driver,userid, listvariable=[]):

    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
    # if not co_ordinates_status and not img_status and not region_status:
    #     element = driver.find_element(By.XPATH, xpath)
    #     outer_html = element.get_attribute("outerHTML")
    
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
    - Full Page HTML (context only): {html_content}
    - Variable name: {var_name}
    - List of Iframe ID: {iframe_id}
    
    ===============================================================================
    🎯 PRIMARY OBJECTIVE
    ===============================================================================
    Generate **runnable Selenium + Python code** that performs both:
    - The provided `driver`
    - The given `xpath`
    - The required browser automation actions.
    - Any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.).
    - **MUST return element existence status (True/False)** at the end of function.
    - Do not create or modify any new XPath.
    - Does NOT create, modify, or alter any XPath.
    - Must load the XPath dynamically from the JSON file using the exact pattern below:

        import json
        json_path = "json_info/json_xpath.json"
        element_name = {var_name}

        with open(json_path, "r") as f:
            xpath_json = json.load(f)

        xpath = xpath_json[element_name]["xpath"]

    Always use the `xpath` variable for locating elements. Never hardcode any XPath.

    ===============================================================================
    🖼️ IFRAME HANDLING RULES (MANDATORY)
    ===============================================================================
    **CRITICAL:** The target element is ALWAYS inside an iframe.
    
    The generated code MUST follow this exact structure:
    
    1. **Switch to all iframe id's one by one from the list** (before any element interaction):
```python
        iframe_ids={iframe_id}
        for iframe_data in iframe_ids:
            driver.switch_to.frame(iframe_data)
```
    
    2. **Check element existence and perform interactions** (click, type, select, extract, etc.)
    
    3. **Switch back to default content** (after completing all actions):
```python
        driver.switch_to.default_content()
```
    
    4. **Return element existence status** (True if element found, False otherwise)
    
    **Structure Pattern:**
```python
    def run(driver):
        # Load XPath from JSON
        import json
        json_path = "json_info/json_xpath.json"
        element_name = "{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]["xpath"]
        
        element_exists = False
        
        try:
            # Switch to all iframe id's
            iframe_ids={iframe_id}
            for iframe_data in iframe_ids:
                driver.switch_to.frame(iframe_data)
            
            # Check if element exists
            wait = WebDriverWait(driver, 30)
            element = wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
            element_exists = True
            
            # Perform actions here (click/type/select/extract/etc.)
            # ...your logic...
            
        except Exception as e:
            print(f"Error: {{e}}")
            element_exists = False
        
        finally:
            # Switch back to default content
            driver.switch_to.default_content()
            
        return element_exists
```

    ===============================================================================
    🧩 ACTION DETECTION RULES
    ===============================================================================
    Detect the action type from the description:
    - "type", "enter", "input" → typing actions
    - "click", "press", "submit" → clicking
    - "select", "choose", "pick" → dropdown selection
    - "vault", "from vault", "get from vault" → vault retrieval
    - "screenshot", "capture screen" → browser screenshot
    - "extract", "fetch", "get table", "export" → data extraction

    ===============================================================================
    🔐 VAULT HANDLING RULES
    ===============================================================================
    If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
    1. Extract the asset name (the word before "from vault").
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
    arg_con = "run(driver)"
    for list in function_arg:
        arg_con += list + ","
    function_string = arg_con[:-1] + ")"
    
    1. The function name must be exactly {{function_string}}.
    2. Use the xpath on the code by below pattern:
        import json
        json_path = "json_info/json_xpath.json"
        element_name = {var_name}
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]["xpath"]

    3. Do NOT hardcode the XPath anywhere in the code.  
        Always use the `xpath` variable loaded from the JSON file.
    
    4. Required package imports (must be inside the function):
        import json  # MANDATORY
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC
    
    5. Type Functionality:
        If the User req: {desc} is about typing element on field means 
        For Example: "type password as 'welcome#2025'" should type the exact value "welcome#2025", 
        NOT placeholder values like "type your username here"
    
    6. Dropdown handling rules:
        - If element contains `<select>`, use `Select(element).select_by_visible_text(...)`.
        - If element is a custom async-ui-select or div-based dropdown:
            1. Click on the dropdown trigger element.
            2. Wait for the options container to appear (`ul.ui-select-choices` or `.ui-select-choices-row`).
            3. Find the correct option by its visible text and click it.
            4. Example structure:
```python
                wait = WebDriverWait(driver, 30)
                element = wait.until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                element_exists = True
                element.click()
                wait = WebDriverWait(driver, 10)
                option = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ui-select-choices-row')]//span[normalize-space()='Declined']")))
                option.click()
```
        - Ensure to match the nested `<span>` text for options, not just `<div>`.

    7. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

    ===============================================================================
    💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION)
    ===============================================================================
    Dynamically detect both file path and format based on the user description.

    🧩 Step 1: Path Detection
    - If the description includes any of these patterns:
        "in this path", "to path", "save at", "save in", "write it in"
    - Extract the full file path.
    - If none found, default to "output.xlsx".

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

    def run(driver):
        import json
        json_path = "json_info/json_xpath.json"
        element_name = "{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]["xpath"]
        
        element_exists = False
        
        try:
            # Switch to all iframe id's
            iframe_ids={iframe_id}
            for iframe_data in iframe_ids:
                driver.switch_to.frame(iframe_data)
            
            # Check element existence
            wait = WebDriverWait(driver, 30)
            element = wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
            element_exists = True
            
            # Generated logic here
            # ...perform actions...
            
        except Exception as e:
            print(f"Error: {{e}}")
            element_exists = False
        
        finally:
            # Switch back to default content
            driver.switch_to.default_content()
        
        return element_exists

    ===============================================================================
    🔄 ELEMENT EXISTENCE CHECK RULES (MANDATORY)
    ===============================================================================
    1. **Initialize status variable**: `element_exists = False` at the start of function
    
    2. **Wrap all logic in try-except-finally block**:
       - try: Switch to iframes → Find element → Set element_exists = True → Perform actions
       - except: Catch any errors → Set element_exists = False
       - finally: Switch back to default_content() → Return element_exists
    
    3. **Always return boolean**: The function MUST always return `element_exists` (True/False)
    
    4. **Set True only after successful element location**:
       - After `driver.find_element(By.XPATH, xpath)` succeeds, set `element_exists = True`
       - If element is not found or any error occurs, keep it as False
    
    5. **Error handling pattern**:
```python
        element_exists = False
        try:
            # iframe switching
            iframe_ids={iframe_id}
            for iframe_data in iframe_ids:
                driver.switch_to.frame(iframe_data)
            
            # element check
            wait = WebDriverWait(driver, 30)
            element = wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
            element_exists = True  # Set to True only after successful find
            
            # perform actions
            element.click()  # or any other action
            
        except Exception as e:
            print(f"Error: {{e}}")
            element_exists = False
        finally:
            driver.switch_to.default_content()
        
        return element_exists
```

    ===============================================================================
    NOTE: (MANDATORY)
    ===============================================================================
    - All import statements must be placed inside the function block.
    - The import statement `import json` is mandatory and must always be included.
    - ALWAYS switch to iframe BEFORE any element interaction.
    - ALWAYS switch back to default_content() AFTER completing all actions (in finally block).
    - The iframe switch is NON-OPTIONAL and must be present in every generated code.
    - For logic building using iframe id switch do not use logic like EC.element_to_be_clickable always prefer EC.presence_of_element_located
    - ALWAYS initialize `element_exists = False` at the start.
    - ALWAYS wrap iframe switching and element operations in try-except-finally block.
    - ALWAYS set `element_exists = True` only after successfully finding the element.
    - ALWAYS return `element_exists` at the end of the function.
    - Use finally block to ensure driver.switch_to.default_content() is always called.
    
    ===============================================================================
    💬 EXAMPLES
    ===============================================================================
    Example 1: Click action
    ```python
    def run(driver):
        import json
        from selenium.webdriver.common.by import By
        
        json_path = "json_info/json_xpath.json"
        element_name = "submit_button"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]["xpath"]
        
        element_exists = False
        
        try:
            iframe_ids={iframe_id}
            for iframe_data in iframe_ids:
                driver.switch_to.frame(iframe_data)
            
            wait = WebDriverWait(driver, 30)
            element = wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
            element_exists = True
            element.click()
            
        except Exception as e:
            print(f"Error: {{e}}")
            element_exists = False
        finally:
            driver.switch_to.default_content()
        
        return element_exists
    ```

    Example 2: Type action
    ```python
    def run(driver):
        import json
        from selenium.webdriver.common.by import By
        
        json_path = "json_info/json_xpath.json"
        element_name = "username_field"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath = xpath_json[element_name]["xpath"]
        
        element_exists = False
        
        try:
            iframe_ids={iframe_id}
            for iframe_data in iframe_ids:
                driver.switch_to.frame(iframe_data)
            
            wait = WebDriverWait(driver, 30)
            element = wait.until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
            element_exists = True
            element.clear()
            element.send_keys("admin@example.com")
            
        except Exception as e:
            print(f"Error: {{e}}")
            element_exists = False
        finally:
            driver.switch_to.default_content()
        
        return element_exists
    ```

    - "select Declined from Bill Status dropdown" → Returns True/False
    - "choose Completed from Status menu" → Returns True/False
    - "type username from vault in username field" → Returns True/False
    - "extract table and save to Excel" → Returns True/False
    - "fetch table and export to CSV" → Returns True/False
    - "click on Submit button" → Returns True/False
    - "capture screenshot of current page" → Returns True/False
    - "read div container and export as JSON" → Returns True/False
    ===============================================================================
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

def iframe_code_correction(desc,xpath,file_path,var_name,iframe_id,driver,userid,add_info,type_input, listvariable=[]):
    dynamic_status=False
    if type_input==None:
        type_input=""
    if add_info["xpath_variables"] !="":
        dynamic_xpath_variables=add_info["xpath_variables"]
        dynamic_status=True
    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False
    region_status=False
    if type(xpath) == list:
        if len(xpath)==2:
            co_ordinates_status=True
        elif len(xpath)==4:
            region_status=True
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
    # if not co_ordinates_status and not img_status and not region_status:
    #     element = driver.find_element(By.XPATH, xpath)
    #     outer_html = element.get_attribute("outerHTML")
    if dynamic_status:
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
- Full Page HTML (context only): {html_content}
- Variable name: {var_name}
- List of Iframe ID: {iframe_id}
- Type Input Data: {type_input}

===============================================================================
🎯 PRIMARY OBJECTIVE
===============================================================================
Generate **runnable Selenium + Python code** that performs:
- Uses the provided `driver`
- **For TYPE actions**: Function signature is `run(driver, type_input, *args)` with type_input as 2nd argument
- **For NON-TYPE actions**: Function signature is `run(driver, *args)` without type_input
- Uses the given `xpath` loaded dynamically from JSON
- Performs required browser automation actions
- Handles any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)
- Does NOT create, modify, or alter any XPath
- Must load the XPath and dynamic variables from JSON files using the exact pattern below:

    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)

Always use the `xpath` variable for locating elements. Never hardcode any XPath or dynamic variables.

===============================================================================
🖼️ IFRAME HANDLING RULES (MANDATORY)
===============================================================================
**CRITICAL:** The target element is ALWAYS inside an iframe.

The generated code MUST follow this exact structure:

1. **Switch to all iframe id's one by one from the list** (before any element interaction):
```python
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
```

2. **Perform all element interactions** (click, type, select, extract, etc.)

3. **Switch back to default content** (after completing all actions):
```python
    driver.switch_to.default_content()
```

**Structure Pattern for TYPE actions:**
```python
def run(driver, type_input, *args):  # type_input as 2nd parameter
    # Load XPath from JSON
    import json
    from datas.source_files.xpath_format import format_xpath
    
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Type using the parameter
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # Use parameter directly
    
    # Switch back to default content
    driver.switch_to.default_content()
```

**Structure Pattern for NON-TYPE actions:**
```python
def run(driver, *args):  # No type_input parameter
    # Load XPath from JSON
    import json
    from datas.source_files.xpath_format import format_xpath
    
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Perform actions here (click/select/extract/etc.)
    # ...your logic...
    
    # Switch back to default content
    driver.switch_to.default_content()
```

===============================================================================
🚨 MULTI-ACTION HANDLING (CRITICAL - NO AUTONOMOUS DECISIONS)
===============================================================================

**RULE: Generate EXACTLY what the user requests - NO MORE, NO LESS**

When the user description contains multiple actions:
1. **Identify ALL actions explicitly mentioned**
2. **Generate code for ALL of them in sequence**
3. **DO NOT comment out any action**
4. **DO NOT make assumptions about what's "required" or "optional"**
5. **DO NOT add suggestions or alternatives**
6. **The code is auto-executed - commented code won't run and will FAIL the user's requirement**

**Common Multi-Action Patterns:**

1. **Type + Enter Key:**
   User says: "type username and press enter" or "enter text and hit enter key"
   
   ✓ CORRECT Implementation:
```python
def run(driver, type_input, *args):
    import json
    from selenium.webdriver.common.keys import Keys  # Import Keys
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids = {iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # Action 1: Type
    element.send_keys(Keys.RETURN)  # Action 2: Press Enter
    
    driver.switch_to.default_content()
```

   ❌ WRONG - Do NOT do this:
```python
    element.send_keys(type_input)
    # element.send_keys(Keys.RETURN)  # Uncomment if you want to press Enter
```

2. **Click + Type:**
   User says: "click the field and type username"
   
   ✓ CORRECT - Generate both actions:
```python
def run(driver, type_input, *args):
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids = {iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.click()  # Action 1: Click
    element.send_keys(type_input)  # Action 2: Type
    
    driver.switch_to.default_content()
```

3. **Type + Tab Key:**
   User says: "type and press tab"
   
   ✓ CORRECT:
```python
def run(driver, type_input, *args):
    import json
    from selenium.webdriver.common.keys import Keys
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids = {iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.send_keys(type_input)
    element.send_keys(Keys.TAB)
    
    driver.switch_to.default_content()
```

4. **Type + Click Different Element:**
   User says: "enter password and click submit button"
   
   ✓ CORRECT - This requires TWO separate xpath variables:
   **NOTE**: In this case, the submit button xpath should also be loaded from JSON
```python
def run(driver, type_input, *args):
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids = {iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Type in password field
    password_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    password_element.send_keys(type_input)
    
    # If submit button xpath is also available in JSON, load it similarly
    # For now, using a generic xpath (in real scenario, this should also come from JSON)
    submit_xpath = "//button[@type='submit']"
    submit_btn = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, submit_xpath)))
    submit_btn.click()
    
    driver.switch_to.default_content()
```

**Special Key Mappings:**
When user mentions keyboard keys, use these imports and constants:
```python
from selenium.webdriver.common.keys import Keys

# Key mappings:
- "press enter" / "hit enter" / "press return" → Keys.RETURN or Keys.ENTER
- "press tab" → Keys.TAB
- "press escape" / "press esc" → Keys.ESCAPE
- "press space" / "spacebar" → Keys.SPACE
- "press backspace" → Keys.BACKSPACE
- "press delete" → Keys.DELETE
- "press arrow up" → Keys.ARROW_UP
- "press arrow down" → Keys.ARROW_DOWN
- "press arrow left" → Keys.ARROW_LEFT
- "press arrow right" → Keys.ARROW_RIGHT
- "press home" → Keys.HOME
- "press end" → Keys.END
- "press page up" → Keys.PAGE_UP
- "press page down" → Keys.PAGE_DOWN
```

**CRITICAL RULES:**
1. If user mentions ONE action → Generate code for ONE action
2. If user mentions TWO actions → Generate code for BOTH actions
3. If user mentions THREE actions → Generate code for ALL THREE actions
4. NEVER comment out code that user explicitly requested
5. NEVER add comments like "uncomment if needed" or "optional"
6. NEVER make autonomous decisions about what's "necessary"
7. The code is auto-executed - commented code won't run and will FAIL user's requirement
8. ALWAYS import Keys if any keyboard action is mentioned

**Decision Matrix:**
- User says "type" only → Generate only typing code
- User says "type and press enter" → Generate typing + Keys.RETURN code
- User says "click and type" → Generate click + type code
- User says "type, press tab, and click next" → Generate all three actions in sequence
- User says "clear and type" → Generate clear + type code

===============================================================================
🧩 ACTION DETECTION RULES
===============================================================================
Detect the action type from the description:

1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
   - Standard click for buttons, links, any clickable element
   - Wait for element to be present (30 sec max)
   - **Function signature**: `def run(driver, *args):`

2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
   - For text input fields
   - Wait for element to be visible (30 sec max)
   - **Function signature**: `def run(driver, type_input, *args):`
   - **CRITICAL: Use the type_input parameter directly - it's passed as an argument**
   - **NEVER hardcode or use placeholder text**
   - **If combined with keyboard keys (enter/tab/etc.), include those actions too**
   - Example implementation:
```python
     def run(driver, type_input, *args):  # ✓ CORRECT - type_input as 2nd parameter
         # ... load xpath from JSON with dynamic variables using format_xpath ...
         # ... switch to iframe ...
         
         element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
         element.clear()
         element.send_keys(type_input)  # ✓ Use parameter directly
         
         driver.switch_to.default_content()
```

3. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
   - **Function signature**: `def run(driver, *args):`
   - Analyze element structure
   - Extract option text from description

4. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
   - **Function signature**: `def run(driver, *args):`
   - Scroll into view and hover
   - Wait for element to be present

5. **ELEMENT WAIT**: "wait for element", "check element", "element exists"
   - **Function signature**: `def run(driver, *args):`
   - Check element presence only
   - Return True/False status
   - Do not perform Click or Type action

6. **SCROLL ACTION**: "scroll to", "scroll into view"
   - **Function signature**: `def run(driver, *args):`
   - Scroll element into view

7. **SCROLL + CLICK COMBINED ACTION**: "scroll to and click", "scroll and click", "scroll to element and click", "bring into view and click"
- **This is a COMBINED action requiring both scroll and click**
- Must perform in sequence: scroll → wait → click
- Use the pattern below:

**Implementation Pattern:**
```python
def run(driver, *args):
    import json
    import time
    from datas.source_files.xpath_format import format_xpath
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Wait for element presence
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    
    # Scroll element into view
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    
    # Wait for scroll to complete
    time.sleep(0.5)
    
    # Wait for element to be clickable and click
    clickable_element = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    clickable_element.click()
    
    driver.switch_to.default_content()
```

**Key Points for Scroll + Click:**
- Always use smooth scrolling with center alignment
- Add 0.5s delay after scroll for stability
- Re-verify element is clickable after scroll
- Use xpath variable from JSON (never hardcode)
- Import time module for sleep

8. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
   - **Function signature**: `def run(driver, *args):`
   - Wait for element visibility
   - Return element text or value

9. **CLEAR FIELD**: "clear", "empty", "delete content"
   - **Function signature**: `def run(driver, *args):`
   - Wait for element visibility
   - Clear the input field

10. **Other Actions**:
   - "vault", "from vault", "get from vault" → vault retrieval (TYPE action)
   - "screenshot", "capture screen" → browser screenshot (NON-TYPE)
   - "extract", "fetch", "get table", "export" → data extraction (NON-TYPE)

===============================================================================
🔐 VAULT HANDLING RULES (FOR TYPE ACTIONS)
===============================================================================
If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
1. This is still a TYPE action, so use `def run(driver, type_input, *args):`
2. The type_input parameter will contain the vault-retrieved value (handled by caller)
3. Simply use the type_input parameter as-is
4. Example:
```python
   def run(driver, type_input, *args):  # Vault data passed via type_input
       import json
       from datas.source_files.xpath_format import format_xpath
       
       # Load XPath from JSON
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       
       # Load dynamic variables from JSON
       dynamic_var_path = "json_info/dynamic_xpath.json"
       with open(dynamic_var_path, "r") as f:
           dynamic_info = json.load(f)
       values = dynamic_info["data"]
       
       # Format XPath with dynamic values using format_xpath
       xpath_pattern = xpath_json[element_name]["xpath"]
       xpath = format_xpath(xpath_pattern, values)
       
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.clear()
       element.send_keys(type_input)  # Use parameter containing vault data
       
       driver.switch_to.default_content()
```

===============================================================================
⚙️ IMPLEMENTATION RULES
===============================================================================
1. **CRITICAL FUNCTION SIGNATURE RULES**:
   - **TYPE actions**: `def run(driver, type_input, *args):`
   - **NON-TYPE actions**: `def run(driver, *args):`
   - The `*args` allows for dynamic xpath variables to be passed

2. Use the xpath on the code by below pattern:
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)

3. Do NOT hardcode the XPath or dynamic variables anywhere in the code.  
    Always use the `xpath` variable loaded from the JSON file with values from dynamic_xpath.json using format_xpath function.

4. Required package imports (must be inside the function):
    import json  # MANDATORY
    from datas.source_files.xpath_format import format_xpath  # MANDATORY
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys  # If keyboard actions needed

5. **Type Functionality (CRITICAL):**
   - Function signature: `def run(driver, type_input, *args):`
   - **USE the type_input parameter directly - it's passed as an argument**
   - **NEVER hardcode text values in send_keys()**
   - **DO NOT** use generic text like:
     ❌ "type your username here"
     ❌ "enter password"
     ❌ "input text"
     ❌ Any hardcoded string
   - **ALWAYS DO** this:
     ✓ element.send_keys(type_input)  # Use the parameter
   
   Example:
```python
   # User req: type username as admin inside iframe
   # Type Input Data will be passed as argument
   def run(driver, type_input, *args):  # ✓ type_input as 2nd parameter
       import json
       from datas.source_files.xpath_format import format_xpath
       
       # Load XPath from JSON
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       
       # Load dynamic variables from JSON
       dynamic_var_path = "json_info/dynamic_xpath.json"
       with open(dynamic_var_path, "r") as f:
           dynamic_info = json.load(f)
       values = dynamic_info["data"]
       
       # Format XPath with dynamic values using format_xpath
       xpath_pattern = xpath_json[element_name]["xpath"]
       xpath = format_xpath(xpath_pattern, values)
       
       # Switch to iframe
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       # Type using parameter
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.clear()
       element.send_keys(type_input)  # ✓ Use parameter directly
       
       # Switch back
       driver.switch_to.default_content()
```

6. Dropdown handling rules:
    - If element contains `<select>`, use `Select(element).select_by_visible_text(...)`.
    - If element is a custom async-ui-select or div-based dropdown:
        1. Click on the dropdown trigger element.
        2. Wait for the options container to appear.
        3. Find the correct option by its visible text and click it.
        4. Example structure:
```python
def run(driver, *args):  # ✓ No type_input for dropdown
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = driver.find_element(By.XPATH, xpath)
    element.click()
    wait = WebDriverWait(driver, 10)
    option = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ui-select-choices-row')]//span[normalize-space()='Declined']")))
    option.click()
    
    driver.switch_to.default_content()
```

7. **Iframe-Specific Wait Strategy:**
   - For logic building using iframe id switch, always prefer `EC.presence_of_element_located`
   - Avoid `EC.element_to_be_clickable` inside iframes as it may cause issues
   - Use explicit waits with reasonable timeouts (10-30 seconds)

8. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

===============================================================================
💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION)
===============================================================================
Use function signature: `def run(driver, *args):`  # No type_input for file operations

Dynamically detect both file path and format based on the user description.

🧩 Step 1: Path Detection
- If the description includes any of these patterns:
    "in this path", "to path", "save at", "save in", "write it in"
- Extract the full file path.
- If none found, default to "output.xlsx".

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
📊 TABLE / DIV-CONTAINER EXTRACTION RULES
===============================================================================
When the user requirement mentions:
- "extract table", "get table data", "read table", "fetch table contents"
- "extract grid", "extract div table", "extract container"

Use function signature: `def run(driver, *args):`  # No type_input

Example:
```python
def run(driver, *args):  # ✓ 1 argument for table extraction
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    # Switch to iframe
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Extract table
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    rows = element.find_elements(By.XPATH, ".//tr")
    table_data = []
    for row in rows:
        cols = row.find_elements(By.XPATH, ".//th|.//td")
        row_data = [col.text.strip() for col in cols]
        table_data.append(row_data)
    
    # Normalize columns
    max_cols = max(len(r) for r in table_data) if table_data else 0
    for r in table_data:
        while len(r) < max_cols:
            r.append("")
    
    # Switch back
    driver.switch_to.default_content()
    
    return table_data
```

===============================================================================
✅ OUTPUT FORMAT (MANDATORY)
===============================================================================

**FOR TYPE ACTIONS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
def run(driver, type_input, *args):  # ✓ type_input as 2nd parameter
import json
from datas.source_files.xpath_format import format_xpath

# Load XPath from JSON
json_path = "json_info/json_xpath.json"
element_name = "{var_name}"
with open(json_path, "r") as f:
    xpath_json = json.load(f)

# Load dynamic variables from JSON
dynamic_var_path = "json_info/dynamic_xpath.json"
with open(dynamic_var_path, "r") as f:
    dynamic_info = json.load(f)
values = dynamic_info["data"]

# Format XPath with dynamic values using format_xpath
xpath_pattern = xpath_json[element_name]["xpath"]
xpath = format_xpath(xpath_pattern, values)

# Switch to all iframe id's
iframe_ids={iframe_id}
for iframe_data in iframe_ids:
    driver.switch_to.frame(iframe_data)

# Type using parameter - NO hardcoded values
element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
element.clear()
element.send_keys(type_input)  # ✓ Use the parameter

# Switch back to default content
driver.switch_to.default_content()

**FOR TYPE ACTIONS WITH KEYBOARD KEYS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver, type_input, *args):  # ✓ type_input as 2nd parameter
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Type and press key
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # Action 1: Type
    element.send_keys(Keys.RETURN)  # Action 2: Press Enter (or TAB, etc.)
    
    # Switch back to default content
    driver.switch_to.default_content()
```

**FOR ALL OTHER ACTIONS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver, *args):  # ✓ No type_input parameter
    import json
    from datas.source_files.xpath_format import format_xpath
    
    # Load XPath from JSON
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Generated logic here (click, select, extract, etc.)
    # ...your logic...
    
    # Switch back to default content
    driver.switch_to.default_content()
```

===============================================================================
NOTE: (MANDATORY)
===============================================================================
- **CRITICAL**: TYPE actions use `def run(driver, type_input, *args):` with type_input as 2nd parameter
- **CRITICAL**: All other actions use `def run(driver, *args):` without type_input
- **CRITICAL**: If user requests multiple actions, generate code for ALL of them - NEVER comment out
- **CRITICAL**: Import Keys if any keyboard action is mentioned
- All import statements must be placed inside the function block.
- The import statement `import json` is mandatory and must always be included.
- The import statement `from datas.source_files.xpath_format import format_xpath` is mandatory and must always be included.
- The xpath formatting with dynamic variables must always follow the pattern:
    # Load dynamic variables from JSON
    dynamic_var_path = "json_info/dynamic_xpath.json"
    with open(dynamic_var_path, "r") as f:
        dynamic_info = json.load(f)
    values = dynamic_info["data"]
    
    # Format XPath with dynamic values using format_xpath
    xpath_pattern = xpath_json[element_name]["xpath"]
    xpath = format_xpath(xpath_pattern, values)
- This pattern is NON-NEGOTIABLE and must be present in every generated code.
- Dynamic variables must ALWAYS be loaded from the JSON file and formatted using format_xpath, NEVER hardcoded.
- **For TYPE actions**: Use the type_input parameter - it's passed as an argument with exact data
- **NEVER** hardcode text in send_keys() - always use the type_input parameter
- ALWAYS switch to iframe BEFORE any element interaction.
- ALWAYS switch back to default_content() AFTER completing all actions.
- The iframe switch is NON-OPTIONAL and must be present in every generated code.
- For logic building using iframe id switch, always prefer EC.presence_of_element_located

===============================================================================
💬 EXAMPLES
===============================================================================

**TYPE Action Examples (with type_input parameter):**
```python
# "type username as admin inside iframe"
def run(driver, type_input, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.send_keys(type_input)  # Will receive "admin"
    # ... switch back ...

# "enter password as welcome#2025 in iframe"
def run(driver, type_input, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.send_keys(type_input)  # Will receive "welcome#2025"
    # ... switch back ...

# "type email from vault in iframe"
def run(driver, type_input, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.send_keys(type_input)  # Will receive vault value
    # ... switch back ...

# "type username and press enter"
def run(driver, type_input, *args):
    from selenium.webdriver.common.keys import Keys
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.send_keys(type_input)
    element.send_keys(Keys.RETURN)
    # ... switch back ...

# "enter text and press tab"
def run(driver, type_input, *args):
    from selenium.webdriver.common.keys import Keys
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.send_keys(type_input)
    element.send_keys(Keys.TAB)
    # ... switch back ...
```

**Non-TYPE Action Examples (without type_input):**
```python
# "click Submit button in iframe"
def run(driver, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    element.click()
    # ... switch back ...

# "select Declined from dropdown in iframe"
def run(driver, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    # dropdown logic
    # ... switch back ...

# "extract table and save to Excel from iframe"
def run(driver, *args):
    # ... load xpath from JSON with dynamic variables using format_xpath ...
    # ... switch to iframe ...
    # table extraction logic
    # ... switch back ...
```

===============================================================================
🔴 CRITICAL TYPE ACTION RULES (READ CAREFULLY)
===============================================================================
When generating code for TYPE actions inside iframes:

1. **Function Signature**: MUST be `def run(driver, type_input, *args):` with type_input as 2nd parameter

2. **Using type_input**: It's a parameter, use it directly
```python
   element.send_keys(type_input)  # ✓ CORRECT
```

3. **What NOT to do**:
   ❌ element.send_keys("enter your text")
   ❌ element.send_keys("type password here")
   ❌ element.send_keys("admin")  # hardcoded
   ❌ type_input = "some value"  # Don't redefine the parameter
   ❌ def run(driver, *args):  # Wrong signature for TYPE action
   ❌ # element.send_keys(Keys.RETURN)  # Uncomment if needed  ← NEVER DO THIS

4. **What TO do**:
   ✓ def run(driver, type_input, *args):  # Correct signature
   ✓ element.send_keys(type_input)  # Use parameter directly
   ✓ from datas.source_files.xpath_format import format_xpath  # Import format_xpath
   ✓ xpath = format_xpath(xpath_pattern, values)  # Use format_xpath function
   ✓ element.send_keys(Keys.RETURN)  # If user requested, include it directly

5. **The Caller Handles**:
   - Reading Type Input Data: {type_input}
   - Vault retrieval (if needed)
   - Passing the value as type_input argument

6. **You Just Use It**:
   - Accept type_input as 2nd parameter (after driver)
   - Pass it to send_keys()
   - Don't hardcode anything
   - Use format_xpath to format the xpath pattern with dynamic values
   - If user asks for keyboard actions, add them WITHOUT commenting

7. **Complete Iframe + Type Pattern**:
```python
   def run(driver, type_input, *args):
       import json
       from datas.source_files.xpath_format import format_xpath
       
       # Load XPath from JSON
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       
       # Load dynamic variables from JSON
       dynamic_var_path = "json_info/dynamic_xpath.json"
       with open(dynamic_var_path, "r") as f:
           dynamic_info = json.load(f)
       values = dynamic_info["data"]
       
       # Format XPath with dynamic values using format_xpath
       xpath_pattern = xpath_json[element_name]["xpath"]
       xpath = format_xpath(xpath_pattern, values)
       
       # Switch to iframe first
       iframe_ids = {iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       # Type using parameter (NEVER hardcode)
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.clear()
       element.send_keys(type_input)

       # Switch back
       driver.switch_to.default_content()
```

8. **Error Prevention**:
   - If error mentioned "missing argument" → Check function has type_input as 2nd parameter
   - If error mentioned "wrong text typed" → Ensure using type_input parameter
   - If error mentioned hardcoded text → Replace with type_input parameter
   - If error mentioned iframe issues → Ensure switch before and after
   - If error mentioned timeout in iframe → Use EC.presence_of_element_located
   - If error mentioned xpath formatting → Ensure using format_xpath function
   - If error mentioned "missing enter/tab action" → User asked for it, don't comment it out

===============================================================================
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
- Full Page HTML (context only): {html_content}
- Variable name: {var_name}
- List of Iframe ID: {iframe_id}
- Type Input Data: {type_input}

===============================================================================
🎯 PRIMARY OBJECTIVE
===============================================================================
Generate **runnable Selenium + Python code** that performs:
- Uses the provided `driver`
- **For TYPE actions**: Function signature is `run(driver, type_input)` with type_input as 2nd argument
- **For NON-TYPE actions**: Function signature is `run(driver)` without type_input
- Uses the given `xpath` loaded dynamically from JSON
- Performs ALL requested browser automation actions WITHOUT EXCEPTION
- Handles any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)
- Does NOT create, modify, or alter any XPath
- Must load the XPath dynamically from the JSON file using the exact pattern below:

    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"

    with open(json_path, "r") as f:
        xpath_json = json.load(f)

    xpath = xpath_json[element_name]["xpath"]

Always use the `xpath` variable for locating elements. Never hardcode any XPath.

===============================================================================
🚨 CRITICAL MULTI-ACTION RULES (MANDATORY)
===============================================================================
**ZERO AUTONOMOUS DECISION-MAKING:**
- Generate code for EVERY action mentioned in the user requirement
- DO NOT comment out any user-requested action
- DO NOT add explanatory comments suggesting "uncomment if needed"
- DO NOT make assumptions about what the user "actually needs"
- If user says "type and press enter" → Generate BOTH actions
- If user says "click and type" → Generate BOTH actions in sequence
- If user says "type, click submit, then press enter" → Generate ALL THREE actions

**Action Combination Detection:**
Detect multi-action patterns from user description:

1. **TYPE + ENTER Key Pattern:**
   Keywords: "type and press enter", "enter text and submit", "type then enter", "input and press enter"
   
   Implementation:
   ```python
   def run(driver, type_input):
       from selenium.webdriver.common.keys import Keys
       import json
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       xpath = xpath_json[element_name]["xpath"]
       
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.clear()
       element.send_keys(type_input)
       element.send_keys(Keys.RETURN)  # ALWAYS include if user requested
       
       driver.switch_to.default_content()
   ```

2. **TYPE + CLICK (Separate Element) Pattern:**
   Keywords: "type username and click login", "enter text and click submit"
   Note: This requires TWO separate function calls (handled by orchestrator)

3. **CLICK + TYPE Pattern:**
   Keywords: "click field and type", "click then enter text"
   
   Implementation:
   ```python
   def run(driver, type_input):
       import json
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       xpath = xpath_json[element_name]["xpath"]
       
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.click()  # Click first
       element.clear()
       element.send_keys(type_input)  # Then type
       
       driver.switch_to.default_content()
   ```

4. **TYPE + TAB Key Pattern:**
   Keywords: "type and press tab", "enter text and tab"
   
   Implementation:
   ```python
   def run(driver, type_input):
       from selenium.webdriver.common.keys import Keys
       import json
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       xpath = xpath_json[element_name]["xpath"]
       
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       element.clear()
       element.send_keys(type_input)
       element.send_keys(Keys.TAB)  # ALWAYS include if user requested
       
       driver.switch_to.default_content()
   ```

5. **SCROLL + CLICK + TYPE Pattern:**
   Keywords: "scroll to field, click and type", "bring into view, click then enter"
   
   Implementation:
   ```python
   def run(driver, type_input):
       import json
       import time
       from selenium.webdriver.common.by import By
       from selenium.webdriver.support.ui import WebDriverWait
       from selenium.webdriver.support import expected_conditions as EC
       
       json_path = "json_info/json_xpath.json"
       element_name = "{var_name}"
       with open(json_path, "r") as f:
           xpath_json = json.load(f)
       xpath = xpath_json[element_name]["xpath"]
       
       iframe_ids={iframe_id}
       for iframe_data in iframe_ids:
           driver.switch_to.frame(iframe_data)
       
       element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
       driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
       time.sleep(0.5)
       element.click()
       element.clear()
       element.send_keys(type_input)
       
       driver.switch_to.default_content()
   ```

**KEYBOARD KEY SUPPORT:**
When user mentions keyboard keys, import and use them:
```python
from selenium.webdriver.common.keys import Keys

# Available keys:
Keys.RETURN / Keys.ENTER  # Enter key
Keys.TAB                   # Tab key
Keys.ESCAPE               # Escape key
Keys.SPACE                # Space bar
Keys.BACKSPACE            # Backspace
Keys.DELETE               # Delete key
Keys.ARROW_DOWN           # Down arrow
Keys.ARROW_UP             # Up arrow
Keys.ARROW_LEFT           # Left arrow
Keys.ARROW_RIGHT          # Right arrow
```

**Example Multi-Action Implementations:**

User: "type username and press enter"
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    # ... load xpath and switch to iframe ...
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.RETURN)  # ✓ BOTH actions executed
    # ... switch back ...
```

User: "click the field and type email"
```python
def run(driver, type_input):
    # ... load xpath and switch to iframe ...
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.click()  # ✓ First action
    element.clear()
    element.send_keys(type_input)  # ✓ Second action
    # ... switch back ...
```

User: "type password, press tab, then press enter"
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    # ... load xpath and switch to iframe ...
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # ✓ First action
    element.send_keys(Keys.TAB)     # ✓ Second action
    element.send_keys(Keys.RETURN)  # ✓ Third action
    # ... switch back ...
```

===============================================================================
🖼️ IFRAME HANDLING RULES (MANDATORY)
===============================================================================
**CRITICAL:** The target element is ALWAYS inside an iframe.

The generated code MUST follow this exact structure:

1. **Switch to all iframe id's one by one from the list** (before any element interaction):
```python
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
```

2. **Perform all element interactions** (click, type, select, extract, etc.)

3. **Switch back to default content** (after completing all actions):
```python
    driver.switch_to.default_content()
```

**Structure Pattern for TYPE actions:**
```python
def run(driver, type_input):  # type_input as 2nd parameter
    # Load XPath from JSON
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Type using the parameter
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)  # Use parameter directly
    
    # Switch back to default content
    driver.switch_to.default_content()
```

**Structure Pattern for NON-TYPE actions:**
```python
def run(driver):  # No type_input parameter
    # Load XPath from JSON
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Perform actions here (click/select/extract/etc.)
    # ...your logic...
    
    # Switch back to default content
    driver.switch_to.default_content()
```

===============================================================================
🧩 ACTION DETECTION RULES
===============================================================================
Detect the action type from the description:

1. **CLICK ACTION**: "click", "press", "submit", "tap", "open"
   - Standard click for buttons, links, any clickable element
   - Wait for element to be present (30 sec max)
   - **Function signature**: `def run(driver):`

2. **TYPE ACTION**: "type", "enter", "input", "fill", "write"
   - For text input fields
   - Wait for element to be visible (30 sec max)
   - **Function signature**: `def run(driver, type_input):`
   - **CRITICAL: Use the type_input parameter directly - it's passed as an argument**
   - **NEVER hardcode or use placeholder text**

3. **DROPDOWN SELECT**: "select", "choose", "pick from dropdown"
   - **Function signature**: `def run(driver):`
   - Analyze element structure
   - Extract option text from description

4. **HOVER ACTION**: "hover", "move cursor to", "mouse over"
   - **Function signature**: `def run(driver):`
   - Scroll into view and hover
   - Wait for element to be present

5. **ELEMENT WAIT**: "wait for element", "check element", "element exists"
   - **Function signature**: `def run(driver):`
   - Check element presence only
   - Return True/False status

6. **SCROLL ACTION**: "scroll to", "scroll into view"
   - **Function signature**: `def run(driver):`
   - Scroll element into view

7. **SCROLL + CLICK COMBINED ACTION**: "scroll to and click", "scroll and click", "scroll to element and click", "bring into view and click"
   - **This is a COMBINED action requiring both scroll and click**
   - Must perform in sequence: scroll → wait → click
   - **Function signature**: `def run(driver):`

8. **GET TEXT/VALUE**: "get text", "extract text", "read text", "fetch value"
   - **Function signature**: `def run(driver):`
   - Wait for element visibility
   - Return element text or value

9. **CLEAR FIELD**: "clear", "empty", "delete content"
   - **Function signature**: `def run(driver):`
   - Wait for element visibility
   - Clear the input field

10. **Other Actions**:
    - "vault", "from vault", "get from vault" → vault retrieval (TYPE action)
    - "screenshot", "capture screen" → browser screenshot (NON-TYPE)
    - "extract", "fetch", "get table", "export" → data extraction (NON-TYPE)

===============================================================================
🔐 VAULT HANDLING RULES (FOR TYPE ACTIONS)
===============================================================================
If vault retrieval is mentioned ("from vault", "get from vault", "retrieve from vault"):
1. This is still a TYPE action, so use `def run(driver, type_input):`
2. The type_input parameter will contain the vault-retrieved value (handled by caller)
3. Simply use the type_input parameter as-is

===============================================================================
⚙️ IMPLEMENTATION RULES
===============================================================================
1. **CRITICAL FUNCTION SIGNATURE RULES**:
   - **TYPE actions ONLY**: `def run(driver, type_input):`
   - **ALL OTHER actions**: `def run(driver):`

2. Use the xpath on the code by below pattern:
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]

3. Do NOT hardcode the XPath anywhere in the code.  
    Always use the `xpath` variable loaded from the JSON file.

4. Required package imports (must be inside the function):
    import json  # MANDATORY
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys  # Add if keyboard keys needed

5. **Type Functionality (CRITICAL):**
   - Function signature: `def run(driver, type_input):`
   - **USE the type_input parameter directly - it's passed as an argument**
   - **NEVER hardcode text values in send_keys()**

6. Dropdown handling rules:
    - If element contains `<select>`, use `Select(element).select_by_visible_text(...)`.
    - If element is a custom async-ui-select or div-based dropdown:
        1. Click on the dropdown trigger element.
        2. Wait for the options container to appear.
        3. Find the correct option by its visible text and click it.

7. **Iframe-Specific Wait Strategy:**
   - For logic building using iframe id switch, always prefer `EC.presence_of_element_located`
   - Avoid `EC.element_to_be_clickable` inside iframes as it may cause issues
   - Use explicit waits with reasonable timeouts (10-30 seconds)

8. Avoid any explanation, markdown, or comments — output must be valid runnable Python.

===============================================================================
💾 NATIVE FILE OPERATION RULES (AUTO-DETECTION)
===============================================================================
Use function signature: `def run(driver):`  # No type_input for file operations

Dynamically detect both file path and format based on the user description.

🧩 Step 1: Path Detection
- If the description includes any of these patterns:
    "in this path", "to path", "save at", "save in", "write it in"
- Extract the full file path.
- If none found, default to "output.xlsx".

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

===============================================================================
📊 TABLE / DIV-CONTAINER EXTRACTION RULES
===============================================================================
When the user requirement mentions:
- "extract table", "get table data", "read table", "fetch table contents"
- "extract grid", "extract div table", "extract container"

Use function signature: `def run(driver):`  # No type_input

===============================================================================
✅ OUTPUT FORMAT (MANDATORY)
===============================================================================

**FOR TYPE ACTIONS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# Add this line ONLY if user requested keyboard keys (enter, tab, etc.):
from selenium.webdriver.common.keys import Keys

def run(driver, type_input):  # ✓ 2 arguments for TYPE action
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Execute ALL user-requested actions
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    # If user requested: element.send_keys(Keys.RETURN)
    # If user requested: element.send_keys(Keys.TAB)
    
    # Switch back to default content
    driver.switch_to.default_content()
```

**FOR ALL OTHER ACTIONS:**
```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def run(driver):  # ✓ 1 argument for non-TYPE actions
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    # Switch to all iframe id's
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    # Execute ALL user-requested actions
    # ...your logic...
    
    # Switch back to default content
    driver.switch_to.default_content()
```

===============================================================================
NOTE: (MANDATORY)
===============================================================================
- **ZERO AUTONOMOUS FILTERING**: Generate code for EVERY action user mentions
- **NO COMMENTING OUT**: Never comment out user-requested functionality
- **NO SUGGESTIONS**: Never add "uncomment if needed" comments
- **EXECUTE EVERYTHING**: If user says "do X and Y", generate code for BOTH
- **CRITICAL**: TYPE actions use `def run(driver, type_input):` with 2 arguments
- **CRITICAL**: All other actions use `def run(driver):` with 1 argument only
- All import statements must be placed inside the function block.
- The import statement `import json` is mandatory and must always be included.
- The xpath loading pattern must always follow the exact format shown above.
- **For TYPE actions**: Use the type_input parameter - it's passed as an argument with exact data
- **NEVER** hardcode text in send_keys() - always use the type_input parameter
- ALWAYS switch to iframe BEFORE any element interaction.
- ALWAYS switch back to default_content() AFTER completing all actions.
- The iframe switch is NON-OPTIONAL and must be present in every generated code.
- For logic building using iframe id switch, always prefer EC.presence_of_element_located

===============================================================================
💬 MULTI-ACTION EXAMPLES
===============================================================================

**Example 1: Type + Enter**
User: "type username and press enter"
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.RETURN)
    
    driver.switch_to.default_content()
```

**Example 2: Click + Type**
User: "click the field and type email address"
```python
def run(driver, type_input):
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.click()
    element.clear()
    element.send_keys(type_input)
    
    driver.switch_to.default_content()
```

**Example 3: Type + Tab + Enter**
User: "enter password, press tab, then press enter"
```python
def run(driver, type_input):
    from selenium.webdriver.common.keys import Keys
    import json
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    element.clear()
    element.send_keys(type_input)
    element.send_keys(Keys.TAB)
    element.send_keys(Keys.RETURN)
    
    driver.switch_to.default_content()
```

**Example 4: Scroll + Click**
User: "scroll to button and click it"
```python
def run(driver):
    import json
    import time
    json_path = "json_info/json_xpath.json"
    element_name = "{var_name}"
    with open(json_path, "r") as f:
        xpath_json = json.load(f)
    xpath = xpath_json[element_name]["xpath"]
    
    iframe_ids={iframe_id}
    for iframe_data in iframe_ids:
        driver.switch_to.frame(iframe_data)
    
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({{behavior: 'smooth', block: 'center'}});", element)
    time.sleep(0.5)
    element.click()
    
    driver.switch_to.default_content()
```

===============================================================================
🔴 FINAL REMINDER: EXECUTE ALL USER ACTIONS
===============================================================================
- If user says "type and press enter" → Generate code for BOTH
- If user says "click and type" → Generate code for BOTH
- If user says "scroll, click, type, tab, enter" → Generate code for ALL FIVE
- NEVER decide what's "needed" or "optional"
- NEVER comment out any action
- NEVER suggest "uncomment if needed"
- USER REQUIREMENT IS LAW - Execute everything requested

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

