"""
Notification popup system for ABA application.
Provides attractive frameless popups with minimize and close options.
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class StatusPopup(QWidget):
    """Modern frameless notification popup with minimize/close controls"""
    
    # Signal emitted when popup is closed
    popup_closed = pyqtSignal()
    
    def __init__(self, title, message, duration=5000, parent=None, callback=None):
        super().__init__(parent)
        self.duration = duration
        self.callback = callback
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 120)
        
        # Position popup at center of screen
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.setup_ui(title, message)
        self.setup_animations()
        
        # Auto-close timer
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.fade_out_and_close)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(self.duration)
        
    def setup_ui(self, title, message):
        """Setup the modern UI with gradient background and controls"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main container with rounded corners and gradient
        container = QFrame()
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            QFrame#popupContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E3440, stop:0.5 #3B4252, stop:1 #434C5E);
                border: 2px solid #5E81AC;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(8)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ECEFF4;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(25, 25)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #EBCB8B;
                border: none;
                border-radius: 12px;
                color: #2E3440;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
        """)
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                border: none;
                border-radius: 12px;
                color: #ECEFF4;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(self.minimize_btn)
        header_layout.addWidget(self.close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #D8DEE9;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.4;
            }
        """)
        container_layout.addWidget(message_label)
        
        # Progress bar for timing
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.duration)
        self.progress_bar.setValue(self.duration)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #4C566A;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #5E81AC;
                border-radius: 2px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(container)
        
        # Progress timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(50)  # Update every 50ms
        
    def setup_animations(self):
        """Setup fade in/out animations"""
        self.fade_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_in_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        
        self.fade_out_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.finished.connect(self.close)
        
    def showEvent(self, event):
        """Start fade in animation when shown"""
        super().showEvent(event)
        self.fade_in_animation.start()
        
    def update_progress(self):
        """Update progress bar"""
        current_value = self.progress_bar.value()
        if current_value > 0:
            self.progress_bar.setValue(current_value - 50)
        else:
            self.progress_timer.stop()
            
    def fade_out_and_close(self):
        """Start fade out animation and close"""
        self.progress_timer.stop()
        self.fade_out_animation.start()
        
    def closeEvent(self, event):
        """Handle close event and emit signal"""
        self.popup_closed.emit()
        if self.callback:
            self.callback()
        super().closeEvent(event)
        
    def mousePressEvent(self, event):
        """Allow dragging the popup"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """Handle popup dragging"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()


def show_task_generated_notification(task_count, parent=None, callback=None):
    """Show notification when tasks are generated"""
    title = "✅ Steps Generated"
    message = f"{task_count} steps have been successfully generated and are ready for processing."
    
    popup = StatusPopup(title, message, duration=5000, parent=parent, callback=callback)
    popup.show()
    return popup


def show_detail_mode_started_notification(parent=None):
    """Show notification when detail mode validation starts"""
    title = " Detail Mode Started"
    message = "Task validation has begun. Please wait while we verify all generated tasks."
    
    popup = StatusPopup(title, message, duration=3000, parent=parent)
    popup.show()
    return popup


def show_detail_mode_completed_notification(parent=None):
    """Show notification when detail mode validation completes"""
    title = "✅ Detail Mode Completed"
    message = "Task validation completed successfully. All tasks are now ready for execution."
    
    popup = DetailModeCompletedPopup(title, message, parent=parent)
    popup.show()
    return popup


class DetailModeCompletedPopup(QWidget):
    """Custom popup for detail mode completion without progress bar"""
    
    # Signal emitted when popup is closed
    popup_closed = pyqtSignal()
    
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 100)
        
        # Position popup at center of screen
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self.setup_ui(title, message)
        self.setup_animations()
        
        # Auto-close timer (3 seconds)
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.fade_out_and_close)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(3000)
        
    def setup_ui(self, title, message):
        """Setup the modern UI without progress bar"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main container with rounded corners and gradient
        container = QFrame()
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            QFrame#popupContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E3440, stop:0.5 #3B4252, stop:1 #434C5E);
                border: 2px solid #4CAF50;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(8)
        
        # Header with title and controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ECEFF4;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Close button only
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                border: none;
                border-radius: 12px;
                color: #ECEFF4;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
        """)
        self.close_btn.clicked.connect(self.close_and_cleanup)
        
        header_layout.addWidget(self.close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #D8DEE9;
                font-size: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.4;
            }
        """)
        container_layout.addWidget(message_label)
        
        # No progress bar for this popup
        
        main_layout.addWidget(container)
        
    def setup_animations(self):
        """Setup fade in/out animations"""
        self.fade_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_in_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        
        self.fade_out_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.finished.connect(self.close)
        
    def showEvent(self, event):
        """Start fade in animation when shown"""
        super().showEvent(event)
        self.fade_in_animation.start()
            
    def fade_out_and_close(self):
        """Start fade out animation and close"""
        self.fade_out_animation.start()
        
    def close_and_cleanup(self):
        """Close this popup and the main detail validation popup"""
        # Close the main detail validation popup if it exists
        if self.parent_window and hasattr(self.parent_window, 'unified_popup'):
            try:
                if self.parent_window.unified_popup and not self.parent_window.unified_popup.isHidden():
                    self.parent_window.unified_popup.close()
                    print("🔄 Closed main detail validation popup")
            except Exception as e:
                print(f"Error closing main detail popup: {e}")
        
        self.close()
        
    def closeEvent(self, event):
        """Handle close event and emit signal"""
        self.popup_closed.emit()
        super().closeEvent(event)


# Global list to track active popups
active_popups = []

def cleanup_popups():
    """Clean up all active popups"""
    global active_popups
    for popup in active_popups[:]:  # Create a copy to iterate
        try:
            if popup and not popup.isHidden():
                popup.close()
        except:
            pass
    active_popups.clear()


def add_popup_to_tracker(popup):
    """Add popup to global tracker"""
    global active_popups
    active_popups.append(popup)
    # Clean up closed popups
    active_popups = [p for p in active_popups if p and not p.isHidden()]


# Test function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Test popups
    popup1 = show_task_generated_notification(5)
    
    QTimer.singleShot(2000, lambda: show_detail_mode_started_notification())
    QTimer.singleShot(4000, lambda: show_detail_mode_completed_notification())
    
    sys.exit(app.exec_())
