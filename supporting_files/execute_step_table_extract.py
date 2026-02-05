def main(driver, var_name, description,user_id,org_path,flag,error_info):
    try:
        import os
        import json
        import importlib.util
        from datas.source_files import element_confirmation
        # import gemini_code_correction
        from datas.process_flow.Citrix_process import citrix_gemini_correction
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
        file_path = f"{proj_name}/{task_name}/{var_name}.py"
        if current_xpath == "Not_assigned":
            raw_xpath = xpath_find.main(description, driver)
            # Verify status
            from datas.source_files import element_confirmation
            is_valid, current_xpath = element_confirmation.element_status(var_name, raw_xpath, driver)
            # Update JSON
            json_xpath[var_name] = current_xpath
            with open(JSON_PATH, "w") as f:
                json.dump(json_xpath, f, indent=4)

            if is_valid!=True:
                while True:
                    from datas.source_files import element_confirmation
                    is_valid, current_xpath = element_confirmation.element_status(var_name, raw_xpath, driver)
                    json_xpath[var_name] = current_xpath
                    with open(JSON_PATH, "w") as f:
                        json.dump(json_xpath, f, indent=4)
                    if is_valid:
                        break

        # 2. Code Generation & Execute
        if not os.path.exists(file_path):
            if flag==False:
                citrix_gemini_correction.code_correction_table_extract(description, current_xpath, file_path, var_name, driver, user_id)
            else:
                citrix_gemini_correction.fallback_code_correction_table_extract(description, current_xpath, file_path, var_name, driver, user_id,error_info)
            run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
            if os.path.exists(run_fn_path):
                file_exists=True
            if file_exists:
                run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
                run_fn_module = importlib.util.module_from_spec(run_fn_spec)
                run_fn_spec.loader.exec_module(run_fn_module)
                data=run_fn_module.run(driver)
            else:
                return "failed",{"error":"Error Occured during the code generation for this action",
                          "code":"",
                          "file":""},data
        else:
            #run function code loader
            run_fn_path = os.path.join(org_path, f"{proj_name}/{task_name}/{var_name}.py")
            run_fn_spec = importlib.util.spec_from_file_location(f"{var_name}", run_fn_path)
            run_fn_module = importlib.util.module_from_spec(run_fn_spec)
            run_fn_spec.loader.exec_module(run_fn_module)
            data=run_fn_module.run(driver)
        with open(file_path, "r", encoding="utf-8") as f:
            code_write = f.read()
        return "success",{"code":code_write},data
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
        return "failed",res_json,""
        
