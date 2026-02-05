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
    # if not co_ordinates_status and not img_status and not region_status:
    #     element = driver.find_element(By.XPATH, xpath)
    #     outer_html = element.get_attribute("outerHTML")
    
    
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run()` that performs the described UI action using `pyautogui` for mouse and keyboard automation. 
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run(drier):` and its body. Do NOT include any function calls, test examples, or extra output.
                3. No argument should accepts in the run() function
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
                5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                7. Include concise inline comments explaining key steps, imports, and assumptions.
                8. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {desc} → will be replaced with the user's action description (used for the logic and inline comments).
            - {var_name} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic according to {desc}):
            def run():
                import pyautogui
                import time
                import json
                import os


                json_path = "json_info/citrix_data.json"

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
                json_path = "json_info/citrix_data.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get({{element_name}}) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """


    elif img_status :
        prompt = f"""
        You will be given:
        - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP").
        - json_path: Path to the JSON file containing image information.
        - var_name: The key used to retrieve the image path from the JSON file.

        Task:
        Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
        The function must:
        1. Always be named `run`.
        2. No argument should be accepted.
        3. Load the image path from JSON using:
        import json
        json_path = "json_info/citrix_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            json_info = json.load(f)
        image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"

        4. CRITICAL - Wait for Image (MANDATORY FOR ALL ACTIONS):
        - Before performing ANY action (click, type, extract, etc.), you MUST wait for the image to appear on screen
        - Maximum timeout: 20 seconds
        - Poll interval: 0.5 seconds (check every half second)
        - Use a while loop with time tracking to wait for the image
        - Only proceed with the action once the image is located
        - If image is not found within 20 seconds, return False with appropriate error message

        5. Type Functionality:
        - If the User req : {desc} is about to type element on field means 
        - For Example : type password as "welcome#2025" is User req means the generated code should be like Typing this data welcome#2025 not like default values like type your username here or any values

        6. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
        - If the description implies a click (e.g., "click login button"), generate wait + click code.
        - If the description implies a typing action (e.g., "type username as www"), generate wait + typing code — do not include click/extract logic.
        - If the description implies a text extraction action (e.g., "extract OTP from image"), generate wait + text extraction code — not click/type code.
        - If the description implies scrolling (e.g., "scroll down", "scroll to bottom"), generate wait + scroll code.
        - If the description implies hovering (e.g., "hover over menu"), generate wait + hover code.

        7. Do not use the description: {desc} inside the code. Create preferred logic based on analyzed description.

        8. Use pyautogui.locateOnScreen(image_path, confidence=confidence) for image matching.

        9. Include proper error handling (e.g., image not found after timeout).

        10. For typing actions, extract the text to type from the description intelligently.

        Output:
        Return only the complete Python function code — no extra text, explanation, or commentary.

        ================================================================================
        MANDATORY WAIT PATTERN (APPLY TO ALL ACTIONS)
        ================================================================================

        Every generated function MUST include this wait logic before performing the action:

        ```python
        # Wait for image to appear (max 20 seconds)
        timeout = 20
        start_time = time.time()
        location = None

        while time.time() - start_time < timeout:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location is not None:
                break
            time.sleep(0.5)

        if location is None:
            print(f"Image not found on screen after {{timeout}} seconds!")
            return False
        ```

        ================================================================================
        EXAMPLE TEMPLATES
        ================================================================================

        Example 1: Click Action with Wait

        def run():
            import json
            import time
            import pyautogui
            
            json_path = "json_info/citrix_data.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            confidence = 0.8
            
            # Wait for image to appear (max 20 seconds)
            timeout = 20
            start_time = time.time()
            location = None
            
            while time.time() - start_time < timeout:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is not None:
                    break
                time.sleep(0.5)
            
            if location is None:
                print(f"Image not found on screen after {{timeout}} seconds!")
                return False
            
            # Perform click action
            x, y = pyautogui.center(location)
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            return True


        Example 2: Type Action with Wait (e.g., desc = "type username as admin123")

        def run():
            import json
            import time
            import pyautogui
            
            json_path = "json_info/citrix_data.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            confidence = 0.8
            
            # Wait for image to appear (max 20 seconds)
            timeout = 20
            start_time = time.time()
            location = None
            
            while time.time() - start_time < timeout:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is not None:
                    break
                time.sleep(0.5)
            
            if location is None:
                print(f"Image not found on screen after {{timeout}} seconds!")
                return False
            
            # Perform type action
            x, y = pyautogui.center(location)
            pyautogui.click(x, y)
            time.sleep(0.3)
            pyautogui.typewrite("admin123", interval=0.1)
            return True


        Example 3: Text Extraction with Wait (e.g., desc = "extract OTP from field")

        def run():
            import json
            import time
            import pyautogui
            import pytesseract
            from PIL import Image
            
            json_path = "json_info/citrix_data.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            confidence = 0.8
            
            # Wait for image to appear (max 20 seconds)
            timeout = 20
            start_time = time.time()
            location = None
            
            while time.time() - start_time < timeout:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is not None:
                    break
                time.sleep(0.5)
            
            if location is None:
                print(f"Image not found on screen after {{timeout}} seconds!")
                return None
            
            # Perform text extraction
            x, y, w, h = location
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            extracted_text = pytesseract.image_to_string(screenshot).strip()
            return extracted_text


        Example 4: Scroll Action with Wait (e.g., desc = "scroll down to view more")

        def run():
            import json
            import time
            import pyautogui
            
            json_path = "json_info/citrix_data.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            confidence = 0.8
            
            # Wait for image to appear (max 20 seconds)
            timeout = 20
            start_time = time.time()
            location = None
            
            while time.time() - start_time < timeout:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is not None:
                    break
                time.sleep(0.5)
            
            if location is None:
                print(f"Image not found on screen after {{timeout}} seconds!")
                return False
            
            # Perform scroll action
            x, y = pyautogui.center(location)
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.scroll(-3)  # Negative for scroll down, positive for scroll up
            return True


        Example 5: Hover Action with Wait (e.g., desc = "hover over menu item")

        def run():
            import json
            import time
            import pyautogui
            
            json_path = "json_info/citrix_data.json"
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            
            image_path = f"{proj_fol}/{task_fol}/images/{{json_info[{var_name}]}}"
            confidence = 0.8
            
            # Wait for image to appear (max 20 seconds)
            timeout = 20
            start_time = time.time()
            location = None
            
            while time.time() - start_time < timeout:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location is not None:
                    break
                time.sleep(0.5)
            
            if location is None:
                print(f"Image not found on screen after {{timeout}} seconds!")
                return False
            
            # Perform hover action
            x, y = pyautogui.center(location)
            pyautogui.moveTo(x, y, duration=0.5)
            return True

        ================================================================================
        CRITICAL REMINDERS
        ================================================================================

        1. ALWAYS include the 20-second wait logic before ANY action
        2. Poll every 0.5 seconds during the wait
        3. Return False if image not found after timeout
        4. Only proceed with the action after image is successfully located
        5. Use appropriate confidence level (default 0.8)
        6. Include proper imports: json, time, pyautogui (and others as needed)
        7. Return only the function code - no explanations or markdown
        8. The function must always be named `run` with no arguments

        Generate the function code now:
        """
    elif region_status :
        prompt=f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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
            json_path = "json_info/citrix_data.json"
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
        json_path="json_info/citrix_data.json"
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
        json_path="json_info/citrix_data.json"
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

