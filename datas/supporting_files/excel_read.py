import pandas as pd
import os

def excel_read_file(file_path, start_row=None, end_row=None, sheet_name=None):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Read file WITHOUT header first
    if ext == ".xlsx":
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name if sheet_name is not None else 0,
            header=None
        )

    elif ext == ".csv":
        df = pd.read_csv(file_path, header=None)

    else:
        raise ValueError("Unsupported file type. Only .xlsx and .csv are allowed.")

    # Determine header row (0-based)
    header_row = (start_row - 1) if start_row else 0

    # Assign header
    df.columns = df.iloc[header_row]

    # Data starts after header row
    data_start = header_row + 1

    # Apply end row slicing (1-based inclusive)
    if end_row:
        df = df.iloc[data_start:end_row]
    else:
        df = df.iloc[data_start:]

    df = df.reset_index(drop=True)

    return df
