
def citrix_click(var_name: str, description: str, userid: object, cwd: str) -> bool:
   
    try:
        import os
        import json
        import time
        import traceback
        import pyautogui


        os.makedirs("json_info", exist_ok=True)
        json_path = os.path.join(cwd, "json_info", "citrix_data.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"citrix_data.json not found at {json_path}")
        
        JSON_PATH=os.path.join(cwd,"json_info/citrix_data.json")
        Task_file=os.path.join(cwd,"json_info/task_info.json")
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            citrix_data = json.load(f)

        with open(Task_file, "r", encoding="utf-8") as f:
            task_info = json.load(f)
        proj_name=task_info["Proj_file_name"]
        task_name=task_info["Task_file_name"]
        
        var_name=var_name
        current_xpath = citrix_data.get(var_name)
        file_path = f"{proj_name}/{task_name}/{var_name}.py"
        if current_xpath == "Not_assigned":
            # raw_xpath = xpath_find.main(description, driver)
            # Verify status
            import Citrix_process.verify_citrix_element
            is_valid, current_xpath = Citrix_process.verify_citrix_element.mod_citrix(description)
            # Update JSON
            citrix_data[var_name] = current_xpath
            with open(JSON_PATH, "w") as f:
                json.dump(citrix_data, f, indent=4)

        with open(json_path, "r", encoding="utf-8") as f:
            citrix_data = json.load(f)

        element_data = citrix_data.get(var_name)
        if element_data is None:
            # try case-insensitive lookup
            for k, v in citrix_data.items():
                if k.lower() == var_name.lower():
                    element_data = v
                    break

        if element_data is None:
            raise KeyError(f"Element '{var_name}' not found in citrix_data.json")

        # If element_data is a list of 4 numbers -> interpret as coords
        if isinstance(element_data, list) and len(element_data) == 4:
            try:
                top_left_x, top_left_y, bottom_right_x, bottom_right_y = element_data
                x = (int(top_left_x) + int(bottom_right_x)) // 2
                y = (int(top_left_y) + int(bottom_right_y)) // 2
            except Exception:
                raise ValueError("Coordinate list must contain four integers/floats")

            time.sleep(0.2)
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            # store last click info
            
            return True

        # If element_data is a string -> treat as image path
        elif isinstance(element_data, str):
            image_path = element_data
            # if path is relative, join with cwd
            if not os.path.isabs(image_path):
                image_path = os.path.join(cwd, image_path)

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found at {image_path}")

            time.sleep(0.2)
            location = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
            if location:
                pyautogui.moveTo(location.x, location.y, duration=0.2)
                pyautogui.click()
                return True
            else:
                # image not found on screen
                return False

        else:
            raise TypeError("Element data must be either a 4-length list of coords or a string path to image")

    except Exception:
        import os, json, traceback
        os.makedirs("json_info", exist_ok=True)
        with open(os.path.join("json_info", "exception_info.json"), "w", encoding="utf-8") as f:
            json.dump({"code_exception": traceback.format_exc()}, f, indent=4)
        return False