def fallback_code_correction(desc,xpath,file_path,var_name,driver,userid,error_info):

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
    # WebDriverWait(driver, 20).until(
    #     lambda d: d.execute_script("return document.readyState") == "complete"
    # )
    html_content=""
    outer_html=""
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
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
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
            Generate a corrected, single, valid Python function definition named `run()` that fixes the error and performs the described UI action using `pyautogui` for mouse and keyboard automation.
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
                3. No argument should accepts in the run() function
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
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
            def run():
                import pyautogui
                import time
                import json
                import os


                json_path = "json_info/citrix_data.json"

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
                json_path = "json_info/citrix_data.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get(element_name) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """


    elif img_status :
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
2. No argument should be accepted.
3. Load the image path from JSON using:
   import json
   json_path = "json_info/citrix_data.json"
   with open(json_path, "r", encoding="utf-8") as f:
       json_info = json.load(f)
   element_name = {var_name}
   image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"

4. CRITICAL - Wait for Image (MANDATORY FOR ALL ACTIONS):
   - Before performing ANY action (click, type, extract, etc.), you MUST wait for the image to appear on screen
   - Maximum timeout: 20 seconds
   - Poll interval: 0.5 seconds (check every half second)
   - Use a while loop with time tracking to wait for the image
   - Only proceed with the action once the image is located
   - If image is not found within 20 seconds, return False with appropriate error message

5. Analyze the description ({desc}) intelligently and generate only the code relevant to that specific action:
   - If the description implies a click (e.g., "click login button"), generate wait + click code.
   - If the description implies a typing action (e.g., "type username as www"), generate wait + typing code — do not include click/extract logic.
   - If the description implies a text extraction action (e.g., "extract OTP from image"), generate wait + text extraction code — not click/type code.
   - If the description implies scrolling (e.g., "scroll down", "scroll to bottom"), generate wait + scroll code.
   - If the description implies hovering (e.g., "hover over menu"), generate wait + hover code.

6. Do not use the description: {desc} inside the code. Create preferred logic based on analyzing the description.

7. Use pyautogui.locateOnScreen(image_path, confidence=confidence) for image matching.

