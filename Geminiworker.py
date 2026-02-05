# GeminiWorker_PDF.py
from PyQt5.QtCore import QThread, pyqtSignal
import traceback
import gemini_pdf
import pythoncom
import sys

class GeminiWorker_PDF(QThread):
    """Thread to process PDF via gemini_pdf safely with COM"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.result = None
        self.exception = None
        self.com_initialized = False

    def run(self):
        """Run the PDF processing with proper COM management"""
        try:
            # Initialize COM for this thread only if needed
            try:
                pythoncom.CoInitialize()
                self.com_initialized = True
                print(f"[THREAD] COM initialized for file processing thread")
            except Exception as com_error:
                print(f"[THREAD] COM initialization failed: {com_error}")
                # Continue without COM if it fails
                pass
            
            # Process the file
            print(f"[THREAD] Starting file processing: {self.file_path}")
            self.result = gemini_pdf.gemini_pdf_response(self.file_path)
            print(f"[THREAD] File processing completed successfully")
            
        except Exception as e:
            error_msg = f"File processing error: {str(e)}"
            print(f"[THREAD] {error_msg}")
            self.exception = traceback.format_exc()
            self.error.emit(error_msg)
            
        finally:
            # Clean up COM only if we initialized it in this thread
            if self.com_initialized:
                try:
                    pythoncom.CoUninitialize()
                    print(f"[THREAD] COM uninitialized for file processing thread")
                except Exception as cleanup_error:
                    print(f"[THREAD] COM cleanup warning: {cleanup_error}")
            
            # Always emit finished signal
            self.finished.emit()
            print(f"[THREAD] File processing thread finished")
