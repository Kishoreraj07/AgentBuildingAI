import google.generativeai as genai
import config
from selenium.webdriver.support.ui import WebDriverWait
# import screenshot_xpath
from google import genai as genai2
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

    2. If the description refers to extracting, reading, or retrieving a data table, grid, or tabular content from the desktop window,
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
def code_correction(desc,attributes,file_path,var_name,dlg,userid):

    with open("json_info/task_info.json", "r", encoding="utf-8") as f:
        json_info = json.load(f)
    proj_fol=json_info["Proj_file_name"]
    task_fol=json_info["Task_file_name"]

    co_ordinates_status=False
    img_status=False

    if type(attributes) == list:
        co_ordinates_status=True
    if isinstance(attributes, str):
        if attributes.lower().endswith(".png"):
            img_status = True
    try:
        dlg.wait("visible", timeout=20)
        dlg.wait("enabled", timeout=20)
    except:
        pass
    try:
        element_content = dlg.print_control_identifiers()
    except:
        element_content = ""
    # with open("page_content.html", "w", encoding="utf-8") as f:
    #     f.write(html_content)
    # xpath=screenshot_xpath.get_xpath(driver,desc,html_content)
    
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
            element = dlg.child_window(title=desc, control_type="Text")
        except:
            try:
                element = dlg.child_window(best_match=desc)
            except:
                element = None
        if element:
            try:
                outer_element = element.element_info.__dict__
            except:
                outer_element = {}
        else:
            outer_element = {}    

    # elif not dropdown_selection and not table_extraction:
    if co_ordinates_status and not img_status:
        genai.configure(api_key=config.API_KEY)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        chat = model.start_chat()
        prompt = f"""
            You will be given:
            - desc: a short natural-language description of the user's intended UI action (string).
            - coordinate_index: a JSON-style coordinate index in the form [x_axis, y_axis] (list of two integers) — this value should be read from a JSON file inside the generated code.
            - var_name: the JSON key (string) used to look up the coordinate index inside the JSON file.

            Task:
            Generate a single, valid Python function definition named `run(dlg)` that performs the described UI action using `pyautogui` for mouse and keyboard automation. 
            The generated code must:
                1. Be valid, fully functional, and well-formatted Python code (no partial or pseudo-code).
                2. Contain only the function definition `def run(dlg):` and its body. Do NOT include any function calls, test examples, or extra output.
                3. The `dlg` argument must be present in the function signature but MUST NOT be used in the function body (it may be silenced using `_ = driver`).
                4. Read the [x_axis, y_axis] coordinate values from a JSON file at path `"json_info/json_attr.json"` using the provided `{var_name}` key.
                5. Validate that the coordinate index exists and is a list or tuple of **two integers**. Raise a clear `ValueError` if the format is invalid.
                6. Use `pyautogui` for performing the required user actions (e.g., `pyautogui.click`, `pyautogui.moveTo`, `pyautogui.write`, etc.), as described in `{desc}`.
                7. Include concise inline comments explaining key steps, imports, and assumptions.
                8. Do NOT print or return any extra explanatory text — only generate the function code.

            Placeholders:
            - {desc} → will be replaced with the user's action description (used for the logic and inline comments).
            - {var_name} → will be replaced with the key string to retrieve the coordinate pair from the JSON file.

            Sample output format (follow this pattern; adapt logic according to {desc}):
            def run(dlg):
                import pyautogui
                import time
                import json
                import os

                # Silence unused parameter
                _ = dlg

                json_path = "json_info/json_attr.json"

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
                json_path = "json_info/json_attr.json"
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                coordinates_points = json_info.get({{element_name}}) 
            - Keep the function self-contained and robust.
            - Do not send any additional explanation or console text beyond the function definition itself.
        """
        response = chat.send_message(prompt)


    elif img_status and not co_ordinates_status:
        genai.configure(api_key=config.API_KEY)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
        chat = model.start_chat()
        prompt = f"""
            You will be given:
            - desc: The user's action requirement in natural language (e.g., "click login button", "type username", "extract OTP").
            - json_path: Path to the JSON file containing image information.
            - var_name: The key used to retrieve the image path from the JSON file.

            Task:
            Generate a Python Citrix automation function using the pyautogui package to perform the described user action.
            The function must:
            1. Always be named `run`.
            2. Always accept an argument `dlg=None` (even if unused).
            3. Load the image path from JSON using:
            import json
            json_path = "json_info/json_attr.json"
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

            def run(dlg=None):
                import json
                import timeelement_name
                import pyautogui
                json_path = "json_info/json_attr.json"
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
        response = chat.send_message(prompt)

    else:
        client = genai2.Client(api_key=config.API_KEY)
        
        import ast
        try:
            attributes=ast.literal_eval(attributes)
            screen_shot_file=attributes["screenshot_path"]
            img_file=client.files.upload(file=screen_shot_file)
            attributes.pop("screenshot_path")
        except:
            pass
        element_format = """{"current_element": {<current element UI data like auto_id, class_name, value, rectangle, etc.>},
                    "child_info": {<current element's all child elements in tree-like structure>}}"""

        prompt = f"""
        User Action: {desc}

        Element Information: {attributes}

        Screenshot: Attached screenshot of application {dlg}

        Element Format: {element_format}

        Task:
        Generate Python code using pywinauto to perform the user action: "{desc}"

        Requirements:
        1. Analyze the current element AND its child_info structure thoroughly
        2. For dropdowns, data selections, or table extractions - use the child_info hierarchy and screenshot to understand the full structure
        3. Use the provided element attributes (auto_id, class_name, rectangle, etc.) to locate and interact with elements
        4. Generate ONLY executable Python code
        5. Code must be inside a function named 'run' with single parameter: {dlg}
        6. Do NOT include function calls - only the function definition
        7. Do NOT include explanations, comments, or markdown formatting

        Required Function Signature:
        def run({dlg}):
            # Your pywinauto automation code here

        Output: Pure Python code only, no additional text or explanations.
    """
        response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[prompt, img_file]
            )

    # response = chat.send_message(prompt)
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