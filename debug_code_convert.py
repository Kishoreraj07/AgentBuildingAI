def code_convert(code_str):
    clean_code = code_str.strip("`").replace("python", "", 1).strip()
    debug_line="import pdb\npdb.set_trace()"
    final_code=f"{debug_line}\n{clean_code}"
    return final_code