8. Include proper error handling (e.g., image not found after timeout).

9. For typing actions, extract the text to type from the description intelligently.

10. Address and fix the specific error from {error_detail}. Common error fixes:
    - If error is about missing imports, add the required import statements
    - If error is about undefined variables, ensure all variables are properly defined
    - If error is about image not found, ensure the wait logic is properly implemented
    - If error is about indentation, fix the indentation to be consistent
    - If error is about syntax, correct the syntax error
    - If error is about file paths, ensure proper path construction

Output:
Return only the complete Python function code — no extra text, explanation, or commentary.

================================================================================
MANDATORY WAIT PATTERN (APPLY TO ALL ACTIONS)
================================================================================

Every generated function MUST include this wait logic before performing the action:

```python
# Wait for image to appear (max 20 seconds)
timeout = 20
start_time = time.time()
location = None

while time.time() - start_time < timeout:
    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
    if location is not None:
        break
    time.sleep(0.5)

if location is None:
    print(f"Image not found on screen after {{timeout}} seconds!")
    return False
```

================================================================================
EXAMPLE TEMPLATES
================================================================================

Example 1: Click Action with Wait (Corrected)

def run():
    import json
    import time
    import pyautogui
    
    json_path = "json_info/citrix_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    
    element_name = {var_name}
    image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
    confidence = 0.8
    
    # Wait for image to appear (max 20 seconds)
    timeout = 20
    start_time = time.time()
    location = None
    
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location is not None:
            break
        time.sleep(0.5)
    
    if location is None:
        print(f"Image not found on screen after {{timeout}} seconds!")
        return False
    
    # Perform click action
    x, y = pyautogui.center(location)
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    return True


Example 2: Type Action with Wait (Corrected - e.g., desc = "type username as admin123")

def run():
    import json
    import time
    import pyautogui
    
    json_path = "json_info/citrix_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    
    element_name = {var_name}
    image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
    confidence = 0.8
    
    # Wait for image to appear (max 20 seconds)
    timeout = 20
    start_time = time.time()
    location = None
    
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location is not None:
            break
        time.sleep(0.5)
    
    if location is None:
        print(f"Image not found on screen after {{timeout}} seconds!")
        return False
    
    # Perform type action
    x, y = pyautogui.center(location)
    pyautogui.click(x, y)
    time.sleep(0.3)
    pyautogui.typewrite("admin123", interval=0.1)
    return True


Example 3: Text Extraction with Wait (Corrected - e.g., desc = "extract OTP from field")

def run():
    import json
    import time
    import pyautogui
    import pytesseract
    from PIL import Image
    
    json_path = "json_info/citrix_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    
    element_name = {var_name}
    image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
    confidence = 0.8
    
    # Wait for image to appear (max 20 seconds)
    timeout = 20
    start_time = time.time()
    location = None
    
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location is not None:
            break
        time.sleep(0.5)
    
    if location is None:
        print(f"Image not found on screen after {{timeout}} seconds!")
        return None
    
    # Perform text extraction
    x, y, w, h = location
    screenshot = pyautogui.screenshot(region=(x, y, w, h))
    extracted_text = pytesseract.image_to_string(screenshot).strip()
    return extracted_text


Example 4: Scroll Action with Wait (Corrected - e.g., desc = "scroll down to view more")

def run():
    import json
    import time
    import pyautogui
    
    json_path = "json_info/citrix_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    
    element_name = {var_name}
    image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
    confidence = 0.8
    
    # Wait for image to appear (max 20 seconds)
    timeout = 20
    start_time = time.time()
    location = None
    
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location is not None:
            break
        time.sleep(0.5)
    
    if location is None:
        print(f"Image not found on screen after {{timeout}} seconds!")
        return False
    
    # Perform scroll action
    x, y = pyautogui.center(location)
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.scroll(-3)  # Negative for scroll down, positive for scroll up
    return True


Example 5: Hover Action with Wait (Corrected - e.g., desc = "hover over menu item")

def run():
    import json
    import time
    import pyautogui
    
    json_path = "json_info/citrix_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        json_info = json.load(f)
    
    element_name = {var_name}
    image_path = f"{proj_fol}/{task_fol}/images/{{json_info[element_name]}}"
    confidence = 0.8
    
    # Wait for image to appear (max 20 seconds)
    timeout = 20
    start_time = time.time()
    location = None
    
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
        if location is not None:
            break
        time.sleep(0.5)
    
    if location is None:
        print(f"Image not found on screen after {{timeout}} seconds!")
        return False
    
    # Perform hover action
    x, y = pyautogui.center(location)
    pyautogui.moveTo(x, y, duration=0.5)
    return True

================================================================================
CRITICAL REMINDERS
================================================================================

