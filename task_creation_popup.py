import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class TaskCreationPopup(QDialog):
    """Custom frameless popup for task creation confirmation"""
    
    # Signals
    start_detail_mode = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(self, task_count=0, parent=None, show_empty_mode=False):
        super().__init__(parent)
        self.task_count = task_count
        self.result = None
        self.drag_position = QPoint()
        self.show_empty_mode = show_empty_mode
        
        self.setupUI()
        self.setModal(True)
        
    def setupUI(self):
        """Setup the frameless popup UI"""
        self.setProperty('class', '')
        # Make dialog frameless and always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Clear any inherited stylesheets
        self.setStyleSheet("")
        
        # Fixed size and absolute position
        self.setFixedSize(620, 320)
         # ✅ Center the popup on the screen
        screen = QDesktopWidget().availableGeometry().center()
        popup_rect = self.frameGeometry()
        popup_rect.moveCenter(screen)
        self.move(popup_rect.topLeft())
        
        # Add dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        
        # Create main container with rounded corners (no border)
        container = QWidget(self)
        container.setGeometry(0, 0, 620, 320)
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            QWidget#popupContainer {
                background-color: #414141 !important;
                border: none !important;
                border-radius: 15px !important;
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
                background: #333333 !important;
                border-radius: 20px 20px 0px 0px !important;
                border: none !important;
            }
        """)

        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)

        # Title label with icon and text
        title_label = QLabel("Step Generation Complete")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff !important;
                font-family: 'Asen Pro' !important;
                font-weight: bold !important;
                font-size: 16px !important;
                background: transparent !important;
                border: none !important;
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
                background: transparent !important;
                border: none !important;
                border-radius: 0px !important;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1) !important;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2) !important;
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
        close_btn.clicked.connect(self.close_popup)
        title_layout.addWidget(close_btn)

        layout.addWidget(title_container)

        # Add spacing between title and content
        layout.addSpacing(30)
        
        # Main message
        if self.task_count==0:
            self.show_empty_mode=True
        if self.show_empty_mode:
            main_message = QLabel("No steps created from the requirement...")
            main_message.setStyleSheet("""
                QLabel {
                    color: #FFFFFF !important;
                    font-family: 'Asen Pro' !important;
                    font-style: normal !important;
                    font-weight: 600 !important;
                    font-size: 20px !important;
                    line-height: 24px !important;
                    letter-spacing: 0.05em !important;
                    text-align: center !important;
                    background: transparent !important;
                    border: none !important;
                    padding: 20px !important;
                }
            """)
            main_message.setAlignment(Qt.AlignCenter)
            main_message.setWordWrap(True)
            layout.addWidget(main_message)
            
            # Sub message for empty mode
            sub_message = QLabel("Please provide Valid Requirement...")
            sub_message.setStyleSheet("""
                QLabel {
                    color: #FFFFFF !important;
                    font-family: 'Asen Pro' !important;
                    font-style: normal !important;
                    font-weight: 400 !important;
                    font-size: 16px !important;
                    line-height: 19px !important;
                    letter-spacing: 0.05em !important;
                    text-align: center !important;
                    background: transparent !important;
                    border: none !important;
                    padding: 10px !important;
                }
            """)
            sub_message.setAlignment(Qt.AlignCenter)
            sub_message.setWordWrap(True)
            layout.addWidget(sub_message)
        else:
            main_message = QLabel(f"{self.task_count} steps created successfully!")
            main_message.setStyleSheet("""
                QLabel {
                    color: #FFFFFF !important;
                    font-family: 'Asen Pro' !important;
                    font-style: normal !important;
                    font-weight: 600 !important;
                    font-size: 20px !important;
                    line-height: 24px !important;
                    letter-spacing: 0.05em !important;
                    text-align: center !important;
                    background: transparent !important;
                    border: none !important;
                    padding: 20px !important;
                }
            """)
            main_message.setAlignment(Qt.AlignCenter)
            main_message.setWordWrap(True)
            layout.addWidget(main_message)
            
            # Sub message
            sub_message = QLabel("Would you like to start detail mode for task validation?")
            sub_message.setStyleSheet("""
                QLabel {
                    color: #FFFFFF !important;
                    font-family: 'Asen Pro' !important;
                    font-style: normal !important;
                    font-weight: 400 !important;
                    font-size: 16px !important;
                    line-height: 19px !important;
                    letter-spacing: 0.05em !important;
                    text-align: center !important;
                    background: transparent !important;
                    border: none !important;
                    padding: 10px !important;
                }
            """)
            sub_message.setAlignment(Qt.AlignCenter)
            sub_message.setWordWrap(True)
            layout.addWidget(sub_message)
        
        # Add spacing before buttons
        layout.addSpacing(30)
        
                # Buttons
                # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        if self.show_empty_mode:
            # For empty mode, show only OK button
            self.ok_btn = QPushButton("OK")
            self.ok_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 10px !important;
                    font-family: 'Asen Pro' !important;
                    font-weight: 600 !important;
                    font-size: 16px !important;
                    letter-spacing: 0.05em !important;
                    padding: 0 20px !important;
                    min-width: 150px !important;
                    max-width: 150px !important;
                    height: 40px !important;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455) !important;
                }
            """)
            self.ok_btn.clicked.connect(self.ok_action)
            
            button_layout.addStretch()
            button_layout.addWidget(self.ok_btn)
            button_layout.addStretch()
        else:
            # Cancel button
            self.cancel_btn = QPushButton("❌ Cancel")
            self.cancel_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 10px !important;
                    font-family: 'Asen Pro' !important;
                    font-weight: 600 !important;
                    font-size: 16px !important;
                    letter-spacing: 0.05em !important;
                    padding: 0 20px !important;  /* Increased padding */
                    min-width: 150px !important;  /* Minimum width to ensure text fits */
                    max-width: 150px !important;  /* Fixed width enforcement */
                    height: 40px !important;      /* Fixed height */
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455) !important;
                }
            """)
            self.cancel_btn.clicked.connect(self.cancel_action)
            
            # Start Detail Mode button
            self.start_btn = QPushButton("✅ Start Detail Mode")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important;
                    color: #FFFFFF !important;
                    border: none !important;
                    border-radius: 10px !important;
                    font-family: 'Asen Pro' !important;
                    font-weight: 600 !important;
                    font-size: 16px !important;
                    letter-spacing: 0.05em !important;
                    padding: 0 25px !important;  /* Increased padding */
                    min-width: 220px !important;  /* Minimum width to ensure text fits */
                    max-width: 220px !important;  /* Fixed width enforcement */
                    height: 40px !important;      /* Fixed height */
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #007799, stop: 1 #004455) !important;
                }
            """)
            self.start_btn.clicked.connect(self.start_detail_action)
            
            button_layout.addStretch()
            button_layout.addWidget(self.cancel_btn)
            button_layout.addWidget(self.start_btn)
            button_layout.addStretch()
        
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
    
    def ok_action(self):
        """Handle OK button click in empty mode - behaves like Cancel"""
        self.result = "ok"
        self.cancelled.emit()
        self.reject()
    
    def start_detail_action(self):
        """Handle Start Detail Mode button click"""
        self.result = "start_detail"
        self.start_detail_mode.emit()
        self.accept()
    
    def cancel_action(self):
        """Handle Cancel button click"""
        self.result = "cancel"
        self.cancelled.emit()
        self.reject()
    
    def close_popup(self):
        """Handle close button click"""
        self.result = "close"
        self.cancelled.emit()
        self.reject()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.cancel_action()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.start_detail_action()
        else:
            super().keyPressEvent(event)

# Test the popup if run directly
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
    
#     # Apply dark theme
#     app.setStyle("Fusion")
#     palette = QPalette()
#     palette.setColor(QPalette.Window, QColor(45, 45, 48))
#     palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
#     app.setPalette(palette)
    
#     popup = TaskCreationPopup(task_count=25)
#     result = popup.exec_()
    
#     print(f"Popup result: {popup.result}")
    
#     sys.exit()