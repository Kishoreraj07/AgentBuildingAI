import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datas.source_files.web_element_picker import element_picker
from datas.source_files.xpath_find import main
from datas.source_files import style_loader
import tempfile
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox


class XPathModifyDialog(QDialog):
    """Standalone XPath modification dialog with Web element picker"""
    
    def __init__(self, driver, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.extracted_xpath = ""
        self.result = False
        self.html_content = ""
        
        self.setupUI()
        
        # Ensure dialog stays independent
        self.raise_()
        self.activateWindow()
        
    def setupUI(self):
        """Setup the XPath modification dialog UI"""
        # Make dialog standalone and independent from main application
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Show without stealing focus from main app
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        
        # Create main container with rounded corners (no border)
        container = QWidget(self)
        container.setGeometry(0, 0, 620, 249)
        container.setStyleSheet("""
            QWidget {
                background-color: #414141;
                border: none;
                border-radius: 15px;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)  # Remove top margin for title bar
        layout.setSpacing(0)

        # Title bar with dark background and rounded top corners
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("""
            QWidget {
                background: #333333;
                border-radius: 20px 20px 0px 0px;
                border: none;
            }
        """)

        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)

        # Title label with icon and text
        title_label = QLabel("XPath Modification")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro';
                font-weight: bold;
                font-size: 16px;
                background: transparent;
                border: none;
            }
        """)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()  # Push title to left, close button to right
        
        # Close button with X design
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Create X using paintEvent override
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Set pen for white lines
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            
            # Draw X lines (25% margins on all sides)
            margin = int(24 * 0.25)  # 25% of 24px = 6px margin
            start_x = margin
            start_y = margin
            end_x = 24 - margin
            end_y = 24 - margin
            
            # Draw first diagonal line (top-left to bottom-right)
            painter.drawLine(start_x, start_y, end_x, end_y)
            
            # Draw second diagonal line (top-right to bottom-left)
            painter.drawLine(end_x, start_y, start_x, end_y)
            
        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

        layout.addWidget(title_container)

        # Add spacing between title and content
        layout.addSpacing(20)
        
        # Instruction label
        instruction_label = QLabel("Click the Element Picker button to select an element, then confirm to get the XPath:")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-style: normal;
                font-weight: 400;
                font-size: 16px;
                line-height: 19px;
                letter-spacing: 0.05em;
                text-align: center;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # # Web element picker button centered
        # picker_layout = QHBoxLayout()
        # picker_layout.addStretch()
        # self.web_picker_btn = QPushButton("Element Picker")
        # self.web_picker_btn.setFixedSize(150, 45)
        # self.web_picker_btn.setStyleSheet("""
        #     QPushButton {   
        #         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
        #         color: #FFFFFF;
        #         border: none;
        #         border-radius: 10px;
        #         font-family: 'Asen Pro';
        #         font-weight: 600;
        #         font-size: 14px;
        #         letter-spacing: 0.05em;
        #         padding: 8px;
        #     }
        #     QPushButton:hover {
        #         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699);
        #     }
        #     QPushButton:pressed {
        #         background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455);
        #     }
        # """)
        # self.web_picker_btn.clicked.connect(self.pick_web_element)
        # picker_layout.addWidget(self.web_picker_btn)
        # picker_layout.addStretch()
        # layout.addLayout(picker_layout)
        
        # Web element picker and read page buttons centered
        picker_layout = QHBoxLayout()
        picker_layout.addStretch()

        # Element Picker button
        self.web_picker_btn = QPushButton("Element Picker")
        self.web_picker_btn.setFixedSize(150, 45)
        self.web_picker_btn.setStyleSheet("""
            QPushButton {   
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #008AB3, stop:1 #005B7F);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0099CC, stop:1 #006699);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007799, stop:1 #004455);
            }
        """)
        self.web_picker_btn.clicked.connect(self.pick_web_element)
        picker_layout.addWidget(self.web_picker_btn)

        # Spacer between buttons
        picker_layout.addSpacing(20)  # space between the two buttons

        # Read Page button
        self.read_page_btn = QPushButton("Read Page")
        self.read_page_btn.setFixedSize(150, 45)
        self.read_page_btn.setStyleSheet("""
            QPushButton {   
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00B37E, stop:1 #057A55);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00D191, stop:1 #059966);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #009966, stop:1 #045533);
            }
        """)
        self.read_page_btn.clicked.connect(self.read_page)
        picker_layout.addWidget(self.read_page_btn)

        picker_layout.addStretch()
        layout.addLayout(picker_layout)

        
        # XPath display area
        xpath_label = QLabel("Selected XPath:")
        xpath_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro';
                font-weight: bold;
                font-size: 12px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(xpath_label)
        
        self.xpath_display = QTextEdit()
        self.xpath_display.setPlaceholderText("No XPath selected yet. Click the WEB button to select an element or type XPath manually.")
        self.xpath_display.setFixedHeight(80)
        self.xpath_display.setReadOnly(False)
        self.xpath_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Asen Pro';
                font-size: 11px;
            }
        """)
        
        # Connect text change signal to enable/disable confirm button
        self.xpath_display.textChanged.connect(self.on_xpath_text_changed)
        
        layout.addWidget(self.xpath_display)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # Confirm button
        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setFixedSize(100, 45)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                qproperty-icon: none;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-family: 'Asen Pro';
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455);
            }
            QPushButton:disabled {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF; /* Changed to match Cancel button's text color */
                opacity: 0.6; /* Slight transparency to indicate disabled */
            }
        """)
        self.confirm_btn.setEnabled(False)  # Disabled until XPath is selected
        self.confirm_btn.clicked.connect(self.confirm_xpath)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        layout.addLayout(button_layout)
    
    def on_xpath_text_changed(self):
        """Handle text changes in XPath display to enable/disable confirm button"""
        try:
            # Get current text content
            current_text = self.xpath_display.toPlainText().strip()
            
            # Enable confirm button if there's any text, disable if empty
            if current_text:
                self.confirm_btn.setEnabled(True)
                # Update styling to show active state
                self.xpath_display.setStyleSheet("""
                    QTextEdit {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 2px solid #0078d4;
                        border-radius: 8px;
                        padding: 8px;
                        font-family: 'Asen Pro';
                        font-size: 11px;
                    }
                """)
                print(f"[OK] Confirm button enabled - XPath text: {current_text[:50]}...")
            else:
                self.confirm_btn.setEnabled(False)
                # Reset styling to default state
                self.xpath_display.setStyleSheet("""
                    QTextEdit {
                        background-color: #1e1e1e;
                        color: #ffffff;
                        border: 2px solid #404040;
                        border-radius: 8px;
                        padding: 8px;
                        font-family: 'Asen Pro';
                        font-size: 11px;
                    }
                """)
                print("[WARN] Confirm button disabled - XPath text is empty")
                
        except Exception as e:
            print(f"[ERROR] Error in on_xpath_text_changed: {e}")
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self._mouse_pressed and self._mouse_pos is not None:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()
    
    def pick_web_element(self):
        """Pick web element using element_picker"""
        try:
            if not self.driver:
                QMessageBox.warning(self, "Error", "No web driver available.")
                return
            
            # Minimize dialog during element picking to allow user to see the webpage
            self.showMinimized()
            
            # Use element_picker to get XPath
            xpath = element_picker(self.driver)
            
            # Restore dialog after element picking
            self.showNormal()
            self.raise_()
            self.activateWindow()
            
            if xpath:
                self.extracted_xpath = xpath
                self.xpath_display.setPlainText(xpath)
                
                # Update styling to show success (green for WEB button selection)
                self.xpath_display.setStyleSheet("""
                    QTextEdit {
                        background-color: #1e1e1e;
                        color: #00ff00;
                        border: 2px solid #28a745;
                        border-radius: 8px;
                        padding: 8px;
                        font-family: 'Asen Pro';
                        font-size: 11px;
                    }
                """)
                
                # Enable confirm button (this will be handled by textChanged signal as well)
                self.confirm_btn.setEnabled(True)
                
                # Update placeholder text to show success
                self.xpath_display.setPlaceholderText("[OK] XPath selected successfully! Click Confirm to proceed.")
                
                print(f"[OK] XPath selected via WEB button: {xpath}")
                print("[OK] Dialog stayed open, waiting for user confirmation...")
                print("[OK] Confirm button enabled")
            else:
                QMessageBox.information(self, "Info", "No element was selected.")
                print(" No element was selected")
                
        except Exception as e:
            error_msg = f"Failed to pick element: {str(e)}"
            QMessageBox.warning(self, "Error", error_msg)
            print(f"[ERROR] Element picker error: {e}")
            


    # def read_page(driver):
    #     """
    #     Reads the current page HTML from Selenium driver, stores it in a temporary file,
    #     and returns the file path if there is content. Deletes the file if content is empty.
    #     """
    #     try:
    #         html_content = driver.page_source

    #         # Check if HTML content is not empty
    #         if not html_content.strip():
    #             print("[INFO] Page source is empty. No file created.")
    #             return None

    #         # Create a temporary file to store HTML
    #         with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp_file:
    #             tmp_file.write(html_content)
    #             tmp_file_path = tmp_file.name

    #         print(f"[INFO] HTML content saved to temporary file: {tmp_file_path}")
    #         return html_content

    #     except Exception as e:
    #         print(f"[ERROR] Failed to read page: {str(e)}")
    #         return None
    
    # def read_page(self):
    #     """
    #     Reads the current web page using Selenium's driver
    #     and stores the HTML content in a variable for later use.
    #     """
    #     try:
    #         if hasattr(self, 'driver') and self.driver:
    #             # ✅ Get the HTML content from the active Selenium page
    #             self.html_content = self.driver.page_source
                
    #             # Optional: feedback to console or UI
    #             print("[INFO] Page HTML content successfully read and stored.")
    #             print(f"[INFO] HTML length: {len(self.html_content)} characters")

    #             # Optional message box
    #             QMessageBox.information(self, "Read Page", "HTML content successfully captured!")
    #         else:
    #             QMessageBox.warning(self, "Error", "No active driver found.")
    #             self.html_content = ""
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Failed to read page: {str(e)}")
    #         self.html_content = ""

    #     return self.html_content
    
    def read_page(self):
        """
        Reads the current web page using Selenium's driver
        and saves the HTML content into a file named 'html_file_content.html'
        inside the 'page_html' folder.
        Returns the saved file path.
        """
        try:
            if hasattr(self, 'driver') and self.driver:
               
                # Get HTML content
                html_content = self.driver.page_source

                # Create output directory if not exists
                output_dir = os.path.join(os.getcwd(), "page_html")
                os.makedirs(output_dir, exist_ok=True)

                # Fixed filename (no timestamp)
                file_path = os.path.join(output_dir, "html_file_content.html")

                # Write content to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                print(f"[INFO] Page HTML content saved to: {file_path}")
                print(f"[INFO] HTML length: {len(html_content)} characters")

                QMessageBox.information(self, "Read Page", f"HTML content saved to:\n{file_path}")
                return file_path
            else:
                QMessageBox.warning(self, "Error", "No active driver found.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read page: {str(e)}")


        
    
    
    def confirm_xpath(self):
        """Confirm XPath selection and close dialog"""
        # Get current text from the input field
        current_xpath = self.xpath_display.toPlainText().strip()
        
        if current_xpath:
            # Update extracted_xpath with whatever is in the text field
            self.extracted_xpath = current_xpath
            self.result = True
            print(f"[OK] XPath confirmed: {current_xpath}")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "No XPath entered. Please enter an XPath or select an element first.")
    
    def reject(self):
        """Handle dialog rejection"""
        self.result = False
        self.extracted_xpath = ""
        print("[WARN] XPath selection cancelled - reject() called")
        super().reject()
    
    def closeEvent(self, event):
        """Handle close event"""
        print("[WARN] Dialog closeEvent triggered")
        self.result = False
        self.extracted_xpath = ""
        super().closeEvent(event)