1. ALWAYS include the 20-second wait logic before ANY action
2. Poll every 0.5 seconds during the wait
3. Return False if image not found after timeout
4. Only proceed with the action after image is successfully located
5. Use appropriate confidence level (default 0.8)
6. Include proper imports: json, time, pyautogui (and others as needed)
7. Return only the function code - no explanations or markdown
8. The function must always be named `run` with no arguments
9. Ensure element_name = {var_name} is used before accessing json_info
10. Analyze the error in {error_detail} and ensure the corrected code addresses the root cause
11. Keep the function self-contained and robust
12. Do not send any additional explanation or console text beyond the function definition itself

Notes / Constraints:
- Carefully analyze the error in {error_detail} and ensure the corrected code addresses the root cause
- If the error is about missing wait logic, add the mandatory 20-second wait pattern
- If the error is about imports, ensure all necessary imports are included
- If the error is about syntax, correct the syntax while maintaining the wait pattern
- Ensure element_name = {var_name} is used before accessing json_info
- Keep the function self-contained and robust

Generate the corrected function code now:
"""

    elif region_status :
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
            2. Always accept an argument `` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

        **Note**: These are provided for context to help you understand the element structure.
        The XPath must be loaded dynamically from JSON (see below). The outer HTML and full page HTML
        help you understand element type, attributes, and page structure to generate correct logic.

        ===============================================================================
        🎯 PRIMARY OBJECTIVE
        ===============================================================================
        Generate **corrected, runnable Selenium + Python code** that:
        - Fixes the error from {error_detail}
        - Uses the provided `driver`
        - Loads the XPath dynamically from JSON (never hardcodes it)
        - Performs the required browser automation actions
        - Handles any requested **native Python operations** (file handling, Excel/CSV/JSON export, screenshots, etc.)
        - Does NOT create, modify, or alter any XPath
        - Must load the XPath dynamically from the JSON file using the exact pattern below:

            import json
            json_path = "json_info/citrix_data.json"
            element_name = {var_name}

            with open(json_path, "r") as f:
                xpath_json = json.load(f)

            xpath = xpath_json[element_name]

        Always use the `xpath` variable for locating elements. Never hardcode any XPath.

        ===============================================================================
        🧩 ACTION DETECTION RULES
        ===============================================================================
        Detect the action type from the description:
        - "type", "enter", "input" → typing actions
        - "click", "press", "submit" → clicking
        - "select", "choose", "pick" → dropdown selection
        - "extract", "read", "get", "fetch" → data extraction
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
            var_name = vault_data[vault_keys[6]] if len(vault_keys) >= 7 else ""
        4. Use var_name for typing into the field.
    
    ===============================================================================
    ⚙️ IMPLEMENTATION RULES
    ===============================================================================
    1. The function name must be exactly `run(driver)`.
    2. Use the xpath on the code by below pattern:
        import json
        json_path="json_info/citrix_data.json"
        element_name={var_name}
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath=xpath_json[element_name]

    3. Do NOT hardcode the XPath anywhere in the code.  
        Always use the `xpath` variable loaded from the JSON file.
    4. Don't miss the needed package imports:
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

    6. **Address the specific error from {error_detail}** - analyze what went wrong and fix it.
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

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC

    def run(driver):
        import json
        json_path="json_info/citrix_data.json"
        element_name="{var_name}"
        with open(json_path, "r") as f:
            xpath_json = json.load(f)
        xpath=xpath_json[element_name]
        # Generated corrected logic here
    
    ===============================================================================
    NOTE: (MANDATORY)
    ===============================================================================
    - All import statements must be placed inside the `run(driver)` function block.
    - The import statement `import json` is mandatory and must always be included.
    - Analyze the error from {error_detail} and ensure the corrected code addresses the root cause.
    - Use the outer HTML ({outer_html}) and full page HTML ({html_content}) as reference to understand:
        * Element type (input, select, div, button, etc.)
        * Element attributes (class, id, data-*, etc.)
        * Parent/child relationships
        * Whether it's a standard HTML element or custom component
    - The current element XPath ({xpath}) should guide you on element location strategy.
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
        

    # if region_status:
    #     from region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run()` that extracts text from the UI element at the specified coordinates and returns it.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
            3. No argument should accepts in the run() function
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{{var_name}}` key.
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

            def run():
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Define JSON file path
                json_path = "json_info/citrix_data.json"
                
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


    elif img_status :
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "extract text from field", "get OTP from screen", "read value from label").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python Citrix automation function using pyautogui and pytesseract packages to extract text from the UI element identified by the image.

            The function must:
            1. Always be named `run`.
            2. Always accept an argument `` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/citrix_data.json"
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

    elif region_status :
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
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                
                json_path = "json_info/citrix_data.json"
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
from region_img_table_extract import gemini_image_response,capture_region
def run():
    desc="{desc}"
    json_path = "json_info/citrix_data.json"
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

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
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
            Generate a corrected, single, valid Python function definition named `run()` that fixes the error and extracts text from the UI element at the specified coordinates, returning the extracted text as a string.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
            3. No argument should accepts in the run() function
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
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

            def run():
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Define JSON file path
                json_path = "json_info/citrix_data.json"
                
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


    elif img_status :
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
            2. Always accept an argument `` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/citrix_data.json"
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
    elif region_status :
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
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                
                json_path = "json_info/citrix_data.json"
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



    if region_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""
import pandas as pd
import json
from region_img_table_extract import gemini_image_response,capture_region
def run():
    desc="{desc}"
    json_path = "json_info/citrix_data.json"
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
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run()` that extracts text from the UI element at the specified coordinates and returns it.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
            3. No argument should accepts in the run() function
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{{var_name}}` key.
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

            def run():
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Define JSON file path
                json_path = "json_info/citrix_data.json"
                
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


    elif img_status :
        prompt=""

    elif region_status :
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP", "extract table data").
            - json_path: Path to the JSON file containing bounding box information.
            - var_name: The key used to retrieve the bounding box coordinates from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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
            - Checks if the element exists on the page
            - Returns True if element exists, False if it doesn't

            CRITICAL: Must load the XPath dynamically from the JSON file using this exact pattern:

                import json
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                
                json_path = "json_info/citrix_data.json"
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
    if not img_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""import time
import pyautogui
import json
def run():
    timeout=20
    confidence=0.9
    element_name="{var_name}"
    start_time = time.time()
    json_path="json_info/citrix_data.json"
    task_info_path="json_info/task_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(task_info_path, "r", encoding="utf-8") as f:
        task_info = json.load(f)
    proj_name=task_info["Proj_file_name"]
    task_name=task_info["Task_file_name"]
    path=f"{{proj_name}}/{{task_name}}/images/{{data[element_name]}}"
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            try:
                pyautogui.moveTo(center)
                return True          
            except:
                pass

        time.sleep(0.3)

    return False
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
        

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
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
            Generate a corrected, single, valid Python function definition named `run()` that fixes the error and extracts text from the UI element at the specified coordinates, returning the extracted text as a string.

            The generated code must:
            1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
            2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
            3. No argument should accepts in the run() function
            4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
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

            def run():
                import pyautogui
                import pyperclip
                import time
                import json
                import os
                
                # Define JSON file path
                json_path = "json_info/citrix_data.json"
                
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


    elif img_status :
        prompt=""
    elif region_status :
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
            2. Always accept an argument `` (even if unused).
            3. Load the bounding box coordinates from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                import pytesseract
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import time
                import pyautogui
                from PIL import Image
                
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                
                json_path = "json_info/citrix_data.json"
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



    if not img_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""import time
import pyautogui
import json
def run():
    timeout=20
    confidence=0.9
    element_name="{var_name}"
    start_time = time.time()
    json_path="json_info/citrix_data.json"
    task_info_path="json_info/task_info.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(task_info_path, "r", encoding="utf-8") as f:
        task_info = json.load(f)
    proj_name=task_info["Proj_file_name"]
    task_name=task_info["Task_file_name"]
    path=f"{{proj_name}}/{{task_name}}/images/{{data[element_name]}}"
    while time.time() - start_time < timeout:
        location = pyautogui.locateOnScreen(path, confidence=confidence)
        if location:
            center = pyautogui.center(location)
            try:
                pyautogui.moveTo(center)
                return True          
            except:
                pass

        time.sleep(0.3)

    return False
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

def code_correction_table_extract(desc,xpath,file_path,var_name,driver,userid):
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
    #     from region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)
    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
        prompt = f"""
                    You will be given:
                    - desc: a short natural-language description of the user's intended UI action (string).
                    - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
                    - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

                    Task:
                    Generate a single, valid Python function definition named `run()` that performs the described UI action using `pyautogui` for mouse and keyboard automation. 
                    The generated code must:
                        1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                        2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
                        3. No argument should accepts in the run() function
                        4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
                        5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                        6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                        7. Include concise inline comments explaining key steps, imports, and assumptions.
                        8. Do NOT print or return any extra explanatory text — only generate the function code.

                    Placeholders:
                    - {desc} → will be replaced with the user's action description (used for the logic and inline comments).
                    - {var_name} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

                    Sample output format (follow this pattern; adapt logic according to {desc}):
                    def run():
                        import pyautogui
                        import time
                        import json
                        import os
                        json_path = "json_info/citrix_data.json"

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
                        json_path = "json_info/citrix_data.json"
                        with open(json_path, "r", encoding="utf-8") as f:
                            json_info = json.load(f)
                        coordinates_points = json_info.get({{element_name}}) 
                    - Keep the function self-contained and robust.
                    - Do not send any additional explanation or console text beyond the function definition itself.
                """


    elif img_status :
        prompt = f"""
            You will be given:
            - desc: The user's requirement describing the table extraction task (e.g., "extract table from invoice", "get data table from screenshot").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python function that extracts table data from an image and returns it as a pandas DataFrame.

            The function must:
            1. Always be named `run`.
            2. No argument should accepts in the run() function
            3. All code logic must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import pandas as pd
                import cv2
                import pytesseract
                from PIL import Image
                
                # Load image path from JSON
                json_path = "json_info/citrix_data.json"
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
            - The function signature must be: def run():
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

    elif region_status :
        prompt = """"""
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
            - Locates the table element on the page
            - Analyzes the table structure from outer HTML
            - Extracts all table data (headers and rows) from current page
            - **Detects pagination and extracts data from ALL pages if pagination exists**
            - Identifies "Next" button or page navigation elements automatically
            - Returns a combined pandas DataFrame with data from all pages

            CRITICAL: Must load the XPath dynamically from the JSON file using this exact pattern:

                import json
                json_path = "json_info/citrix_data.json"
                element_name = {var_name}
                
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                
                xpath = xpath_json[element_name]

            Always use the `xpath` variable for locating elements. Never hardcode any XPath.

            ===============================================================================
            🧩 TABLE EXTRACTION WITH PAGINATION RULES
            ===============================================================================
            The user requirement is about extracting table data from a web page with potential pagination.

            Implementation steps:
            1. Load XPath from JSON file using the pattern above
            2. Locate the table element using WebDriverWait with the loaded XPath
            3. Analyze the outer HTML structure to identify:
            - Table headers (<th> or first <tr> elements)
            - Table rows (<tr> elements)
            - Table cells (<td> elements)
            4. Extract data from the current page
            5. **Detect pagination elements:**
            - Look for "Next" button (common patterns: button with text "Next", "›", "→", ">")
            - Look for page numbers (1, 2, 3, etc.)
            - Common XPaths for next button:
                * //button[contains(text(), 'Next')]
                * //a[contains(text(), 'Next')]
                * //button[contains(@class, 'next')]
                * //a[contains(@class, 'next')]
                * //li[contains(@class, 'next')]//a
                * //*[contains(@aria-label, 'Next')]
                * //button[@title='Next page']
                * //*[text()='›' or text()='→' or text()='>']
            6. **If pagination exists:**
            - Click next button
            - Wait for page to load
            - Extract data from new page
            - Repeat until no more pages (next button disabled/not found)
            7. **Combine all data** into a single DataFrame
            8. Return the complete DataFrame

            ===============================================================================
            📊 TABLE STRUCTURE ANALYSIS
            ===============================================================================
            Based on the provided outer_html: {outer_html}
            And full page HTML: {html_content}

            Analyze the structure to identify:
            - Header row location (usually <thead> or first <tr> with <th> tags)
            - Data rows location (usually <tbody> or <tr> tags with <td> tags)
            - Column count and structure
            - **Pagination elements location:**
            * Next button location and attributes
            * Page number indicators
            * Disabled state indicators (for last page detection)

            Common table patterns:
            1. Standard HTML table: <table><thead><tr><th>...</th></tr></thead><tbody><tr><td>...</td></tr></tbody></table>
            2. Simple table: <table><tr><th>...</th></tr><tr><td>...</td></tr></table>
            3. Div-based table: <div class="table"><div class="row"><div class="cell">...</div></div></div>

            Common pagination patterns:
            1. Button: <button class="next">Next</button>
            2. Link: <a href="#" class="next">Next</a>
            3. List item: <li class="next"><a>›</a></li>
            4. Icon: <button><span>→</span></button>

            ===============================================================================
            ⚙️ IMPLEMENTATION RULES
            ===============================================================================
            1. The function name must be exactly `run(driver)`.
            2. Load XPath using this exact pattern:
                import json
                json_path = "json_info/citrix_data.json"
                element_name = {var_name}
                with open(json_path, "r") as f:
                    xpath_json = json.load(f)
                xpath = xpath_json[element_name]

            3. Do NOT hardcode the XPath anywhere in the code.
            4. Required imports (must be inside the function):
                import json  # MANDATORY
                import pandas as pd  # MANDATORY
                import time  # For wait between page loads
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

            5. Use WebDriverWait to locate the table element
            6. Extract table headers and data rows systematically
            7. **Implement pagination logic with multiple fallback XPaths**
            8. **Add proper wait time between page navigation (time.sleep)**
            9. **Detect when pagination ends** (no more next button or button disabled)
            10. Always return a pandas DataFrame (empty DataFrame on failure)
            11. Handle all exceptions gracefully
            12. Avoid any explanation, markdown, or comments — output must be valid runnable Python

            ===============================================================================
            ✅ OUTPUT FORMAT (MANDATORY)
            ===============================================================================
            Output must exactly follow this format:

            def run(driver):
                import json
                import pandas as pd
                import time
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
                
                json_path = "json_info/citrix_data.json"
                element_name = "{var_name}"
                
                try:
                    with open(json_path, "r") as f:
                        xpath_json = json.load(f)
                except Exception as e:
                    print(f"Error loading JSON file: {{e}}")
                    return pd.DataFrame()
                
                xpath = xpath_json.get(element_name)
                
                if not xpath:
                    print(f"XPath for '{{element_name}}' not found in JSON")
                    return pd.DataFrame()
                
                all_data = []
                headers = []
                page_number = 1
                
                # Common XPaths for Next button (in priority order)
                next_button_xpaths = [
                    "//button[contains(translate(text(), 'NEXT', 'next'), 'next')]",
                    "//a[contains(translate(text(), 'NEXT', 'next'), 'next')]",
                    "//button[contains(@class, 'next')]",
                    "//a[contains(@class, 'next')]",
                    "//li[contains(@class, 'next')]//a",
                    "//button[contains(@aria-label, 'Next')]",
                    "//a[contains(@aria-label, 'Next')]",
                    "//button[@title='Next page']",
                    "//*[text()='›' or text()='→' or text()='>' or text()='Next']",
                    "//button[contains(@class, 'pagination')]//following-sibling::button",
                    "//nav//button[last()]",
                    "//ul[contains(@class, 'pagination')]//li[last()]//a"
                ]
                
                while True:
                    try:
                        print(f"Extracting data from page {{page_number}}...")
                        
                        # Wait for table element to be present
                        table_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, xpath))
                        )
                        
                        # Extract table headers (only once from first page)
                        if not headers:
                            try:
                                header_elements = table_element.find_elements(By.XPATH, ".//thead//th | .//tr[1]//th")
                                if header_elements:
                                    headers = [header.text.strip() for header in header_elements]
                                else:
                                    # If no <th>, use first row as headers
                                    first_row = table_element.find_elements(By.XPATH, ".//tr[1]//td")
                                    headers = [cell.text.strip() for cell in first_row]
                                    # Skip first row in data extraction if used as header
                            except Exception as e:
                                print(f"Error extracting headers: {{e}}")
                        
                        # Extract table rows from current page
                        try:
                            # Get all data rows (skip header row if it was <th>)
                            row_elements = table_element.find_elements(By.XPATH, ".//tbody//tr | .//tr[position()>1]")
                            
                            for row in row_elements:
                                cells = row.find_elements(By.XPATH, ".//td")
                                row_data = [cell.text.strip() for cell in cells]
                                if row_data and any(row_data):  # Only add non-empty rows
                                    all_data.append(row_data)
                            
                            print(f"Extracted {{len([r for r in row_elements if r.find_elements(By.XPATH, './/td')])}} rows from page {{page_number}}")
                        except Exception as e:
                            print(f"Error extracting rows from page {{page_number}}: {{e}}")
                        
                        # Try to find and click Next button
                        next_button = None
                        next_button_found = False
                        
                        for next_xpath in next_button_xpaths:
                            try:
                                next_button = WebDriverWait(driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, next_xpath))
                                )
                                
                                # Check if button is disabled
                                if next_button.get_attribute("disabled") or \
                                "disabled" in next_button.get_attribute("class") or \
                                next_button.get_attribute("aria-disabled") == "true":
                                    print("Next button is disabled - reached last page")
                                    break
                                
                                next_button_found = True
                                print(f"Found next button using XPath: {{next_xpath}}")
                                break
                            except:
                                continue
                        
                        # If no next button found or it's disabled, we're done
                        if not next_button_found or not next_button:
                            print("No more pages to extract")
                            break
                        
                        # Click next button and wait for page to load
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(0.5)
                            next_button.click()
                            time.sleep(2)  # Wait for page to load
                            page_number += 1
                        except ElementClickInterceptedException:
                            try:
                                driver.execute_script("arguments[0].click();", next_button)
                                time.sleep(2)
                                page_number += 1
                            except Exception as e:
                                print(f"Could not click next button: {{e}}")
                                break
                        except Exception as e:
                            print(f"Error navigating to next page: {{e}}")
                            break
                            
                    except (TimeoutException, NoSuchElementException) as e:
                        print(f"Table element not found on page {{page_number}}: {{e}}")
                        break
                    except Exception as e:
                        print(f"Error during pagination on page {{page_number}}: {{e}}")
                        break
                
                # Create final DataFrame from all collected data
                try:
                    if all_data:
                        if headers and len(headers) == len(all_data[0]):
                            df = pd.DataFrame(all_data, columns=headers)
                        else:
                            df = pd.DataFrame(all_data)
                        
                        print(f"Successfully extracted table with {{len(df)}} total rows and {{len(df.columns)}} columns from {{page_number}} pages")
                        return df
                    else:
                        print("No table data found across all pages")
                        return pd.DataFrame()
                except Exception as e:
                    print(f"Error creating final DataFrame: {{e}}")
                    return pd.DataFrame()

            MANDATORY CONDITION:
            - It must return a pandas DataFrame compulsory
            - Return populated DataFrame with data from ALL pages if pagination exists
            - Return empty DataFrame (pd.DataFrame()) if extraction fails or errors occur
            - Always analyze the outer_html and full HTML to determine pagination strategy
            - Combine data from all pages into a single DataFrame

            ===============================================================================
            NOTE: (MANDATORY)
            ===============================================================================
            - All import statements must be placed inside the `run(driver)` function block
            - The import statements `import json`, `import pandas as pd`, and `import time` are mandatory
            - The function must RETURN a DataFrame, not print it
            - Use WebDriverWait with appropriate timeout (10 seconds recommended)
            - Handle TimeoutException, NoSuchElementException, and ElementClickInterceptedException
            - Return empty DataFrame for any exceptions or errors
            - Extract both headers and data rows from the table
            - **Implement multiple fallback XPaths for next button detection**
            - **Add proper wait times between page loads (time.sleep)**
            - **Detect disabled state of next button to stop pagination**
            - **Scroll to next button before clicking**
            - **Use JavaScript click as fallback if regular click fails**
            - Handle various table structures (thead/tbody, simple tr/td, div-based)
            - Clean extracted text (strip whitespace)
            - Match column count between headers and data rows
            - Extract headers only once from the first page
            - Accumulate all data across pages before creating final DataFrame

            ===============================================================================
            🔄 PAGINATION DETECTION LOGIC
            ===============================================================================
            The code automatically detects pagination by:
            1. Trying multiple common XPaths for "Next" button
            2. Checking if button exists and is clickable
            3. Checking if button is disabled (indicates last page)
            4. Clicking and waiting for new page to load
            5. Continuing until no more pages or error occurs

            Common pagination indicators:
            - "Next" text in buttons/links
            - Arrow symbols: ›, →, >
            - Class names: "next", "pagination-next"
            - ARIA labels: "Next page"
            - Disabled state on last page

            ===============================================================================
            💬 EXAMPLES OF USER REQUIREMENTS (TABLE EXTRACTION WITH PAGINATION)
            ===============================================================================
            - "extract table data from all pages"
            - "get complete table with pagination"
            - "scrape all pages of data table"
            - "extract table and handle next page navigation"
            - "get all transaction records across multiple pages"
            - "extract product listing from all pages"
            - "scrape entire paginated table"
            - "get all data handling page navigation"
            ===============================================================================
            """
    if not region_status:
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""
import pandas as pd
import json
from region_img_table_extract import gemini_image_response,capture_region
def run():
    desc="{desc}"
    json_path = "json_info/citrix_data.json"
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
    
    # if region_status:
    #     from region_img_table_extract import gemini_image_response,capture_region
    #     img_path=capture_region(xpath)
    #     ret_data=gemini_image_response(img_path,desc)

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status:
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run()` that performs the described UI action using `pyautogui` for mouse and keyboard automation. 
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run():` and its body. Do NOT include any function calls, test examples, or extra output.
                3. No argument should accepts in the run() function
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/citrix_data.json"` using the provided `{var_name}` key.
                5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                7. Include concise inline comments explaining key steps, imports, and assumptions.
                8. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {desc} → will be replaced with the user's action description (used for the logic and inline comments).
            - {var_name} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic according to {desc}):
            def run():
                import pyautogui
                import time
                import json
                import os

                json_path = "json_info/citrix_data.json"

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
                json_path = "json_info/citrix_data.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get({{element_name}}) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """


    elif img_status :
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
            2. No argument should accepts in the run() function
            3. All code logic and imports must be inside the run function.
            4. Load the image path from JSON using:
            import json
            json_path = "json_info/citrix_data.json"
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

            def run():
                import json
                import pandas as pd
                import cv2
                import pytesseract
                from PIL import Image
                import numpy as np
                
                # Load image path from JSON
                json_path = "json_info/citrix_data.json"
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
            - The function signature must be: def run():
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
    elif region_status :
        prompt = f""""""
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
                json_path = "json_info/citrix_data.json"
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
                json_path = "json_info/citrix_data.json"
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
                
                json_path = "json_info/citrix_data.json"
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



    if not region_status:   
        response = chat.send_message(prompt)
        code_to_write = response.text
    else:
        code_to_write=f"""
import pandas as pd
import json
from region_img_table_extract import gemini_image_response,capture_region
def run():
    desc="{desc}"
    json_path = "json_info/citrix_data.json"
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

