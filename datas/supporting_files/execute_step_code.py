def log_action(message):
    """Log action to web_element_confirmation.txt"""
    import os
    from datetime import datetime
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_element_confirmation.txt")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] execute_step_code: {message}\n")
    except Exception as e:
        print(f"Error logging: {e}")

def execute_step(driver, var_name, description,user_id,org_path,app_info=None,type_input=None):
    dynamic_xpath=False
    type_action=False
    if type_input != None:
        type_action=True
    import sys,os,json
    from datas.supporting_files.message_box_delay import show_timed_message_box
    # sys.path.append(r"D:\AgentFlow")
    flag=False
    log_action(f"execute_step called with var_name='{var_name}', description='{description}'")
    for i in range(10):
        if flag==False:
            error_info=""
        iframe_sts=False
        try:
            import os
            import json
            import importlib.util
            from datas.source_files import element_confirmation
            from datas.source_files import gemini_code_correction
            from datas.source_files import verify_xpath
            import time
            from datas.source_files import xpath_find
            JSON_PATH=os.path.join(org_path,"json_info/json_xpath.json")
            Task_file=os.path.join(org_path,"json_info/task_info.json")
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                json_xpath = json.load(f)

            with open(Task_file, "r", encoding="utf-8") as f:
                task_info = json.load(f)
            proj_name=task_info["Proj_file_name"]
            task_name=task_info["Task_file_name"]
            
            var_name=var_name
            current_xpath = json_xpath.get(var_name)
            if "iframe" in current_xpath:
                iframe_sts=True
                iframe_data=current_xpath["iframe"]
                iframe_xpath=current_xpath["xpath"]
                if "{" in iframe_xpath and "}" in iframe_xpath:
                    dynamic_xpath=True
            
            if "{" in current_xpath and "}" in current_xpath:
                dynamic_xpath=True
                # current_xpath=app_info
            if dynamic_xpath:
                dynamic_xpath_json="json_info/dynamic_xpath.json"
                dynamic_info={"data":app_info}
                with open(dynamic_xpath_json, "w") as f:
                    json.dump(dynamic_info, f, indent=4)

            if app_info==None:
                app_info=""
            add_info={"xpath_variables":app_info}
            file_path = f"{proj_name}/{task_name}/{var_name}.py"
            if current_xpath == "Not_assigned":
                raw_xpath = xpath_find.main(description, driver)
                # Verify status

                from datas.source_files import element_confirmation
                # show_timed_message_box("Autowait 1")
                time.sleep(2)
                log_action(f"Calling element_status for var_name='{var_name}'")
                is_valid, current_xpath = element_confirmation.element_status(var_name, raw_xpath, driver)
                log_action(f"element_status returned: is_valid={is_valid}, current_xpath='{current_xpath}'")
                iframe_sts=False
                if type(current_xpath)==dict:
                    iframe_sts=True
                    xpath_data=current_xpath["xpath"]
                    if "{" in xpath_data and "}" in xpath_data:
                        dynamic_xpath=True
                    iframe_data=current_xpath["iframe"]

                # Update JSON
                # show_timed_message_box("Autowait 2")
                time.sleep(2)
                json_xpath[var_name] = current_xpath
                with open(JSON_PATH, "w") as f:
                    json.dump(json_xpath, f, indent=4)

                if is_valid!=True:
                    log_action(f"element_status returned invalid, retrying...")
                    while True:
                        from datas.source_files import element_confirmation
                        log_action(f"Retry: Calling element_status for var_name='{var_name}'")
                        is_valid, current_xpath = element_confirmation.element_status(var_name, raw_xpath, driver)
                        log_action(f"Retry: element_status returned: is_valid={is_valid}, current_xpath='{current_xpath}'")
                        json_xpath[var_name] = current_xpath
                        with open(JSON_PATH, "w") as f:
                            json.dump(json_xpath, f, indent=4)
                        if is_valid:
                            log_action(f"Retry successful: element confirmed")
                            break

            # 2. Code Generation & Execute
            if not os.path.exists(file_path):
                if flag==False:
                    if not iframe_sts:
                        gemini_code_correction.code_correction(description, current_xpath, file_path, var_name, driver, user_id,add_info,type_input)
                    else:
                        gemini_code_correction.iframe_code_correction(description, current_xpath, file_path, var_name,iframe_data, driver, user_id,add_info,type_input)
                        driver.switch_to.default_content()
                else:
                    if not iframe_sts:
                        gemini_code_correction.fallback_code_correction(description, current_xpath, file_path, var_name, driver, user_id,add_info,error_info,type_input)
                    else:
                        gemini_code_correction.iframe_code_correction(description, current_xpath, file_path, var_name,iframe_data, driver, user_id,add_info,type_input)
                        driver.switch_to.default_content()
                #run function code loader
                run_fn_path = f"{proj_name}/{task_name}/{var_name}.py" 
                if iframe_sts:
                    driver.switch_to.default_content()
                file_exists=False
                if os.path.exists(run_fn_path):
                    file_exists=True
                if file_exists:
                    # show_timed_message_box("File Exist")
                    time.sleep(2)
                    run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                    run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                    run_fn_spec.loader.exec_module(run_fn_module)
                    if type_action:
                        run_fn_module.run(driver,type_input)
                    else:
                        run_fn_module.run(driver)
                else:
                    # return "failed",{"error":"Error Occured during the code generation for this action",
                    #         "code":"",
                    #         "file":""}
                    show_timed_message_box("file not exist")
                    
                    res="failed"
                    error_info={"error":"Error Occured during the code generation for this action",
                            "code":"",
                            "file":""}
            else:
                #run function code loader
                if iframe_sts:
                    driver.switch_to.default_content()
                run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
                run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                run_fn_spec.loader.exec_module(run_fn_module)
                if type_action:
                    run_fn_module.run(driver,type_input)
                else:
                    run_fn_module.run(driver)
            with open(file_path, "r", encoding="utf-8") as f:
                code_write = f.read()
            # return "success",{"code":code_write}
            res="success"
            error_info={"code":code_write}
        except:
            import traceback
            file_path = f"{proj_name}/{task_name}/{var_name}.py"
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    code_write = f.read()
            else:
                code_write=""
            error=traceback.format_exc()
            res_json={"error":error,
                    "code":code_write,
                    "file":file_path
                    }
            # return "failed",res_json
            res="failed"
            error_info=res_json
            

        if res=="success":
            break
        else:
            flag=True
            error_file=error_info["file"]
            error_file_path=os.path.join(org_path,error_file)
            json_path=os.path.join(org_path,"json_info\\json_xpath.json")
            with open(json_path, "r", encoding="utf-8") as f:
                json_info = json.load(f)
            json_info[var_name]="Not_assigned"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_info, f, indent=4)
            import os
            if os.path.exists(error_file_path):
                os.remove(error_file_path)
