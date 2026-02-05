import fitz  # PyMuPDF
import os

def highlight_text_in_pdf(pdf_path, text, output_path=None):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # If output path not provided, auto-generate one
    if output_path is None:
        base, ext = os.path.splitext(pdf_path)
        output_path = f"{base}_highlighted{ext}"

    doc = fitz.open(pdf_path)

    for page in doc:
        # Search for text occurrences
        text_instances = page.search_for(text)

        for inst in text_instances:
            highlight = page.add_highlight_annot(inst)
            highlight.update()

    doc.save(output_path)
    doc.close()

    print(f"Highlighted PDF saved at: {output_path}")
