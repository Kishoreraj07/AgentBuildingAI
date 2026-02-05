import google.generativeai as genai
import config
import json
import re  # Added for fallback attr extraction in attr_json


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


def gemini_response(input,proj_name,task_name,userid):
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

#Get window Title
title = dlg.window_text()
"""

    prompt = f"""
    Here is the User Requirement: {input}

    Based on the above requirement, generate the **Desktop Automation Code**.

    If the user asks to launch a App/Open a App, use this reference code for launching:
    {launching_code}

    ================================================================================
    CRITICAL: DESKTOP AUTOMATION STRUCTURE IS ABSOLUTELY MANDATORY
    ================================================================================

    ⚠️ WARNING: ANY deviation from the exact pattern below is a CRITICAL ERROR ⚠️

    For EVERY desktop interaction (type, click, select, check, extract from UI), you MUST use the EXACT structure shown below. NO EXCEPTIONS. NO SHORTCUTS. NO MODIFICATIONS.

    ================================================================================
    CODE STRUCTURE INSTRUCTIONS FOR DESKTOP AUTOMATION
    ================================================================================
    The generated code must strictly follow the structure below for Desktop automation tasks.

    ================================================================================
    CORRECT CODE PATTERN (MANDATORY FOR DESKTOP ACTIONS):
    ================================================================================
    If User Requirement is:
        - Launch the HPMG app "C:\\Program Files\\HPMG Client\\HPMG_app.exe",
        - Type username  as admin,
        - Type password as 1234,
        - Click Sign In button,
        - Type 123456 in OTP field,
        - Click Verify button,
        - Click Forms button,
        - Select India from country dropdown,
        - Select Tamil Nadu from state/province dropdown,
        - Select Coimbatore in city dropdown,
        - Click Select Skills button,
        - Check Python checkbox,
        - Type 2323 3232 3224 3223 in credit card field,
        - Set date range from the first day of the previous month to the first day of this month,
        - Click Tables button,
        - Extract the table under master heading and save it in this path C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx.
         
    
    def aba_agent():
        try:
            import sys
            import os
            import requests
            import time
            import json
            from pywinauto.application import Application

            from datas.process_flow.desktop_process.desktop_attr_find import main
            from datas.process_flow.desktop_process.desktop_element_confirmation import desktop_element_status
            from datas.process_flow.desktop_process.verify_desktop_attr import mod_attr
            import os, json, traceback, datetime, pandas as pd

            json_attr = {{}}
            if os.path.exists("json_info/json_attr.json"):
                with open("json_info/json_attr.json", "r") as f:
                    json_attr = json.load(f)
            else:
                os.makedirs("json_info", exist_ok=True)
            
            # Step 1: Launch the APP "C:\\Program Files\\HPMG Client\\HPMG_app.exe"
            file_loc=r"C:\\Program Files\\HPMG Client\\HPMG_app.exe"
            # Configure Chrome options
            app = Application(backend="uia").start(r"{{file_loc}}")

            # Get the main window (title flexible with regex)
            dlg = app.window()

            # Maximize window
            dlg.maximize()

            #Get window Title
            title = dlg.window_text()

            # Step 2: Type username  as admin
            var_name = "username_field"
            description = "Type username as admin"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import username_field
                username_field.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import username_field
                username_field.run(dlg.window_text())

            # Step 3: Type password as 1234
            var_name = "password_field"
            description = "Type password as 1234"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import password_field
                password_field.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import password_field
                password_field.run(dlg.window_text())

            # Step 4: Click Sign In button
            var_name = "signin_button"
            description = "Click Sign In button"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import signin_button
                signin_button.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import signin_button
                signin_button.run(dlg.window_text())

            # Step 5: Type 123456 in OTP field
            var_name = "otp_field"
            description = "Type 123456 in OTP field"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import otp_field
                otp_field.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import otp_field
                otp_field.run(dlg.window_text())

            # Step 6: Click Verify button
            var_name = "verify_button"
            description = "Click Verify button"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import verify_button
                verify_button.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import verify_button
                verify_button.run(dlg.window_text())

            # Step 7: Click Forms button
            var_name = "forms_button"
            description = "Click Forms button"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import forms_button
                forms_button.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import forms_button
                forms_button.run(dlg.window_text())

            # Step 8: Select India from country dropdown
            var_name = "country_dropdown"
            description = "Select India from country dropdown"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import country_dropdown
                country_dropdown.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import country_dropdown
                country_dropdown.run(dlg.window_text())

            # Step 9: Select Tamil Nadu from state/province dropdown
            var_name = "state_province_dropdown"
            description = "Select Tamil Nadu from state/province dropdown"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import state_province_dropdown
                state_province_dropdown.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import state_province_dropdown
                state_province_dropdown.run(dlg.window_text())

            # Step 10: Select Coimbatore in city dropdown
            var_name = "city_dropdown"
            description = "Select Coimbatore in city dropdown"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import city_dropdown
                city_dropdown.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import city_dropdown
                city_dropdown.run(dlg.window_text())

            # Step 11: Click Select Skills button
            var_name = "select_skills_button"
            description = "Click Select Skills button"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import select_skills_button
                select_skills_button.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import select_skills_button
                select_skills_button.run(dlg.window_text())

            # Step 12: Check Python checkbox
            var_name = "python_checkbox"
            description = "Check Python checkbox"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import python_checkbox
                python_checkbox.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import python_checkbox
                python_checkbox.run(dlg.window_text())

            # Step 13: Type 2323 3232 3224 3223 in credit card field
            var_name = "credit_card_field"
            description = "Type 2323 3232 3224 3223 in credit card field"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import credit_card_field
                credit_card_field.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import credit_card_field
                credit_card_field.run(dlg.window_text())

            # Step 14: Set date range from the first day of the previous month to the first day of this month
            var_name = "date_range_picker"
            description = "Set date range from the first day of the previous month to the first day of this month"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import date_range_picker
                date_range_picker.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import date_range_picker
                date_range_picker.run(dlg.window_text())

            # Step 15: Click Tables button
            var_name = "tables_button"
            description = "Click Tables button"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import tables_button
                tables_button.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import tables_button
                tables_button.run(dlg.window_text())

            # Step 16: Extract the table under master heading and save it in this path C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx
            var_name = "extract_master_table"
            description = "Extract the table under master heading and save it in this path C:\\Users\\Administrator\\Documents\\aba\\rpamaster.xlsx"
            file_path = f"{proj_name}/{task_name}/{{var_name}}.py"
            if json_attr.get({{var_name}}) == "Not_assigned":
                element_attr = main(description, dlg,title=dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[{{var_name}}] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[{{var_name}}]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, {{var_name}}, dlg.window_text(), {userid})
                from {proj_name}.{task_name} import extract_master_table
                extract_master_table.run(dlg.window_text())
            else:
                from {proj_name}.{task_name} import extract_master_table
                extract_master_table.run(dlg.window_text())


        except Exception as e:
            import os, json, traceback
            os.makedirs("json_info", exist_ok=True)
            with open("json_info/exception_info.json", "w") as f:
                json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)

    ================================================================================
    ABSOLUTELY FORBIDDEN - THESE WILL CAUSE CRITICAL FAILURES
    ================================================================================

    ❌ NEVER EVER create helper functions like get_element_attributes()
    ❌ NEVER EVER hardcode element_attr = {{"control_type": "*", "backend": "uia"}}
    ❌ NEVER EVER comment out main() - IT MUST BE CALLED: element_attr = main(...)
    ❌ NEVER EVER comment out desktop_element_status() - IT MUST BE CALLED
    ❌ NEVER EVER skip the json_attr.get(var_name) == "Not_assigned" check
    ❌ NEVER EVER skip the if not os.path.exists(file_path) check
    ❌ NEVER EVER skip the desktop_code_correction.code_correction() call
    ❌ NEVER EVER add extra parameters to run(): ONLY run(dlg.window_text())
    ❌ NEVER EVER use pass statements in place of the pattern
    ❌ NEVER EVER write "placeholder" or "simulation" or "example" code
    ❌ NEVER EVER import modules at the top - import immediately before run()

    ✅ ALWAYS copy the exact pattern for each step
    ✅ ALWAYS call main() to get element_attr dynamically
    ✅ ALWAYS call desktop_element_status() to verify elements
    ✅ ALWAYS call desktop_code_correction.code_correction()
    ✅ ALWAYS use ONLY ONE argument for run(): dlg.window_text()
    ✅ ALWAYS import module immediately before run() call
    ✅ ALWAYS check json_attr.get(var_name) == "Not_assigned" (no "or" conditions)

    ================================================================================
    STEP-BY-STEP PATTERN FOR EACH DESKTOP INTERACTION
    ================================================================================

    For EVERY step that involves desktop UI interaction, generate code following this EXACT sequence:

    ```python
    # Step X: <Full description from user requirement>
    var_name = "<unique_variable_name>"
    description = "<Full exact description from user requirement>"
    file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"

    # PHASE 1: Get element attributes
    if json_attr.get(var_name) == "Not_assigned":
        element_attr = main(description, dlg, dlg.window_text())
        element_result, element_attr = desktop_element_status(dlg, element_attr,var_name)
        json_attr[var_name] = element_attr
        with open("json_info/json_attr.json", "w") as f:
            json.dump(json_attr, f, indent=4)
    else:
        element_attr = json_attr[var_name]

    # PHASE 2: Execute action
    if not os.path.exists(file_path):
        from datas.process_flow.desktop_process import desktop_code_correction
        desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
        from {{proj_name}}.{{task_name}} import <var_name>
        <var_name>.run(dlg.window_text())
    else:
        from {{proj_name}}.{{task_name}} import <var_name>
        <var_name>.run(dlg.window_text())
    ```

    ================================================================================
    WHAT COUNTS AS "DESKTOP INTERACTION" REQUIRING THE PATTERN
    ================================================================================

    These actions REQUIRE the desktop automation pattern:
    ✅ Type/Enter text in any field (username, password, text box, etc.)
    ✅ Click any button (login, submit, save, continue, etc.)
    ✅ Click any dropdown/combobox
    ✅ Select option from dropdown
    ✅ Check/Uncheck checkbox
    ✅ Click radio button
    ✅ Click tab to switch views
    ✅ Extract text/data from UI elements
    ✅ Extract table data from desktop application
    ✅ Press keyboard keys (Enter, Tab, etc.) - YES, these also need the pattern
    ✅ Click menu items
    ✅ Any interaction with desktop application UI elements

    These actions DO NOT require the pattern (write direct Python code):
    ❌ time.sleep() - write directly
    ❌ File operations (save to disk, copy files, etc.)
    ❌ Excel file operations (pandas operations on files)
    ❌ Variable assignments and calculations
    ❌ Application launch (use the launching_code pattern instead)

    ================================================================================
    CRITICAL RULE: run() FUNCTION MUST HAVE EXACTLY ONE ARGUMENT
    ================================================================================

    The run() function MUST ALWAYS be called with EXACTLY ONE argument: dlg.window_text()

    ❌ WRONG - Multiple arguments:
    ```python
    username_field.run(dlg.window_text(), "ADMIN_USER")
    password_field.run(dlg.window_text(), "password123")
    ```

    ✅ CORRECT - Only one argument:
    ```python
    username_field.run(dlg.window_text())
    password_field.run(dlg.window_text())
    ```

    The data to be typed, clicked, or selected is determined by the `description` parameter passed to desktop_code_correction.code_correction(). The run() function retrieves this from the generated module.

    ================================================================================
    IMPORT PLACEMENT - CRITICAL RULE
    ================================================================================

    Module imports MUST appear TWICE in each step's code block:
    1. Once inside the `if not os.path.exists(file_path):` block (before run())
    2. Once inside the `else:` block (before run())

    ❌ WRONG - Import at top of function:
    ```python
    from {{proj_name}}.{{task_name}} import username_field, password_field

    # ... later
    username_field.run(dlg.window_text())
    password_field.run(dlg.window_text())
    ```

    ✅ CORRECT - Import immediately before each run() call:
    ```python
    # For username field
    if not os.path.exists(file_path):
        from datas.process_flow.desktop_process import desktop_code_correction
        desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
        from {{proj_name}}.{{task_name}} import username_field
        username_field.run(dlg.window_text())
    else:
        from {{proj_name}}.{{task_name}} import username_field
        username_field.run(dlg.window_text())
    ```

    ================================================================================
    UNIQUE var_name REQUIREMENT
    ================================================================================

    Each var_name MUST be unique across the entire task. If the same element type appears multiple times, use incrementing suffixes:

    ✅ CORRECT:
    ```python
    var_name = "continue_button"      # First continue button
    var_name = "continue_button1"     # Second continue button
    var_name = "continue_button2"     # Third continue button
    var_name = "back_button"          # First back button
    var_name = "back_button1"         # Second back button
    ```

    ❌ WRONG - Duplicate var_names:
    ```python
    var_name = "continue_button"      # First
    var_name = "continue_button"      # Duplicate - WILL OVERWRITE
    ```

    ================================================================================
    COMPLETE EXAMPLE: TWO CONSECUTIVE STEPS
    ================================================================================

    ```python
    def aba_agent():
        try:
            import sys
            import os
            import requests
            import time
            import json
            from pywinauto.application import Application
            from datas.process_flow.desktop_process.desktop_attr_find import main
            from datas.process_flow.desktop_process.desktop_element_confirmation import desktop_element_status
            from datas.process_flow.desktop_process.verify_desktop_attr import mod_attr
            import os, json, traceback, datetime, pandas as pd

            json_attr = {{}}
            if os.path.exists("json_info/json_attr.json"):
                with open("json_info/json_attr.json", "r") as f:
                    json_attr = json.load(f)
            else:
                os.makedirs("json_info", exist_ok=True)
            
            # Step 1: Launch app
            file_loc = "C:\\Program Files\\MyApp\\app.exe"
            app = Application(backend="uia").start(r"{{file_loc}}")
            dlg = app.window()
            dlg.maximize()
            title = dlg.window_text()

            # Step 2: Type username as admin
            var_name = "username_field"
            description = "Type username as admin"
            file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"
            if json_attr.get(var_name) == "Not_assigned":
                element_attr = main(description, dlg, dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[var_name] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[var_name]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
                from {{proj_name}}.{{task_name}} import username_field
                username_field.run(dlg.window_text())
            else:
                from {{proj_name}}.{{task_name}} import username_field
                username_field.run(dlg.window_text())

            # Step 3: Click login button
            var_name = "login_button"
            description = "Click login button"
            file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"
            if json_attr.get(var_name) == "Not_assigned":
                element_attr = main(description, dlg, dlg.window_text())
                element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
                json_attr[var_name] = element_attr
                with open("json_info/json_attr.json", "w") as f:
                    json.dump(json_attr, f, indent=4)
            else:
                element_attr = json_attr[var_name]

            if not os.path.exists(file_path):
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
                from {{proj_name}}.{{task_name}} import login_button
                login_button.run(dlg.window_text())
            else:
                from {{proj_name}}.{{task_name}} import login_button
                login_button.run(dlg.window_text())

        except Exception as e:
            import os, json, traceback
            os.makedirs("json_info", exist_ok=True)
            with open("json_info/exception_info.json", "w") as f:
                json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)
    ```

    ================================================================================
    HANDLING SPECIAL CASES
    ================================================================================

    **Wait/Sleep Operations:**
    These are NOT desktop interactions. Write directly without the pattern:
    ```python
    # Wait for 3 seconds
    time.sleep(3)
    ```

    **File Save Operations:**
    When extracting table data and saving to Excel, the extraction uses the pattern but the save does not:
    ```python
    # Extract table (uses pattern)
    var_name = "extract_table"
    description = "Extract the table under master heading"
    file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"
    if json_attr.get(var_name) == "Not_assigned":
        element_attr = main(description, dlg, dlg.window_text())
        element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
        json_attr[var_name] = element_attr
        with open("json_info/json_attr.json", "w") as f:
            json.dump(json_attr, f, indent=4)
    else:
        element_attr = json_attr[var_name]

    if not os.path.exists(file_path):
        from datas.process_flow.desktop_process import desktop_code_correction
        desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
        from {{proj_name}}.{{task_name}} import extract_table
        table_data = extract_table.run(dlg.window_text())
    else:
        from {{proj_name}}.{{task_name}} import extract_table
        table_data = extract_table.run(dlg.window_text())

    # Save to Excel (direct Python code - no pattern needed)
    import pandas as pd
    output_path = r"C:\\Users\\Administrator\\Documents\\output.xlsx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(table_data)
    df.to_excel(output_path, index=False)
    ```

    **Keyboard Actions (Enter, Tab, etc.):**
    YES, these ALSO require the full desktop automation pattern:
    ```python
    # Step X: Press Enter key
    var_name = "enter_key_action"
    description = "Press Enter key"
    file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"
    if json_attr.get(var_name) == "Not_assigned":
        element_attr = main(description, dlg, dlg.window_text())
        element_result, element_attr = desktop_element_status(dlg, element_attr, var_name)
        json_attr[var_name] = element_attr
        with open("json_info/json_attr.json", "w") as f:
            json.dump(json_attr, f, indent=4)
    else:
        element_attr = json_attr[var_name]

    if not os.path.exists(file_path):
        from datas.process_flow.desktop_process import desktop_code_correction
        desktop_code_correction.code_correction(description, element_attr, file_path, var_name, dlg.window_text(), {{userid}})
        from {{proj_name}}.{{task_name}} import enter_key_action
        enter_key_action.run(dlg.window_text())
    else:
        from {{proj_name}}.{{task_name}} import enter_key_action
        enter_key_action.run(dlg.window_text())
    ```

    ================================================================================
    FINAL VERIFICATION CHECKLIST - BEFORE OUTPUTTING CODE
    ================================================================================

    Before generating the final code, verify EVERY step has:

    ✓ var_name = "<unique_name>" - NO DUPLICATES
    ✓ description = "<full step description>"
    ✓ file_path = f"{{proj_name}}/{{task_name}}/{{var_name}}.py"
    ✓ if json_attr.get(var_name) == "Not_assigned": - EXACT CHECK, NO "or" CONDITIONS
    ✓ element_attr = main(description, dlg, dlg.window_text()) - NOT COMMENTED OUT
    ✓ element_result, element_attr = desktop_element_status(...) - NOT COMMENTED OUT
    ✓ json_attr[var_name] = element_attr - STORING RESULT
    ✓ else: element_attr = json_attr[var_name] - RETRIEVING FROM JSON
    ✓ if not os.path.exists(file_path): - FILE CHECK
    ✓ desktop_code_correction.code_correction(...) - CALLED WITH ALL PARAMETERS
    ✓ from {{proj_name}}.{{task_name}} import <var_name> - BEFORE run()
    ✓ <var_name>.run(dlg.window_text()) - EXACTLY ONE ARGUMENT
    ✓ else: block has same import and run() - DUPLICATED IN ELSE

    If ANY of these checks fail, DO NOT output the code. Fix it first.

    ================================================================================
    QUEUE HANDLING RULES:
    ================================================================================
    CRITICAL: Queue operations should ONLY be used when explicitly mentioned in user requirements.
    DO NOT assume or add queue operations unless the user specifically requests them.

    RULE 1: Queue Detection
        Use queue operations ONLY when user requirement contains keywords like:
        - "queue"
        - "get from queue"
        - "retrieve from queue"
        - "upload to queue"
        - "update queue status"
        - "queue item"
        - "queue data"

        - ***MOST IMPORTANT** : If any of these keywords are present, import queue modules with the below sys code and use queue logic:
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        If none of these are mentioned, DO NOT include any queue-related code.

    RULE 2: Get Queue (Retrieve from Queue)
        - ONLY when user explicitly mentions retrieving/getting values from queue, use:
            import requests
            import time
            import ast
            MAIN_URL = "https://droidal.ai"

            def get_task_from_queue(api_key):
                BASE_URL = f"{{MAIN_URL}}/app/agentsapp"
                startTime = int(round(time.time()))
                resp = requests.get(f"{{BASE_URL}}/tasks/pending/", params={{"apikey": api_key}})
                result = resp.json()

                # Handle no records
                if "status" in result and result["status"] == "no records":
                    return "norecords", "norecords", "norecords", False, startTime, "", ""

                # Handle valid record
                try:
                    records = ast.literal_eval(str(result.get("data", {{}}))) if isinstance(result.get("data"), dict) else result.get("data")
                    rowid = result.get("id")
                    status_val = result.get("status")
                    queuename = result.get("apikey", "")
                    queueemail = result.get("usermailid", "")
                    return records, rowid, status_val, True, startTime, queuename, queueemail
                except Exception as e:
                    return "norecords", "norecords", "norecords", False, startTime, "", ""
            records, rowid, status_val, is_record, startTime, queuename, queueemail = get_task_from_queue(api_key)
        
        - api_key will be provided in user requirement - Use the exact api_key mentioned
        - This returns queue data that can be used in automation
        - DO NOT use this import if queue retrieval is not mentioned

    RULE 3: Upload Queue (Add to Queue)
        - ONLY when user explicitly mentions uploading/adding values to queue, use:
            import requests
            import json
            MAIN_URL = "https://droidal.ai"

            def queueupdate(queueapi,outputvariable):
                    #print(outputvariable.keys()[1])
                all_keys = list(outputvariable.keys())
                #result_list = [{{key: str(value)}} for key, values in outputvariable.items() for value in values]
                
                outputvariable = [{{key: str(values[i]) for key, values in outputvariable.items()}} for i in range(len(outputvariable[all_keys[0]]))]
                
                
                import requests
                payload = {{
                "apikey": queueapi,
                "data": {{
                    "tasks":outputvariable
                }}
                }}

                resp = requests.post(f"{{MAIN_URL}}/app/agentsapp/tasks/create/", json=payload)
                print("Create Task:", resp.status_code, resp.json())
            queueupdate(api_key, outputvariable)
        
        - api_key and outputvariable will be provided in user requirement - Use the exact api_key mentioned
        - outputvariable contains the data to be uploaded to queue
        - DO NOT use this import if queue upload is not mentioned
        - if uploading queue from excel data, read excel using pandas and **DO NOT** convert to dict(orient='records') before passing to queueupdate. Just Pass the DataFrame only.

    RULE 4: Update Queue Status
        - ONLY when user explicitly mentions updating status of queue items, use:
            import requests
            import time
            MAIN_URL = "https://droidal.ai"

            def queue_update(api_key,task_id, statusupdate, queuename="", queueemail="", clientname="", remark="", desc_data="", startTime=None):
                BASE_URL = f"{{MAIN_URL}}/app/agentsapp"
                if not startTime:
                    startTime = int(round(time.time()))

                try:
                    startTime = int(startTime)
                except Exception:
                    startTime = int(round(time.time()))
                endTime = int(round(time.time()))
                time_dur = endTime - startTime

                # --- Step 1: Update task in Django API ---
                payload = {{
                    "apikey": api_key,
                    "status": statusupdate
                }}
                resp = requests.put(f"{{BASE_URL}}/tasks/{{task_id}}/update-status/", json=payload)
                print("Django API Update:", resp.status_code, resp.json())
            queue_update(api_key, task_id, statusupdate, queuename, queueemail, clientname, remark, desc_data, startTime)
        
        - All parameters will be provided in user requirement or obtained from get_task_from_queue
        - Use startTime from get_task_from_queue for status updates
        - statusupdate can be values like "Completed", "Failed", "In Progress", etc.
        - DO NOT use this import if queue status update is not mentioned

    RULE 5: Queue Integration Pattern
        - ONLY apply this pattern when queue operations are explicitly requested:
            1. Get task from queue (get_task_from_queue)
            2. Process the task (automation steps)
            3. Update queue status (queue_update)
        
        - Always handle queue operations inside try/except blocks
        - Update status to "Failed" if exceptions occur during processing
        - DO NOT wrap non-queue automation in queue logic

    RULE 6: Queue Error Handling
        - ONLY use this pattern when queue operations are explicitly mentioned:
        
        try:
            from getqueuev2 import get_task_from_queue
            from queueupdatestatusv2 import queue_update
            
            records, rowid, status_val, is_record, startTime, queuename, queueemail = get_task_from_queue(api_key)
            
            if is_record:
                # Process automation tasks here
                
                # Update status to Completed
                queue_update(api_key, rowid, "Completed", queuename, queueemail, clientname, "Success", "Task completed successfully", startTime)
            else:
                # No records available in queue
                pass
                
        except Exception as e:
            # Update status to Failed
            queue_update(api_key, rowid, "Failed", queuename, queueemail, clientname, "Error", str(e), startTime)

    RULE 7: Queue Exclusion Rule (CRITICAL)
        - If user requirement does NOT mention queue operations:
            * DO NOT import any queue modules
            * DO NOT add queue-related variables
            * DO NOT wrap automation in queue logic
            * Proceed with standard automation code only
        
        - Example of what NOT to do when queue is not mentioned:
            ❌ from getqueuev2 import get_task_from_queue  # Wrong if not requested
            ❌ records, rowid = get_task_from_queue(api_key)  # Wrong if not requested
            ❌ if is_record:  # Wrong if not requested

    RULE 8: Queue Parameter Availability
        - Queue operations require specific parameters from user requirement
        - If user mentions queue but doesn't provide required parameters, do not assume values
        - Required parameters:
            * For get_task_from_queue: api_key
            * For queueupdate: api_key, outputvariable
            * For queue_update: api_key, task_id, statusupdate, queuename, queueemail, clientname, remark, desc_data, startTime
        
    ================================================================================
    RULES
    ================================================================================
    1. The entire code must be wrapped inside a single function named **aba_agent()**.
    - The function must not take any arguments.
    - The function must not be called within the code.

    2. The code must always include **try**, **except**blocks exactly in this format:
        except:
            import os, json, traceback
            os.makedirs("json_info", exist_ok=True)
            with open("json_info/exception_info.json", "w") as f:
                json.dump({{"code_exception": traceback.format_exc()}}, f, indent=4)

    3. For every individual step (typing, clicking, extracting, etc.):
    - Always define:
            -var_name = "<unique_variable_name>"
                Each `var_name` should always be **unique** 
            -description = "<description must be full steps content>" # dont partial step content, dont check and or (,) in steps
            -# STEP = "<step must be full steps content>" # dont partial step content, dont check and or (,) in steps
            -file_path = f"{proj_name}/{task_name}/<variable_name>.py"

    - Before execution, check if the file exists:
            - If NOT exists:
                from datas.process_flow.desktop_process import desktop_code_correction
                desktop_code_correction.code_correction(description,element_xpath, file_path,var_name ,dlg.window_text(),{userid})
                then import the corresponding module dynamically and run it.
            - If exists:
                directly import and run it.

    4. The **import lines** like:
        from {proj_name}.{task_name} import username_field
    must be placed **immediately before the line** of their respective `.run(dlg.window_text())` calls not at starting overall import (MANDATORY)
    Do not move or combine these imports at the top of the script.
    
    5. The functions such as `main`, `element_status`, and `mod_xpath` must always be **imported from external files** and **not redefined within the generated code**.  
    They should be imported exactly as shown below:

        from xpath_find import main
        from element_confirmation import element_status
        from verify_xpath import mod_xpath

    6. When calling the run() function from the Desktop Automation flow, it must always be invoked with these this one argument only — (dlg.window_text()). Missing either argument (i.e., calling it without dlg.window_text()) is not allowed.

    7. Output must contain **only the valid Python code** (no explanations, markdown, or comments).
    """
    try:
        response = chat.send_message(prompt)
        code_to_write = response.text.strip("` \n python")  # Minor: Trim more variants
    except Exception as e:
        raise ValueError(f"Gemini API error: {e}")

    attrjson = attr_json(code_to_write)
    return code_to_write, attrjson

# input="""Launch the SAP Logon app r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
# Click on the connection entry SAP ECC Production
# Click the Logon button
# Type username as ADMIN_USER
# Type password as SecurePass@2024
# Click the green checkmark button to login
# Wait for 3 seconds
# Click on the SAP Easy Access menu button
# Type transaction code MM01 in the command field
# Press Enter key
# Click the Material Type dropdown
# Select FERT from the dropdown options
# Click the Industry Sector dropdown
# Select Mechanical Engineering from the dropdown options
# Type ABC-MATERIAL-001 in the Material field
# Click the Continue button
# Click the Basic Data 1 tab
# Type Test Material Description in the Description field
# Type KG in the Base Unit of Measure field
# Click the Material Group dropdown
# Select Raw Materials from the dropdown options
# Type 1000 in the Gross Weight field
# Type 950 in the Net Weight field
# Click the Sales: Sales Org 1 tab
# Click the Sales Organization dropdown
# Select 1000 - Global Sales from the dropdown options
# Click the Distribution Channel dropdown
# Select 10 - Wholesale from the dropdown options
# Type EA in the Sales Unit field
# Type 100 in the Minimum Order Quantity field
# Type 5000 in the Maximum Order Quantity field
# Check the Batch Management checkbox
# Check the Serial Number Profile checkbox
# Click the Plant Data/Storage 1 tab
# Click the Plant dropdown
# Select 1000 - Main Plant from the dropdown options
# Type 0001 in the Storage Location field
# Click the MRP Type dropdown
# Select PD - MRP from the dropdown options
# Type 10 in the Reorder Point field
# Type 100 in the Maximum Stock Level field
# Type 30 in the Safety Stock field
# Click the Purchasing tab
# Type ADMIN_USER in the Purchasing Group field
# Click the Plant Specific Material Status dropdown
# Select 01 - Active from the dropdown options
# Type 45 in the Planned Delivery Time field
# Check the Source List checkbox
# Click the Quality Management tab
# Check the Inspection Setup checkbox
# Click the Inspection Type dropdown
# Select 01 - Goods Receipt from the dropdown options
# Type QM-PLAN-001 in the Inspection Plan field
# Click the Accounting 1 tab
# Click the Valuation Class dropdown
# Select 3000 - Raw Materials from the dropdown options
# Type 150.50 in the Standard Price field
# Click the Price Control radio button for S - Standard Price
# Click the Costing 1 tab
# Type 500 in the Material Origin field
# Click the Overhead Group dropdown
# Select MATL - Material Overhead from the dropdown options
# Type 10 in the Overhead Percentage field
# Click the Save button
# Wait for 5 seconds
# Extract the Material Number from the confirmation message
# Extract the success message text
# Click the Back button
# Click the Back button again to return to main menu
# Type ME21N in the command field
# Press Enter key
# Click the Vendor field
# Type 1000567 in the Vendor field
# Press Tab key
# Type PO-2024-001 in the Purchase Order field
# Click the Material field in the first row
# Type ABC-MATERIAL-001 in the Material field
# Press Tab key
# Type 500 in the Quantity field
# Press Tab key
# Extract the Unit Price value
# Extract the Total Amount value
# Type 30 in the Delivery Date offset field
# Click the Header button
# Click the Payment Terms dropdown
# Select 0001 - Payable Immediately from the dropdown options
# Type TEST PO Creation from automation in the Header Text field
# Click the Save button
# Wait for 3 seconds
# Extract the Purchase Order Number from the confirmation message
# Click the Display Document button
# Extract all line item details from the table
# Extract the table data and save it to C:\\Users\\Administrator\\Documents\\SAP_Automation\\PO_Details.xlsx
# Click the Close button
# Type /nEX in the command field to exit
# Press Enter key
# Click the Yes button to confirm logout"""
# proj_name="proj_11"
# task_name="task_22"
# userid="5"
# code_data,json_data=gemini_response(input,proj_name,task_name,userid)
# with open("backup.py", "w", encoding="utf-8") as f:
#     f.write(code_data)
# with open("test_json.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, indent=4, ensure_ascii=False)