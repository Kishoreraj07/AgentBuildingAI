def log_action(message):
    """Log action to citrix_element_confirmation_log.txt"""
    import os
    from datetime import datetime
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "citrix_element_confirmation_log.txt")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] element_exist: {message}\n")
    except Exception as e:
        print(f"Error logging: {e}")

def element_status(var_name, description,user_id,org_path):
    try:
        import sys,os,json
        sys.path.append(r"D:\AgentFlow")
        flag=False
        error_info=""
        log_action(f"element_status called with var_name='{var_name}', description='{description}'")
        # while True:
        for i in range(10):
            if flag==False:
                error_info=""
            try:
                import os
                import json
                import importlib.util
                # import gemini_code_correction
                from datas.process_flow.Citrix_process import citrix_gemini_correction
                from datas.supporting_files.message_box_delay import show_timed_message_box
                JSON_PATH=os.path.join(org_path,"json_info/citrix_data.json")
                Task_file=os.path.join(org_path,"json_info/task_info.json")
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    json_xpath = json.load(f)

                with open(Task_file, "r", encoding="utf-8") as f:
                    task_info = json.load(f)
                proj_name=task_info["Proj_file_name"]
                task_name=task_info["Task_file_name"]
                
                var_name=var_name
                current_xpath = json_xpath.get(var_name)
                file_path = f"{proj_name}/{task_name}/{var_name}.py"
                if current_xpath == "Not_assigned":
                    # raw_xpath = xpath_find.main(description, driver)
                    # Verify status
                    from datas.process_flow.Citrix_process import citrix_element_confirmation
                    show_timed_message_box("Autowait 1")
                    log_action(f"Calling element_status for var_name='{var_name}'")
                    is_valid, current_xpath = citrix_element_confirmation.element_status(var_name)
                    log_action(f"element_status returned: is_valid={is_valid}, current_xpath='{current_xpath}'")
                    show_timed_message_box("Autowait 2")
                    # Update JSON
                    json_xpath[var_name] = current_xpath
                    with open(JSON_PATH, "w") as f:
                        json.dump(json_xpath, f, indent=4)

                    if is_valid!=True:
                        log_action(f"element_status returned invalid, retrying...")
                        while True:
                            show_timed_message_box("Autowait 2")
                            from datas.process_flow.Citrix_process import citrix_element_confirmation
                            log_action(f"Retry: Calling element_status for var_name='{var_name}'")
                            is_valid, current_xpath = citrix_element_confirmation.element_status(var_name)
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
                        citrix_gemini_correction.code_correction_element_exist(description, current_xpath, file_path, var_name, "", user_id)
                    else:
                        citrix_gemini_correction.fallback_code_correction_element_exist(description, current_xpath, file_path, var_name, "", user_id,error_info)
                    
                    run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
                    file_exists=False
                    if os.path.exists(run_fn_path):
                        file_exists=True
                    if file_exists:
                        show_timed_message_box(f"File Exists")
                        run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                        run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                        run_fn_spec.loader.exec_module(run_fn_module)
                        data=run_fn_module.run()
                    else:
                        # return "failed",{"error":"Error Occured during the code generation for this action",
                        #         "code":"",
                        #         "file":""},data
                        res="failed"
                        error_info={"error":"Error Occured during the code generation for this action",
                                "code":"",
                                "file":""}
                        return_data=data

                else:
                    #run function code loader
                    run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
                    run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                    run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                    run_fn_spec.loader.exec_module(run_fn_module)
                    data=run_fn_module.run()
                with open(file_path, "r", encoding="utf-8") as f:
                    code_write = f.read()
                # return "success",{"code":code_write},data
                res="success"
                error_info={"code":code_write}
                return_data=data
            except:
                import traceback
                file_path = f"{proj_name}/{task_name}/{var_name}.py"
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        code_write = f.read()
                else:
                    code_write=""
                # error=traceback.format_exc()
                error="Error Occurs"
                res_json={"error":error,
                        "code":"no-code",
                        "file":file_path
                        }
                # return "failed",res_json,""
                res="failed"
                error_info=res_json
                return_data=""
            if res=="success":
                # return res,data
                return return_data
            else:
                flag=True
                error_file=error_info["file"]
                error_file_path=os.path.join(org_path,error_file)
                json_path=os.path.join(org_path,"json_info\\citrix_data.json")
                with open(json_path, "r", encoding="utf-8") as f:
                    json_info = json.load(f)
                json_info[var_name]="Not_assigned"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_info, f, indent=4)
                import os
                if os.path.exists(error_file_path):
                    os.remove(error_file_path)

    except Exception as e1:
        print(e1)
        exception_file="citrix_process.txt"
        with open(exception_file, "a", encoding="utf-8") as f:
            f.write(e1 + "\n")

