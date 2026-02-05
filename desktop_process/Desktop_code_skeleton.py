import google.generativeai as genai
import config
import json
import re  # Added for fallback attr extraction in attr_json
import os  # Added for ensuring directory exists in example usage


def attr_json(code):
    """Extract all attribute variables (like username_attr, password_attr)
    from the generated code and return a JSON dict with 'Not_assigned' values."""
    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()

    prompt = f"""Here is the code : {code}

Analyze this code completely and here attributes are assigned on so many variables like username_attr,password_attr like need to list out all as a JSON format like
{{"username_attr":"Not_assigned","password_attr":"Not_assigned",....}} 
On code all attributes not initially assigned with values so make all as Not_assigned 

And returns the output JSON
Return only the JSON no need additional explanation or text"""

    response = chat.send_message(prompt)
    res_txt = response.text.strip("` \n json python")  # Minor: Trim more whitespace/variants
    try:
        res = json.loads(res_txt)
        # Ensure all values are "Not_assigned" (Gemini might vary)
        for key in res:
            res[key] = "Not_assigned"
    except json.JSONDecodeError:
        # Fallback: Manual extraction via regex for common attr patterns (e.g., *_attr)
        print("Warning: Gemini JSON invalid; falling back to regex extraction.")
        attr_pattern = r'(\w+_attr)\s*='  # Matches var_name = ...
        matches = re.findall(attr_pattern, code)
        res = {attr: "Not_assigned" for attr in set(matches)}
        if not res:
            res = {}  # Empty if no attrs found
    return res


