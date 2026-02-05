import pandas as pd
import json
from pdf_to_table import gemini_pdf_response
def pdf_to_table_extract(pdf_path,description):
    while True:
        list_dict=gemini_pdf_response(pdf_path,description)
        try:
            df = pd.DataFrame(list_dict[0])
            break
        except:
            try:
                data_dict=list_dict
                min_len = min(len(v) for v in data_dict[0].values() if isinstance(v, list))
                for key, value in data_dict[0].items():
                    if isinstance(value, list) and len(value) > min_len:
                        data_dict[0][key] = value[:min_len]
                df=pd.DataFrame(data_dict[0])
                break
            except:
                pass
    return df