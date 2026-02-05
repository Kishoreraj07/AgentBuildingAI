def citrix_execute_step(var_name, description,user_id,org_path):
    import sys,os,json
    # sys.path.append(r"D:\AgentFlow")
    error_flag=False
    while True:
        if error_flag==False:
            data_info=""
        from datas.supporting_files.citrix_execute_step_main import main
        res,data_info=main(var_name, description,user_id,org_path,error_flag,data_info)
        if res=="success":
            break
        else:
            error_flag=True
            error_file=data_info["file"]
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