def gemini_response(input):
    """Generate desktop automation code using pywinauto for a given input (exe path)."""
    if isinstance(input, list):
        input = "\n".join(input)

    genai.configure(api_key=config.API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
    chat = model.start_chat()

    # Launching reference code for desktop application (unchanged)
    launching_code = """from pywinauto.application import Application

# Launch Application (path provided in input)
app = Application(backend="uia").start(r"{file_location}")

# Get the main window (title flexible with regex)
dlg = app.window()

# Maximize window
dlg.maximize()

# Get title of window 
title = dlg.window_text()
"""

    prompt = f"""Here is the user requirement : {input}
Above is the requirement for Desktop Automation flow
Need to create the python code for that use pywinauto package to create the complete python code using attributes

STRICT RULES - MUST FOLLOW EXACTLY WITHOUT DEVIATION:

1. Never assume or hardcode any attribute. ALWAYS use the JSON-based conditional logic for EVERY element.

2. The generated code MUST always begin with EXACTLY these import statements (do not skip, modify, or rearrange ANY of them):

        import json
        from PyQt5.QtWidgets import QApplication  # Added: For processEvents to keep Qt UI responsive
        from pywinauto.application import Application
        from pywinauto import Desktop
        from desktop_attr_find import main
        from desktop_element_confirmation import desktop_element_status
        from verify_desktop_attr import mod_attr
        from desktop_interact_element import interact_with_element
        import time
       

3. ALWAYS read and load the json file EXACTLY like this (assume it always exists) IMMEDIATELY after imports:
       with open("json_info/json_attr.json", "r") as f:
           json_attr = json.load(f)

   - json_attr contains all element_attr variable names as keys with default value "Not_assigned".
   - For EVERY SINGLE ELEMENT in the flow, you MUST use a unique relevant_element_key_name (e.g., "host_input" for host field, "transfer_menu" for Transfer menu, "speed_limits_menu" for speed limits submenu). Use snake_case with descriptive names based on function.
   - STRICT CONDITIONAL LOGIC FOR EVERY ELEMENT - COPY THIS EXACTLY, NO VARIATIONS:
         if json_attr.get(relevant_element_key_name) == "Not_assigned":
             description = "<brief human-readable description, e.g., 'host input field'>"
             element_attr = main(<element_path_list>, dlg,title)
             print(element_attr)  # ALWAYS include this print
             element_result = desktop_element_status(dlg, element_attr, description)  # EXACT CALL: dlg, element_attr, description - NO WRAPPER
             print(element_result)  # ALWAYS include this print
             if not element_result:
                 element_attr = mod_attr(dlg)
             json_attr[relevant_element_key_name] = element_attr
         else:
             element_attr = json_attr[relevant_element_key_name]
   - <element_path_list> is a STRICT list of exact terms from the user requirement representing the navigation path. 
     - For simple fields like "type host", use ["host"] - use EXACT word from user input, e.g., "host" not "hostname".
     - For navigation like "navigate to transfer and then to speed limits", use ["Transfer", "speed limits"] – ALWAYS use original casing and wording from user input, as a list for menu/submenu paths. For deeper: ["Transfer", "speed limits", "Enable"].
     - NEVER use descriptive phrases like "hostname input field" in the main() call; ONLY exact terms from user requirement.
   - description is ONLY for validation, e.g., "host input field", "Transfer menu item" - brief and human-readable.
   - FOR MENU/DROPDOWN NAVIGATION CHAINS (e.g., Transfer -> speed limits -> Enable): Extract and save attributes for EACH level separately using cumulative paths and unique keys (e.g., transfer_menu with ["Transfer"], speed_limits_menu with ["Transfer", "speed limits"], enable_checkbox with ["Transfer", "speed limits", "Enable"]). ALWAYS perform the full conditional logic (main, status, mod_attr if needed, save to json_attr[key]) for EVERY level to capture and persist all intermediate attributes. However, ONLY call interact_with_element on the FINAL level's element_attr (e.g., only interact with enable_checkbox attr). This ensures all attrs are saved in JSON for reuse, but navigation/clicking is handled solely by the final interaction, which uses the ancestors path to click through intermediates automatically. NO interact_with_element calls on intermediate levels - ONLY on the last/final submenu path for such chains. This rule applies STRICTLY only to menu navigation and dropdown sequences; for independent elements, interact as needed.
   - **NEW RULE:**
     Before EACH call to `interact_with_element()`, you MUST immediately write the latest json_attr dictionary to the JSON file, so progress is saved incrementally.
     Example (ALWAYS include before any interaction):
         with open("json_info/json_attr.json", "w") as f:
             json.dump(json_attr, f, indent=4)
         QApplication.processEvents()
     Then call:
         interact_with_element(dlg, element_attr, ...)
     This ensures that even if the flow stops mid-run, all discovered attributes are persisted in json_attr.json before every interaction.

   - AFTER ALL ELEMENTS, EXACTLY ONCE at the END before app.kill(): 
         with open("json_info/json_attr.json", "w") as f:
             json.dump(json_attr, f, indent=4)
4. ALL interactions with desktop elements MUST use EXACTLY: interact_with_element(dlg, element_attr, text="value" if typing else None, extract_text=False if applicable)
   - To type text: interact_with_element(dlg, element_attr, text="value", extract_text=False)
   - To click: interact_with_element(dlg, element_attr)
   - To extract: interact_with_element(dlg, element_attr, extract_text=True)
   - NEVER redefine or inline interactions; ALWAYS import and use this function.
   - For menu/submenu chains, ONLY interact with the final attr as per rule 3; the function will handle ancestor navigation.

5. If a click opens a new window: STRICTLY detect and switch: new_dlg = Desktop(backend="uia").window(title_re=".*<keyword>.*"); new_dlg.set_focus(); then use new_dlg for subsequent actions.

6. UI Responsiveness MANDATORY: Add QApplication.processEvents() AFTER EVERY: app.start(), dlg.maximize(), main(), mod_attr(), interact_with_element(), and before JSON save.
   - Example: interact_with_element(...); QApplication.processEvents(); time.sleep(2) if delay needed.

7. Initial Application Launch: EXACTLY use {launching_code} but replace {{file_location}} with r"path from user input".

8. The final code MUST be wrapped EXACTLY in: def aba_agent(): ... (all code inside); NO call to aba_agent(); NO args.

9. At EXACT END inside function, after JSON save: app.kill()

Output ONLY the code - NO explanations, markdown, or extra text. Ensure NO syntax/indent errors."""

    try:
        response = chat.send_message(prompt)
        code_to_write = response.text.strip("` \n python")  # Minor: Trim more variants
    except Exception as e:
        raise ValueError(f"Gemini API error: {e}")

    attrjson = attr_json(code_to_write)
    return code_to_write, attrjson

