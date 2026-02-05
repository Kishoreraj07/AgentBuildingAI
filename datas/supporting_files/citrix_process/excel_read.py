import pandas as pd
import os

def excel_read_file(file_path):
    """
    Reads .xlsx or .csv file and returns a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".xlsx":
        df = pd.read_excel(file_path)   # reads excel
    elif ext == ".csv":
        df = pd.read_csv(file_path)     # reads csv
    else:
        raise ValueError("Unsupported file type. Only .xlsx and .csv are allowed.")

    return df


# Example usage:
# df = load_file_to_df("data.xlsx")
# print(df)
