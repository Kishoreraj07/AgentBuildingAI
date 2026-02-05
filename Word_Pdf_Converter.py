import subprocess
import tempfile
import os
from pathlib import Path
import time
import sys
import shutil

import aspose.words as aw

def docx_to_pdf(input_path):
    output_path=str(input_path).replace(".docx",".pdf")
    doc = aw.Document(input_path)
    doc.save(output_path)
    print(f"✅ Converted {input_path} → {output_path}")
    return output_path

class WordToPdfConverter:
    def __init__(self):
        def get_base_dir():
            if getattr(sys, 'frozen', False):
                # Running as a bundled executable
                return os.path.dirname(sys.executable)
            else:
                # Running as a normal Python script
                return os.path.dirname(os.path.abspath(__file__))

        base_dir = get_base_dir()

        # Append the relative path to LibreOffice
        self.libreoffice_exe = os.path.join(
            base_dir,
            "LibreOfficePortable", "App", "libreoffice", "program", "soffice.exe"
        )

        # print("LibreOffice exe path:", self.libreoffice_exe)
        # Your specific LibreOffice portable path
        # self.libreoffice_exe = r"C:\Users\Kishore.k\Downloads\LibreOfficePortable\App\libreoffice\program\soffice.exe"
        
        # Verify the executable exists
        if not os.path.exists(self.libreoffice_exe):
            raise FileNotFoundError(f"LibreOffice executable not found at: {self.libreoffice_exe}")
        print(f"✓ LibreOffice found at: {self.libreoffice_exe}")

    def convert_to_pdf_bytes(self, word_file_path, timeout=120):
        """
        Convert Word document to PDF and return as bytes
        """
        word_path = Path(word_file_path)
        if not word_path.exists():
            raise FileNotFoundError(f"Word file not found: {word_file_path}")
        if not word_path.suffix.lower() in ['.doc', '.docx']:
            raise ValueError("File must be .doc or .docx format")
        print(f"Converting: {word_path.name}")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            try:
                cmd = [
                    self.libreoffice_exe,
                    '--headless',
                    '--invisible',
                    '--nodefault',
                    '--nolockcheck',
                    '--nologo',
                    '--norestore',
                    '--convert-to', 'pdf',
                    '--outdir', str(temp_dir_path),
                    str(word_path)
                ]
                env = os.environ.copy()
                env['TEMP'] = str(temp_dir_path)
                env['TMP'] = str(temp_dir_path)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    check=True
                )
                pdf_file = temp_dir_path / f"{word_path.stem}.pdf"
                wait_time = 0
                max_wait = 10
                while not pdf_file.exists() and wait_time < max_wait:
                    time.sleep(0.5)
                    wait_time += 0.5
                if not pdf_file.exists():
                    raise Exception("PDF file was not created")
                with open(pdf_file, 'rb') as f:
                    pdf_bytes = f.read()
                print(f"✓ Conversion successful! PDF size: {len(pdf_bytes):,} bytes")
                return pdf_bytes
            except subprocess.TimeoutExpired:
                raise Exception(f"Conversion timed out after {timeout} seconds")
            except subprocess.CalledProcessError as e:
                error_details = e.stderr.strip() if e.stderr else "Unknown error"
                raise Exception(f"LibreOffice conversion failed: {error_details}")

    def convert_bytes_to_pdf(self, word_bytes, original_filename="document.docx", timeout=120):
        """
        Convert Word document bytes to PDF bytes
        """
        if not original_filename.lower().endswith(('.doc', '.docx')):
            raise ValueError("Filename must end with .doc or .docx")
        with tempfile.NamedTemporaryFile(suffix=Path(original_filename).suffix, delete=False) as temp_file:
            temp_file.write(word_bytes)
            temp_word_path = temp_file.name
        try:
            return self.convert_to_pdf_bytes(temp_word_path, timeout)
        finally:
            if os.path.exists(temp_word_path):
                os.unlink(temp_word_path)

    def save_pdf(self, pdf_bytes, output_path):
        """
        Save PDF bytes to file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        print(f"✓ PDF saved to: {output_path}")

def word_file_to_pdf_bytes(word_file_path):
    """Convert Word file to PDF bytes (one-liner)"""
    converter = WordToPdfConverter()
    return converter.convert_to_pdf_bytes(word_file_path)

def word_bytes_to_pdf_bytes(word_bytes, filename="document.docx"):
    """Convert Word bytes to PDF bytes (one-liner)"""
    converter = WordToPdfConverter()
    return converter.convert_bytes_to_pdf(word_bytes, filename)

def main_word_pdf_converter(input_path):
    try:
        # Define output directory
        output_dir = Path("video_transcript_pdf_output")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Initialize converter
        converter = WordToPdfConverter()
        # Convert Word to PDF
        pdf_bytes = converter.convert_to_pdf_bytes(input_path)
        # Define output path
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".pdf"
        output_path = output_dir / output_filename
        # Save PDF
        converter.save_pdf(pdf_bytes, output_path)
        print(f"Converted successfully! PDF size: {len(pdf_bytes)} bytes")
        return str(output_path)
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the Word file exists and is not corrupted")
        print("2. Ensure LibreOffice portable is at the correct path")
        print("3. Check that the Word file is not currently open in another program")
        return None
