import sys
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PIL import ImageGrab
from datas.process_flow.Citrix_process import single_element_picker
# import single_element_picker
from datas.process_flow.Citrix_process import bound_index_fix
# import bound_index_fix
# import style_loader
from PyQt5.QtSvg import QSvgRenderer

class SnippingTool(QWidget):
    """Snipping tool for capturing screen regions"""
    
    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.screenshot = None
        self.captured_region = None
        
        # Make window fullscreen and transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        
        # Take screenshot of entire screen
        self.take_screenshot()
        
        # Set cursor to crosshair
        self.setCursor(Qt.CrossCursor)
        
    def take_screenshot(self):
        """Take screenshot of entire screen"""
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
    def paintEvent(self, event):
        """Paint the screenshot and selection rectangle"""
        painter = QPainter(self)
        
        # Draw the screenshot
        painter.drawPixmap(0, 0, self.screenshot)
        
        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # If we have a selection, draw it
        if not self.start_point.isNull() and not self.end_point.isNull():
            # Clear the selected area (remove overlay)
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, QColor(0, 0, 0, 0))
            
            # Draw selection border
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)
            
    def mousePressEvent(self, event):
        """Start selection"""
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()
            
    def mouseMoveEvent(self, event):
        """Update selection"""
        if not self.start_point.isNull():
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Finish selection and capture"""
        if event.button() == Qt.LeftButton and not self.start_point.isNull():
            self.end_point = event.pos()
            self.capture_selection()
            self.close()
            
    def keyPressEvent(self, event):
        """Handle escape key to cancel"""
        if event.key() == Qt.Key_Escape:
            self.captured_region = None
            self.close()
            
    def capture_selection(self):
        """Capture the selected region"""
        if not self.start_point.isNull() and not self.end_point.isNull():
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            if selection_rect.width() > 0 and selection_rect.height() > 0:
                self.captured_region = self.screenshot.copy(selection_rect)


class XPathModifyDialog(QDialog):
    """Standalone XPath modification dialog with Web element picker"""
    
    def __init__(self, desc="element", parent=None):
        super().__init__(parent)
        # self.driver = driverdriver
        self.extracted_xpath = ""
        self.result = False
        self.desc = desc  # Store the description for image naming
        
        self.setupUI()
        
        # Ensure dialog stays independent
        self.raise_()
        self.activateWindow()
        
    def setupUI(self):
        """Setup the XPath modification dialog UI with enhanced design from second code"""
        # Make dialog standalone and independent from main application
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Horizontal compact size
        self.setFixedSize(1020, 120)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        
        # Create main container with rounded corners
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 1020, 120)
        container = self.container
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2D2D2D, stop:1 #1A1A1A);
                border: 2px solid #00CED1;
                border-radius: 12px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(15, 12, 15, 12)
        main_layout.setSpacing(8)
        
        # Top row: label + buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(15)
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        element_display_desc = self.desc.replace('_', ' ').replace('field', '').strip().title()
        self.text_label = QLabel(f"Select <b>{element_display_desc}</b> Element")
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Asen Pro';
                font-size: 24px;
                background: transparent;
                border: none;
            }
        """)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setWordWrap(True)
        top_row.addWidget(self.text_label, 1)
        
        # Button container on the right
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Element Picker button with SVG icon
        picker_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-mouse-pointer-click-icon lucide-mouse-pointer-click">
        <path d="M14 4.1 12 6"/>
        <path d="m5.1 8-2.9-.8"/>
        <path d="m6 12-1.9 2"/>
        <path d="M7.2 2.2 8 5.1"/>
        <path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>
        </svg>
        """
        picker_renderer = QSvgRenderer(QByteArray(picker_svg_data))
        picker_pixmap = QPixmap(32, 32)
        picker_pixmap.fill(Qt.transparent)
        painter = QPainter(picker_pixmap)
        picker_renderer.render(painter)
        painter.end()

        self.web_picker_btn = QPushButton()
        self.web_picker_btn.setFixedSize(32, 32)
        self.web_picker_btn.setIcon(QIcon(picker_pixmap))
        self.web_picker_btn.setIconSize(QSize(24, 24))
        self.web_picker_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        self.web_picker_btn.setCursor(Qt.PointingHandCursor)
        self.web_picker_btn.setToolTip("Element Picker")
        self.web_picker_btn.clicked.connect(self.pick_web_element)
        button_layout.addWidget(self.web_picker_btn)
        
        # Image Capture button with SVG icon
        img_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" 
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7" 
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
            class="lucide lucide-image-play-icon lucide-image-play">
            <path d="M15 15.003a1 1 0 0 1 1.517-.859l4.997 2.997a1 1 0 0 1 0 1.718l-4.997 2.997a1 1 0 0 1-1.517-.86z"/>
            <path d="M21 12.17V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6"/>
            <path d="m6 21 5-5"/>
            <circle cx="9" cy="9" r="2"/>
        </svg>
        """
        img_renderer = QSvgRenderer(QByteArray(img_svg_data))
        img_pixmap = QPixmap(32, 32)
        img_pixmap.fill(Qt.transparent)
        painter = QPainter(img_pixmap)
        img_renderer.render(painter)
        painter.end()

        self.image_capture_btn = QPushButton()
        self.image_capture_btn.setFixedSize(32, 32)
        self.image_capture_btn.setIcon(QIcon(img_pixmap))
        self.image_capture_btn.setIconSize(QSize(24, 24))
        self.image_capture_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        self.image_capture_btn.setCursor(Qt.PointingHandCursor)
        self.image_capture_btn.setToolTip("Image Capture")
        self.image_capture_btn.clicked.connect(self.capture_image_region)
        button_layout.addWidget(self.image_capture_btn)
        
        # Confirm button with SVG icon
        confirm_svg_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
            viewBox="0 0 24 24" fill="none" stroke="#f8f7f7"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-check-icon lucide-check">
        <path d="M20 6 9 17l-5-5"/>
        </svg>
        """
        confirm_renderer = QSvgRenderer(QByteArray(confirm_svg_data))
        confirm_pixmap = QPixmap(32, 32)
        confirm_pixmap.fill(Qt.transparent)
        painter = QPainter(confirm_pixmap)
        confirm_renderer.render(painter)
        painter.end()

        self.confirm_btn = QPushButton()
        self.confirm_btn.setFixedSize(32, 32)
        self.confirm_btn.setIcon(QIcon(confirm_pixmap))
        self.confirm_btn.setIconSize(QSize(24, 24))
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                opacity: 0.3;
            }
        """)
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setToolTip("Confirm")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.confirm_xpath)
        button_layout.addWidget(self.confirm_btn)
        
        # Dropdown toggle button
        dropdown_btn = QPushButton("▾")
        dropdown_btn.setFixedSize(32, 32)
        dropdown_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background: transparent;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); }
            QPushButton:pressed { background: rgba(255,255,255,0.16); }
        """)
        dropdown_btn.setCursor(Qt.PointingHandCursor)
        dropdown_btn.setToolTip("Enter custom data")
        dropdown_btn.clicked.connect(self.toggle_input_panel)
        self.dropdown_btn = dropdown_btn
        button_layout.addWidget(dropdown_btn)
        
        top_row.addLayout(button_layout)
        main_layout.addLayout(top_row)
        
        # Input panel (hidden by default)
        self.input_panel = QWidget(container)
        input_layout = QHBoxLayout(self.input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.xpath_display = QLineEdit()
        self.xpath_display.setPlaceholderText("Enter your data here")
        self.xpath_display.setStyleSheet("""
            QLineEdit {
                color: #FFFFFF;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #00CED1; }
        """)
        self.xpath_display.textChanged.connect(self.on_xpath_text_changed)
        
        check_btn = QPushButton("Check")
        check_btn.setFixedHeight(32)
        check_btn.setStyleSheet("""
            QPushButton {
                color: #0E0E0E;
                background: #00CED1;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #12dfe2; }
            QPushButton:pressed { background: #0fb8bb; }
        """)
        check_btn.setCursor(Qt.PointingHandCursor)
        check_btn.clicked.connect(self.on_check_clicked)
        self.check_btn = check_btn
        
        input_layout.addWidget(self.xpath_display, 1)
        input_layout.addWidget(check_btn)
        self.input_panel.setVisible(False)
        main_layout.addWidget(self.input_panel)
        
        # Add fade-in animation
        self.fade_effect = QGraphicsOpacityEffect()
        container.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()
        
        # Add pulsing glow effect
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.toggle_glow)
        self.glow_timer.start(800)
        self.glow_state = False

    def toggle_glow(self):
        """Toggle glow effect for attention"""
        try:
            if self.glow_state:
                self.container.setStyleSheet("""
                    QWidget {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #2D2D2D, stop:1 #1A1A1A);
                        border: 2px solid rgba(0, 206, 209, 0.6);
                        border-radius: 12px;
                    }
                """)
            else:
                self.container.setStyleSheet("""
                    QWidget {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #2D2D2D, stop:1 #1A1A1A);
                        border: 2px solid rgba(0, 206, 209, 1.0);
                        border-radius: 12px;
                    }
                """)
            self.glow_state = not self.glow_state
        except Exception as e:
            print(f"Error toggling glow: {e}")

    def toggle_input_panel(self):
        """Show/Hide the custom XPath input panel and adjust height"""
        try:
            if self.input_panel.isVisible():
                self.input_panel.setVisible(False)
                self.setFixedHeight(120)
                self.container.setGeometry(0, 0, self.width(), 120)
            else:
                self.input_panel.setVisible(True)
                self.setFixedHeight(170)
                self.container.setGeometry(0, 0, self.width(), 170)
        except Exception as e:
            print(f"Error toggling input panel: {e}")

    def on_check_clicked(self):
        """Apply user-entered data and enable confirm"""
        try:
            text = self.xpath_display.text().strip()
            if not text:
                self.xpath_display.setStyleSheet(self.xpath_display.styleSheet() + "\nQLineEdit { border-color: #ff6b6b; }")
                QTimer.singleShot(600, lambda: self.xpath_display.setStyleSheet(self.xpath_display.styleSheet().replace("border-color: #ff6b6b;", "border-color: #00CED1;")))
                return
            # Update styling to show data is checked
            self.xpath_display.setStyleSheet("""
                QLineEdit {
                    color: #00ff00;
                    background: rgba(255,255,255,0.08);
                    border: 1px solid #28a745;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-size: 12px;
                }
            """)
            self.confirm_btn.setEnabled(True)
        except Exception as e:
            print(f"Error on check clicked: {e}")

    def on_xpath_text_changed(self):
        """Handle text changes in XPath display to enable/disable confirm button"""
        try:
            current_text = self.xpath_display.text().strip()
            
            if current_text:
                self.confirm_btn.setEnabled(True)
                print(f"[OK] Confirm button enabled - text: {current_text[:50]}...")
            else:
                self.confirm_btn.setEnabled(False)
                print("[WARN] Confirm button disabled - text is empty")
                
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
        """Pick element without driver"""
        try:
            # Fully hide the dialog so picker is unblocked
            self.hide()
            QApplication.processEvents()
            
            # Call your picker directly (no driver needed)
            coordinates = single_element_picker.citrix_mod_locator()
            
            if coordinates:
                coordinates=bound_index_fix.gemini_response(coordinates)
                self.xpath_display.setText(str(coordinates))  # Changed from setPlainText
                
                # Styling to indicate success
                self.xpath_display.setStyleSheet("""
                    QLineEdit {
                        color: #00ff00;
                        background: rgba(255,255,255,0.08);
                        border: 1px solid #28a745;
                        border-radius: 6px;
                        padding: 6px 8px;
                        font-size: 12px;
                    }
                """)
                
                self.confirm_btn.setEnabled(True)
                self.xpath_display.setPlaceholderText("[OK] Element selected! Click Confirm.")
                print(f"[OK] Element selected: {coordinates}")
            else:
                QMessageBox.information(self, "Info", "No element selected.")
                print("No element selected")
            self.show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Element picker failed: {e}")
            print(f"[ERROR] Element picker error: {e}")

    def capture_image_region(self):
        """Capture image region using snipping tool"""
        try:
            # Hide the dialog temporarily
            self.hide()
            QApplication.processEvents()
            
            # Wait a moment for dialog to hide
            time.sleep(0.5)
            
            # Create and show snipping tool
            snipping_tool = SnippingTool()
            snipping_tool.show()
            
            # Wait for snipping tool to complete
            while snipping_tool.isVisible():
                QApplication.processEvents()
            
            # Check if user captured something
            if snipping_tool.captured_region is not None:
                # Create images directory if it doesn't exist
                images_dir = "images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                # Generate filename using desc parameter
                filename = f"{self.desc}.png"
                filepath = os.path.join(images_dir, filename)
                
                # Save the captured image
                snipping_tool.captured_region.save(filepath)
                
                # Update the text field with the image path
                self.xpath_display.setText(filepath)  # Changed from setPlainText
                
                # Style to indicate success
                self.xpath_display.setStyleSheet("""
                    QLineEdit {
                        color: #ffa500;
                        background: rgba(255,255,255,0.08);
                        border: 1px solid #ffa500;
                        border-radius: 6px;
                        padding: 6px 8px;
                        font-size: 12px;
                    }
                """)
                
                self.confirm_btn.setEnabled(True)
                self.xpath_display.setPlaceholderText("[OK] Image captured! Click Confirm.")
                print(f"[OK] Image captured and saved: {filepath}")
                
            else:
                QMessageBox.information(self, "Info", "No region selected.")
                print("No region selected")
                
            # Show the dialog again
            self.show()
            self.raise_()
            self.activateWindow()
            QApplication.processEvents()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Image capture failed: {e}")
            print(f"[ERROR] Image capture error: {e}")
            # Make sure dialog is visible again
            self.show()
            self.raise_()
            self.activateWindow()

    def confirm_xpath(self):
        """Confirm XPath selection and close dialog"""
        # Get current text from the input field
        current_xpath = self.xpath_display.text().strip()  # Fixed: .text() instead of .toPlainText()
        
        if current_xpath:
            # Update extracted_xpath with whatever is in the text field
            self.extracted_xpath = current_xpath
            self.result = True
            print(f"[OK] XPath confirmed: {current_xpath}")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "No XPath entered. Please enter an XPath or select an element first.")
            self.reject()  # Added: Close dialog and cancel (sets result=False)
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

def mod_citrix(desc):
    """
    Show XPath modification dialog and return selected XPath after user clicks Confirm.
    Dialog stays open until user clicks Confirm or Cancel.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dialog = XPathModifyDialog(desc)
    dialog.show()  # Non-modal
    dialog.raise_()
    dialog.activateWindow()

    # Wait until user clicks Confirm or Cancel
    while dialog.isVisible():
        app.processEvents()  # Keep GUI responsive

    # Check what the user did
    if dialog.result:
        # Confirm was clicked
        xpath = dialog.xpath_display.text().strip()  # Fixed: .text() instead of .toPlainText()
        try:
            import ast
            xpath = ast.literal_eval(xpath)
        except (ValueError, SyntaxError):
            # If not valid Python literal (e.g., image path), keep as string
            pass
        except Exception as e:
            print(f"[ERROR] Failed to eval XPath: {e}")
            xpath = ""  # Fallback to empty on error
        print(f"[OK] Returning XPath: {xpath}")
        return xpath
    else:
        # Cancel or window close
        print("[WARN] Dialog cancelled, returning empty string")
        return ""
    