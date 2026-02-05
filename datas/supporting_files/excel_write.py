import os
import pandas as pd

def write_df_to_file(data_df: pd.DataFrame, excel_file_path: str):
    df=data_df
    file_path=excel_file_path
    index: bool = False
    ext = os.path.splitext(file_path)[1].lower()

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if ext == ".csv":
        df.to_csv(file_path, index=index)
    elif ext == ".xlsx":
        df.to_excel(file_path, index=index, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    print(f"DataFrame written to: {file_path}")
