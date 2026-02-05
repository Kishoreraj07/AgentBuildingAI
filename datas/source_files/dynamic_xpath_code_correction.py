import re,ast
def append_after_keyword(keyword, value, user_id):
    try:
        value=ast.literal_eval(value)
    except:
        pass
    if type(value)==dict:
        value=value["xpath"]
    matches = re.findall(r"\{([^}]+)\}", value)
    if len(matches)>0:
        file_path = "code_py/execute_code.py"

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated_lines = []
        i = 0
        total_lines = len(lines)

        target_calls = (
            "execute_step(",
            "text_data(",
            "element_status(",
            "table_df("
        )

        skip_indexes = set()
        while i < total_lines:
            if i in skip_indexes:
                i += 1
                continue
            line = lines[i]
            updated_lines.append(line)

            if f'var_name = "{keyword}"' in line or f'var_name="{keyword}"' in line:
                indent = line[:len(line) - len(line.lstrip())]

                skip_indexes = set()
                for offset in range(1, 4):
                    idx = i + offset
                    if idx < total_lines:
                        stripped = lines[idx].lstrip()
                        if stripped.startswith("add_info=") or stripped.startswith("add_info ="):
                            skip_indexes.add(idx)
                            # break
                res_code = ", ".join(matches)
                updated_lines.append(
                    f'{indent}add_info = [{res_code}]\n'
                )

                j = i + 1
                while j < total_lines:
                    call_line = lines[j]
                    stripped = call_line.lstrip()

                    if stripped.startswith(target_calls):
                        old_args = f"(driver, var_name, description, {user_id}, cwd)"
                        new_args = f"(driver, var_name, description, {user_id}, cwd, add_info)"

                        if old_args in call_line and "add_info" not in call_line:
                            call_indent = call_line[:len(call_line) - len(call_line.lstrip())]
                            updated_lines.append(
                                f'{call_indent}{stripped.replace(old_args, new_args)}'
                            )
                            j += 1
                            i = j - 1
                        break

                    updated_lines.append(call_line)
                    j += 1

                if len(skip_indexes)>0:
                    for ind in skip_indexes:
                        updated_lines.pop(ind)
                    skip_indexes=set()
                i = j
                continue

            i += 1

        return "".join(updated_lines)
    
    else:
        file_path = "code_py/execute_code.py"

        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        return file_content




# keyword="payment_checkbox"
# value="div[2]/span[1]/table[{pay_index}]"
# user_id=49
# res=append_after_keyword(keyword,value,user_id)
# with open("backup.py", "w", encoding="utf-8") as f:
#     f.write(str(res))