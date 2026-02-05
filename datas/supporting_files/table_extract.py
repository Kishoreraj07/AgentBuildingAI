#table_extract.py

def log_action(message):
    """Log action to web_element_confirmation.txt"""
    import os
    from datetime import datetime
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_element_confirmation.txt")
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] table_extract: {message}\n")
    except Exception as e:
        print(f"Error logging: {e}")

def table_df(driver, var_name, description,user_id,org_path,app_info=None):
    import sys,os,json
    from datas.supporting_files.message_box_delay import show_timed_message_box
    # sys.path.append(r"D:\AgentFlow")
    flag=False
    log_action(f"table_df called with var_name='{var_name}', description='{description}'")
    while True:
        if flag==False:
            error_info=""
        try:
            import os
            import json
            import time
            import importlib.util
            from datas.source_files import element_confirmation
            # import gemini_code_correction
            # from datas.process_flow.Citrix_process import citrix_gemini_correction
            from datas.source_files import gemini_code_correction
            from datas.source_files import verify_xpath
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
            file_path = os.path.join(org_path, proj_name, task_name, f"{var_name}.py")
            if current_xpath == "Not_assigned":
                raw_xpath = xpath_find.main(description, driver)
                # Verify status
                from datas.source_files import element_confirmation
                # show_timed_message_box("Autowait 1")
                time.sleep(2)
                log_action(f"Calling element_status for var_name='{var_name}'")
                is_valid, current_xpath = element_confirmation.element_status(var_name, raw_xpath, driver)
                if "iframe" in current_xpath:
                    iframe_flag=True
                log_action(f"element_status returned: is_valid={is_valid}, current_xpath='{current_xpath}'")
                pageination_res=element_confirmation.show_confirmation_popup("Is this pagination table?")
                pageination_flag=False
                if pageination_res:
                    pageination_flag=True
                    nxt_ntn_isvalid,nxt_btn_xpath=element_confirmation.xpath_status("Confirm the Next button Field",driver)
                    if nxt_ntn_isvalid:
                        dis_btn_isvalid,dis_btn_xpath=element_confirmation.xpath_status("Confirm the Disable button Field",driver)
                    json_path = os.path.join("json_info", "json_xpath.json")
                    # Read JSON
                    # with open(json_path, "r", encoding="utf-8") as f:
                    #     json_info = json.load(f)
                    json_xpath.update({
                        f"{var_name}_nxt_btn": nxt_btn_xpath,
                        f"{var_name}_dis_btn": dis_btn_xpath
                    })
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(json_xpath, f, indent=4)
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
                        if "iframe" in current_xpath:
                            iframe_flag=True
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
                    if not pageination_flag:
                        gemini_code_correction.code_correction_table_extract(description, current_xpath, file_path, var_name, driver, user_id)
                    else:
                        gemini_code_correction.code_correction_pageination_table(description, current_xpath, file_path, var_name, driver, user_id)
                else:
                    if not pageination_flag:
                        gemini_code_correction.fallback_code_correction_table_extract(description, current_xpath, file_path, var_name, driver, user_id,error_info)
                    else:
                        gemini_code_correction.fallback_pagenination_extract(description, current_xpath, file_path, var_name, driver, user_id)
                if iframe_flag:
                    driver.switch_to.default_content()
                run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
                file_exists=False
                if os.path.exists(run_fn_path):
                    # show_timed_message_box("File Exist")
                    time.sleep(2)
                    file_exists=True
                if file_exists:
                    run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                    run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                    run_fn_spec.loader.exec_module(run_fn_module)
                    data=run_fn_module.run(driver)
                else:
                    # return "failed",{"error":"Error Occured during the code generation for this action",
                    #         "code":"",
                    #         "file":""},data
                    show_timed_message_box("File Not Exist")
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
                data=run_fn_module.run(driver)
            with open(file_path, "r", encoding="utf-8") as f:
                code_write = f.read()
            # return "success",{"code":code_write},data
            res="success"
            error_info={"code":code_write}
            return_data=data
        except:
            import traceback
            traceback.print_exc()
            file_path = os.path.join(org_path, proj_name, task_name, f"{var_name}.py")
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
            # return "failed",res_json,""
            res="failed"
            error_info=res_json
            return_data=""
            

        if res=="success":
            return return_data
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