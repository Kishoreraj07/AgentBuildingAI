# supporting_files/citrix_type.py
def citrix_type(var_name: str, description: str, userid: object, cwd: str) -> bool:
    try:
        import os
        import json
        import time
        import traceback
        import re
        import pyautogui
        import logging  # For better debugging
        os.makedirs("json_info", exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        
        json_path = os.path.join(cwd, "json_info", "citrix_data.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"citrix_data.json not found at {json_path}")
       
        JSON_PATH = os.path.join(cwd, "json_info/citrix_data.json")
        Task_file = os.path.join(cwd, "json_info/task_info.json")
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            citrix_data = json.load(f)
        with open(Task_file, "r", encoding="utf-8") as f:
            task_info = json.load(f)
        proj_name = task_info["Proj_file_name"]
        task_name = task_info["Task_file_name"]
       
        var_name = var_name
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
        
        # extract text to type from description
        def _extract_text(desc: str):
            # 1) try quoted text
            m = re.search(r"[\"'](.+?)[\"']", desc)
            if m:
                return m.group(1).strip()
            # 2) try "as <text>" at the end or before "in"
            m = re.search(r"[Aa]s\s+(.+?)(?:\s+in\b|$)", desc)
            if m:
                return m.group(1).strip()
            # 3) try "type <word> into" style
            m = re.search(r"[Tt]ype\s+(.+?)\s+(?:into|in|on)\b", desc)
            if m:
                return m.group(1).strip()
            return None
        
        text_to_type = _extract_text(description)
        if not text_to_type:
            raise ValueError("Could not parse text to type from description. Please include text using 'as <text>' or quotes.")
        
        logger.info(f"Attempting to type '{text_to_type}' into '{var_name}' based on '{description}'")
        
        # Handle both coordinate list and image path cases (similar to provided snippet)
        if isinstance(element_data, list) and len(element_data) == 4:
            try:
                top_left_x, top_left_y, bottom_right_x, bottom_right_y = map(int, element_data)
                x = (top_left_x + bottom_right_x) // 2
                y = (top_left_y + bottom_right_y) // 2
                logger.info(f"Using coordinates: center at ({x}, {y})")
            except Exception:
                raise ValueError("Coordinate list must contain four integers/floats")
            
            time.sleep(0.5)
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            time.sleep(0.3)           
            
            pyautogui.typewrite(text_to_type, interval=0.05)
            logger.info(f"Typed '{text_to_type}' using coordinates.")
            return True
        
        elif isinstance(element_data, str):
            image_path = element_data
            if not os.path.isabs(image_path):
                image_path = os.path.join(cwd, image_path)
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found at {image_path}")
            
            time.sleep(0.5)
            location = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
            if location:
                logger.info(f"Located image '{var_name}' at center ({location.x}, {location.y})")
                pyautogui.moveTo(location.x, location.y, duration=0.2)
                pyautogui.click()
                time.sleep(0.3)
                
                pyautogui.typewrite(text_to_type, interval=0.05)
                logger.info(f"Typed '{text_to_type}' into the detected field using image.")
                return True
            else:
                logger.warning(f"Image '{var_name}' not found on screen for '{description}'")
                return False
        else:
            raise TypeError("Element data must be either a 4-length list of coords or a string path to image")
    
    except Exception:
        import os, json, traceback
        os.makedirs("json_info", exist_ok=True)
        with open(os.path.join("json_info", "exception_info.json"), "w", encoding="utf-8") as f:
            json.dump({"code_exception": traceback.format_exc()}, f, indent=4)
        logger.error(f"Exception in citrix_type for '{var_name}': {traceback.format_exc()}")
        return False