def mod_xpath_old(driver):
    """
    Show XPath modification dialog and return selected XPath
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        str: Selected XPath if confirmed, empty string if cancelled
    """
    # Check if we're running in a worker thread
    import threading
    current_thread = threading.current_thread()
    
    # If we're in the main thread, show dialog directly
    if current_thread.name == 'MainThread':
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create and show dialog
        dialog = XPathModifyDialog(driver)
        
        # Execute dialog and wait for user action
        result = dialog.exec_()
        
        print(f" Dialog result: {result}")
        print(f" Dialog.result: {dialog.result}")
        print(f" Extracted XPath: {dialog.extracted_xpath}")
        print(f" TextEdit content: {dialog.xpath_display.toPlainText()}")
        
        # Use whatever is inside the text box when Confirm is pressed
        if result == QDialog.Accepted and dialog.result:
            final_xpath = dialog.xpath_display.toPlainText().strip()
            if final_xpath:
                print(f"[OK] Returning XPath from text box: {final_xpath}")
                return final_xpath
        
        print("[WARN] Returning empty string - dialog was cancelled or no XPath entered")
        return ""
    else:
        # We're in a worker thread - need to communicate with main thread
        print(f"[INFO] mod_xpath called from worker thread: {current_thread.name}")
        print("[INFO] Using signal-based communication with main thread")
        
        # Try to get the ExecuteCodeWorker instance from global reference
        try:
            # Import the global reference
            import main_process
            execute_worker = main_process._current_execute_worker
            
            print(f"[INFO] Execute worker: {execute_worker}")
            print(f"[INFO] Execute worker type: {type(execute_worker)}")
            
            if execute_worker and hasattr(execute_worker, 'xpath_modification_requested'):
                print("[OK] Found xpath_modification_requested signal")
                
                # Emit signal to main thread
                execute_worker.xpath_modification_requested.emit(driver)
                print("[INFO] Signal emitted to main thread")
                
                # Wait for response from main thread
                print("[INFO] Waiting for response from main thread...")
                event_triggered = execute_worker.xpath_modification_event.wait(timeout=60)  # 60 second timeout for xpath modification
                
                if event_triggered:
                    # Get the result
                    result = execute_worker.xpath_modification_result
                    
                    # Reset the event for next use
                    execute_worker.xpath_modification_event.clear()
                    
                    print(f"[OK] Received XPath response from main thread: {result}")
                    return result
                else:
                    print("[WARN] Timeout waiting for XPath response from main thread")
                    return ""
            else:
                print("[ERROR] Execute worker not found or doesn't have xpath_modification_requested signal")
                if execute_worker:
                    print(f"[ERROR] Available attributes: {[attr for attr in dir(execute_worker) if 'xpath' in attr.lower()]}")
                return ""
                
        except Exception as e:
            print(f"[ERROR] Error in signal-based xpath modification: {e}")
            import traceback
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return ""
        
def mod_xpath(driver):
    xpath=element_picker(driver)
    return xpath
# # Example usage
# if __name__ == "__main__":
#     # This is just for testing - you would pass actual driver
#     print("XPath verification module loaded successfully")