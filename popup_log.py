from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QProgressBar, QPushButton, QApplication
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QMovie, QColor, QIcon, QPixmap
import style_loader
import os
import ctypes
from ctypes import wintypes


class StatusPopup(QWidget):
    """Bottom-right persistent status popup with real-time logs and loading bar."""
    
    # Class variable to track all instances
    _instances = []

    def __init__(self, parent=None):
        super().__init__(None)  # No parent - completely independent window
        # Add this instance to the tracking list
        StatusPopup._instances.append(self)
        
        # Configure as frameless window 
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setFixedSize(380, 220)
        
        # Set window title and icon for taskbar identification
        self.setWindowTitle("AGENT FLOW Status Monitor")
        
        # Set taskbar icon using status_popup.png or status_icon.png
        status_popup_path = os.path.join("Icon", "status_popup.png")
        status_icon_path = os.path.join("Icon", "status_icon.png")
        
        if os.path.exists(status_popup_path):
            self.setWindowIcon(QIcon(status_popup_path))
        elif os.path.exists(status_icon_path):
            self.setWindowIcon(QIcon(status_icon_path))
        else:
            # Fallback to app icon
            app_icon_path = os.path.join("Icon", "app_icon.png")
            if os.path.exists(app_icon_path):
                self.setWindowIcon(QIcon(app_icon_path))

        # Dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        
        # Prevent duplicate logs
        self._last_messages = []
        self._max_messages = 50

        self._build_ui()
        self._position_bottom_right()
        self.show()

    def reset_progress_bar(self):
        """Indeterminate (infinite loading)"""
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setFormat("Processing...")

    def complete_progress_bar(self):
        """Completed"""
        self.loading_bar.setRange(0, 1)
        self.loading_bar.setValue(1)
        self.loading_bar.setFormat("Completed ✅")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = True
            self._mouse_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pressed = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self._mouse_pressed and self._mouse_pos is not None:
            self.move(event.globalPos() - self._mouse_pos)
            event.accept()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        container = QWidget()
        container.setProperty('class', 'StatusPopupContainer')
        style_loader.apply_stylesheet(container)
        inner = QVBoxLayout(container)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("📡 Status")
        title.setObjectName("title")
        header.addWidget(title)

        self.spinner = QLabel()
        self.movie = QMovie("styles/Icon/loader.gif") if QMovie.supportedFormats() else None
        if self.movie:
            self.spinner.setMovie(self.movie)
            self.movie.start()
        header.addWidget(self.spinner)
        header.addStretch()
        
        # Add minimize button (remove close button for frameless design)
        min_btn = QPushButton("–")
        min_btn.setObjectName("minBtn")
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setToolTip("Minimize to taskbar")
        header.addWidget(min_btn)
        
        inner.addLayout(header)

        # Loading progress bar (always loading animation)
        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setRange(0, 0)  # Indeterminate progress (always loading)
        self.loading_bar.setFixedHeight(16)
        self.loading_bar.setFormat("Processing...")
        inner.addWidget(self.loading_bar)

        self.log = QTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Remove scrollbar
        self.log.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Remove horizontal scrollbar
        inner.addWidget(self.log)

        root.addWidget(container)

    def _position_bottom_right(self):
        # Position independently on screen, not relative to any parent window
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        # Position in bottom-right corner with some margin
        self.move(screen.right() - self.width() - 20, screen.bottom() - self.height() - 60)

    def append(self, message: str, level: str = "info"):
        # Prevent duplicate messages
        if message in self._last_messages:
            return
        
        # Add to recent messages list
        self._last_messages.append(message)
        if len(self._last_messages) > self._max_messages:
            self._last_messages.pop(0)
        
        color = {
            "info": "#c4dbf3",
            "success": "#57e063",
            "warning": "#ff9800",
            "error": "#f44336",
        }.get(level, "#c4dbf3")
        
        self.log.append(f'<span style="color:{color};">{message}</span>')
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        
        # Update loading bar based on message content
        self._update_loading_bar(message)

    def show_error_for_task(self, index: int, details: str = ""):
        msg = f"❌ Error occurred at task no. {index}"
        if details:
            msg += f": {details}"
        self.append(msg, level="error")

    def _update_loading_bar(self, message: str):
        """Update loading bar text based on message content (always loading animation)"""
        try:
            if "Starting" in message or "progress" in message.lower():
                self.loading_bar.setFormat("Starting...")
            elif "Validating task" in message:
                # Extract task number and update text
                import re
                match = re.search(r'task (\d+)', message)
                if match:
                    task_num = int(match.group(1))
                    self.loading_bar.setFormat(f"Task {task_num}...")
            elif "completed" in message.lower() or "finished" in message.lower():
                self.loading_bar.setFormat("Completed!")
            elif "error" in message.lower() or "failed" in message.lower():
                self.loading_bar.setFormat("Error occurred")
        except Exception:
            pass

    def set_total_tasks(self, total: int):
        """Set total tasks for progress calculation"""
        self._total_tasks = max(1, int(total))
    
    def closeEvent(self, event):
        """Handle close event and remove from instances list"""
        try:
            if self in StatusPopup._instances:
                StatusPopup._instances.remove(self)
        except Exception:
            pass
        super().closeEvent(event)
    
    # Remove the hideEvent that was interfering with cleanup
    # def hideEvent(self, event):
    #     """Ensure popup stays visible during operations"""
    #     super().hideEvent(event)
    #     # Re-show after a short delay to prevent accidental hiding
    #     QTimer.singleShot(100, self.show)

    @classmethod
    def close_all_popups(cls):
        """Close all status popup instances"""
        print(f"🔄 Closing {len(cls._instances)} status popups...")
        for popup in cls._instances[:]:  # Copy list to avoid modification during iteration
            try:
                if popup and popup.isVisible():
                    print(f"🔄 Closing popup: {popup}")
                    popup.close()
                    popup.deleteLater()
                elif popup:
                    popup.deleteLater()
            except Exception as e:
                print(f"⚠️ Error closing popup: {e}")
        cls._instances.clear()
        print("✅ All status popups closed")


class PopupLogMixin:
    """Mixin to add popup logging helpers to any window."""

    def ensure_popup(self):
        if not hasattr(self, "_status_popup") or self._status_popup is None:
            from PyQt5.QtWidgets import QApplication
            self._status_popup = StatusPopup()  # No parent - independent window
            QApplication.processEvents()
        return self._status_popup

    def popup_info(self, text: str):
        self.ensure_popup().append(text, "info")

    def popup_success(self, text: str):
        self.ensure_popup().append(text, "success")

    def popup_warning(self, text: str):
        self.ensure_popup().append(text, "warning")

    def popup_error(self, text: str):
        self.ensure_popup().append(text, "error")

    def popup_task_error(self, index: int, details: str = ""):
        self.ensure_popup().show_error_for_task(index, details)
