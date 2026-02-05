from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtSvg import QSvgRenderer


class ConfirmationPopup(QDialog):
    def __init__(self, message="Is this pagination table?", parent=None):
        super().__init__(parent)
        self.result = None
        self.drag_pos = QPoint()
        
        self.init_ui(message)
        
    def init_ui(self, message):
        # Frameless window with stay on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main container with cyan border and curved edges
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 2px solid #00ffff;
                border-radius: 15px;
            }
        """)
        
        # Layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # Message label
        self.label = QLabel(message)
        self.label.setStyleSheet("color: white; border: none; background: transparent;")
        self.label.setFont(QFont("Arial", 11))
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        # Yes button
        self.yes_btn = QPushButton()
        self.yes_btn.setFixedSize(100, 36)
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa00;
                color: white;
                border: 1px solid #00ff00;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00cc00;
                border: 1px solid #00ff88;
            }
            QPushButton:pressed {
                background-color: #008800;
            }
        """)
        self.set_button_icon(self.yes_btn, self.get_yes_svg(), "YES")
        self.yes_btn.clicked.connect(self.on_yes)
        
        # No button
        self.no_btn = QPushButton()
        self.no_btn.setFixedSize(100, 36)
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.setStyleSheet("""
            QPushButton {
                background-color: #aa0000;
                color: white;
                border: 1px solid #ff0000;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #cc0000;
                border: 1px solid #ff8888;
            }
            QPushButton:pressed {
                background-color: #880000;
            }
        """)
        self.set_button_icon(self.no_btn, self.get_no_svg(), "NO")
        self.no_btn.clicked.connect(self.on_no)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.yes_btn)
        btn_layout.addWidget(self.no_btn)
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
        # Set main layout
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_widget)
        
        # Set size
        self.setFixedSize(400, 150)
        
    def get_yes_svg(self):
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f5f5f5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-icon lucide-check"><path d="M20 6 9 17l-5-5"/></svg>'''
    
    def get_no_svg(self):
        return '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x-icon lucide-x"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'''
    
    def set_button_icon(self, button, svg_data, text):
        renderer = QSvgRenderer(svg_data.encode())
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        from PyQt5.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        icon = QIcon(pixmap)
        button.setIcon(icon)
        button.setIconSize(pixmap.size())
        button.setText(f"  {text}")
        
    def on_yes(self):
        self.result = True
        self.accept()
        
    def on_no(self):
        self.result = False
        self.accept()
        
    # Make window draggable
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()


def show_confirmation_popup(message="Is this pagination table?", parent=None):
    """
    Shows a confirmation popup and waits for user response.
    Creates a temporary QApplication if one doesn't exist.
    
    Args:
        message (str): The message to display in the popup
        parent (QWidget): Optional parent widget
        
    Returns:
        bool: True if user clicked Yes, False if user clicked No
    """
    from PyQt5.QtWidgets import QApplication
    import sys
    
    # Check if QApplication exists, create if it doesn't
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    else:
        created_app = False
    
    popup = ConfirmationPopup(message, parent)
    popup.exec_()
    
    result = popup.result if popup.result is not None else False
    
    # Clean up if we created the application
    if created_app:
        app.quit()
    
    return result


# Example usage (for testing purposes)
# if __name__ == "__main__":
#     from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
#     import sys
    
#     app = QApplication(sys.argv)
    
#     # Example main window
#     main_window = QMainWindow()
#     main_window.setGeometry(100, 100, 600, 400)
#     main_window.setWindowTitle("Main Application")
    
#     test_btn = QPushButton("Show Confirmation Popup", main_window)
#     test_btn.setGeometry(200, 150, 200, 50)
    
#     def on_test_click():
#         result = show_confirmation_popup("Is this pagination table?", main_window)
#         print(f"User clicked: {'YES' if result else 'NO'}")
    
#     test_btn.clicked.connect(on_test_click)
    
#     main_window.show()
#     sys.exit(app.exec_())