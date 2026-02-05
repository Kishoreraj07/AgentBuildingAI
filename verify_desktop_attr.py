import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from desktop_element_picker import main_desktop_element_picker  #desktop element picker
import json

class DesktopAttributeModifyDialog(QDialog):
    """Standalone desktop attribute modification dialog with desktop element picker"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app  # pywinauto Application instance
        self.extracted_attr = {}
        self.result = False

        self.setupUI()
        self.raise_()
        self.activateWindow()

    def setupUI(self):
        """Setup the attribute modification dialog UI"""
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 620) // 2,
            (screen.height() - 249) // 2
        )

        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None

        # Create main container with rounded corners
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
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
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

        title_label = QLabel("Attribute Modification")
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
        title_layout.addStretch()

        # Close button
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

        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = int(24 * 0.25)
            start_x = margin
            start_y = margin
            end_x = 24 - margin
            end_y = 24 - margin
            painter.drawLine(start_x, start_y, end_x, end_y)
            painter.drawLine(end_x, start_y, start_x, end_y)

        close_btn.paintEvent = paintEvent
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(20)

        # Instruction label
        instruction_label = QLabel("Click the Element Picker button to select a desktop element, then confirm to get its attributes:")
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

        # Desktop element picker button
        picker_layout = QHBoxLayout()
        picker_layout.addStretch()
        self.desktop_picker_btn = QPushButton("Element Picker")
        self.desktop_picker_btn.setFixedSize(150, 45)
        self.desktop_picker_btn.setStyleSheet("""
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
        self.desktop_picker_btn.clicked.connect(self.pick_desktop_element)
        picker_layout.addWidget(self.desktop_picker_btn)
        picker_layout.addStretch()
        layout.addLayout(picker_layout)

        # Attribute display area
        attr_label = QLabel("Selected Attributes:")
        attr_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: 'Asen Pro';
                font-weight: bold;
                font-size: 12px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(attr_label)

        self.attr_display = QTextEdit()
        self.attr_display.setPlaceholderText("No attributes selected yet. Click the ELEMENT PICKER button to select an element.")
        self.attr_display.setFixedHeight(80)
        self.attr_display.setReadOnly(False)
        self.attr_display.setStyleSheet("""
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
        self.attr_display.textChanged.connect(self.on_attr_text_changed)
        layout.addWidget(self.attr_display)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

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

        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.setFixedSize(100, 45)
        self.confirm_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F);
                color: #FFFFFF;
                opacity: 0.6;
            }
        """)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.confirm_attr)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        layout.addLayout(button_layout)

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


    def pick_desktop_element(self):
        """Pick desktop element using desktop_element_picker"""
        try:
            if not self.app:
                QMessageBox.warning(self, "Error", "No application available.")
                return

            self.showMinimized()
            element = main_desktop_element_picker(self.app)
            self.showNormal()
            self.raise_()
            self.activateWindow()

            if element:
                attr_text = "No attributes found"
                self.extracted_attr = {}

                # --- Case 1: real pywinauto element (live object) ---
                if hasattr(element, "element_info"):
                    info = element.element_info
                    attr_text = (
                        f"Title: {info.name}\n"
                        f"Control Type: {info.control_type}\n"
                        f"AutomationId: {info.auto_id}\n"
                        f"ClassName: {info.class_name}\n"
                        f"Rectangle: {info.rectangle}\n"
                        f"ClickPoint: {info.click_point}\n"
                    )
                    self.extracted_attr = {
                        "title": info.name,
                        "auto_id": info.auto_id,
                        "control_type": info.control_type,
                        "class_name": info.class_name,
                        "rectangle": info.rectangle,
                        "click_point": info.click_point,
                        "ancestors": getattr(info, "ancestors", []),
                    }

                # --- Case 2: dictionary (typical JSON-like picker output) ---
                elif isinstance(element, dict):
                    ancestors = element.get("ancestors", [])
                    attr_text = (
                        f"Title: {element.get('name','')}\n"
                        f"Control Type: {element.get('control_type','')}\n"
                        f"AutomationId: {element.get('auto_id','')}\n"
                        f"ClassName: {element.get('class_name','')}\n"
                        f"Rectangle: {element.get('rectangle','')}\n"
                        f"ClickPoint: {element.get('click_point','')}\n"
                    )
                    # Add ancestors list for display
                    if ancestors:
                        attr_text += "Ancestors:\n"
                        for i, anc in enumerate(ancestors, 1):
                            attr_text += (
                                f"  {i}. {anc.get('name', '')} "
                                f"({anc.get('control_type', '')}, "
                                f"{anc.get('class_name', '')})\n"
                            )

                    self.extracted_attr = {
                        "title": element.get("name", ""),
                        "auto_id": element.get("auto_id", ""),
                        "control_type": element.get("control_type", ""),
                        "class_name": element.get("class_name", ""),
                        "rectangle": element.get("rectangle", ""),
                        "click_point": element.get("click_point", ""),
                        "ancestors": ancestors,
                    }

                # --- Case 3: JSON string ---
                elif isinstance(element, str):
                    try:
                        parsed = json.loads(element)
                        ancestors = parsed.get("ancestors", [])
                        attr_text = (
                            f"Title: {parsed.get('name','')}\n"
                            f"Control Type: {parsed.get('control_type','')}\n"
                            f"AutomationId: {parsed.get('auto_id','')}\n"
                            f"ClassName: {parsed.get('class_name','')}\n"
                            f"Rectangle: {parsed.get('rectangle','')}\n"
                            f"ClickPoint: {parsed.get('click_point','')}\n"
                        )
                        if ancestors:
                            attr_text += "Ancestors:\n"
                            for i, anc in enumerate(ancestors, 1):
                                attr_text += (
                                    f"  {i}. {anc.get('name', '')} "
                                    f"({anc.get('control_type', '')}, "
                                    f"{anc.get('class_name', '')})\n"
                                )

                        self.extracted_attr = {
                            "title": parsed.get("name", ""),
                            "auto_id": parsed.get("auto_id", ""),
                            "control_type": parsed.get("control_type", ""),
                            "class_name": parsed.get("class_name", ""),
                            "rectangle": parsed.get("rectangle", ""),
                            "click_point": parsed.get("click_point", ""),
                            "ancestors": ancestors,
                        }
                    except json.JSONDecodeError:
                        print("Failed to decode element JSON string")

                # --- Update UI ---
                self.attr_display.setPlainText(attr_text)
                self.attr_display.setStyleSheet("""
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
                self.confirm_btn.setEnabled(True)
                print(f"Desktop element selected: {attr_text}")

            else:
                QMessageBox.information(self, "Info", "No element was selected.")
                print("No element was selected")

        except Exception as e:
            error_msg = f"Failed to pick element: {str(e)}"
            QMessageBox.warning(self, "Error", error_msg)
            print(f"Element picker error: {e}")

    def on_attr_text_changed(self):
        """Handle text changes in attribute display"""
        try:
            current_text = self.attr_display.toPlainText().strip()
            if current_text:
                self.confirm_btn.setEnabled(True)
                self.attr_display.setStyleSheet("""
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
            else:
                self.confirm_btn.setEnabled(False)
                self.attr_display.setStyleSheet("""
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
        except Exception as e:
            print(f"Error in on_attr_text_changed: {e}")

    def confirm_attr(self):
        """Confirm attribute selection and close dialog"""
        current_attr = self.attr_display.toPlainText().strip()
        if current_attr:
            self.result = True
            print(f"Attributes confirmed: {self.extracted_attr}")
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "No attributes entered. Please select an element first.")

    def reject(self):
        """Handle dialog rejection"""
        self.result = False
        self.extracted_attr = {}
        print("Attribute selection cancelled - reject() called")
        super().reject()

    def closeEvent(self, event):
        """Handle close event"""
        print("Dialog closeEvent triggered")
        self.result = False
        self.extracted_attr = {}
        super().closeEvent(event)

def mod_attr(app):
    """
    Show attribute modification dialog and return selected attributes

    Args:
        app: pywinauto Application instance

    Returns:
        dict: Selected attributes if confirmed, empty dict if cancelled
    """
    import threading
    current_thread = threading.current_thread()

    if current_thread.name == 'MainThread':
        app_qt = QApplication.instance()
        if app_qt is None:
            app_qt = QApplication(sys.argv)

        dialog = DesktopAttributeModifyDialog(app)
        result = dialog.exec_()

        if result == QDialog.Accepted and dialog.result:
            return dialog.extracted_attr
        return {}
    else:
        print(f"mod_attr called from worker thread: {current_thread.name}")
        print("Using signal-based communication with main thread")
        try:
            import main_process
            execute_worker = main_process._current_execute_worker

            if execute_worker and hasattr(execute_worker, 'attr_modification_requested'):
                execute_worker.attr_modification_requested.emit(app)
                event_triggered = execute_worker.attr_modification_event.wait(timeout=60)

                if event_triggered:
                    result = execute_worker.attr_modification_result
                    execute_worker.attr_modification_event.clear()
                    return result
                else:
                    print("Timeout waiting for response from main thread")
                    return {}
            else:
                print("Execute worker not found or doesn't have attr_modification_requested signal")
                return {}
        except Exception as e:
            print(f"Error in signal-based attribute modification: {e}")
            return {}
