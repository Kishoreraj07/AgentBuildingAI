import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(pdf_file_path, page_limit, destination_folder):
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    reader = PdfReader(pdf_file_path)
    total_pages = len(reader.pages)

    # Get base PDF name without extension
    base_name = os.path.splitext(os.path.basename(pdf_file_path))[0]

    split_count = 1

    for start_page in range(0, total_pages, page_limit):
        writer = PdfWriter()

        end_page = min(start_page + page_limit, total_pages)

        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        output_file = os.path.join(
            destination_folder,
            f"{base_name}_split{split_count}.pdf"
        )

        with open(output_file, "wb") as f:
            writer.write(f)

        print(f"Created: {output_file}")
        split_count += 1
