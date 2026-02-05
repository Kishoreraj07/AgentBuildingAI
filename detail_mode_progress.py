import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QProgressBar, QApplication
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtGui import QIcon, QTextCursor
import style_loader


class DetailModeProgressDialog(QDialog):
    def __init__(self, parent=None):
        # CRITICAL FIX: Initialize with NO parent and break ALL connections to main app
        super().__init__(None)
        
        # Store parent reference but NEVER use it for window hierarchy
        self.parent_ref = parent
        self._is_minimized = False

        # Window setup - Make it completely independent with HIGHEST priority
        self.setWindowTitle("Validation Logs")
        
        # FIXED: Maximum independence window flags - higher priority than Detail Mode
        self.setWindowFlags(
            Qt.Window |  # Top-level independent window
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint  # CRITICAL: Bypass window manager conflicts
        )
        
        # CRITICAL: Set attributes for complete independence
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_QuitOnClose, False)  # Don't quit app when closed
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDialog, False)  # Don't treat as dialog
        self.setAttribute(Qt.WA_GroupLeader, True)  # Make it a group leader
        
        # Make it completely non-modal and independent
        self.setModal(False)
        self.setFixedSize(420, 520)

        # Internal state
        self.total_tasks = 0
        self.completed_tasks = 0

        # Build UI
        self._build_ui()

        # Dragging support
        self._mouse_pressed = False
        self._mouse_pos = None
        
        # Timer for minimize state checking
        self._minimize_timer = QTimer()
        self._minimize_timer.timeout.connect(self._check_minimize_state)

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
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("📑 Validation Logs")
        title.setObjectName("titleLabel")
        title.setProperty('class', 'DetailModeProgressTitle')
        style_loader.apply_stylesheet(title)
        title_row.addWidget(title)

        # Count bubble 0/N
        self.count_label = QLabel("0/0")
        self.count_label.setObjectName("countBubble")
        self.count_label.setProperty('class', 'CountBubble')
        style_loader.apply_stylesheet(self.count_label)
        title_row.addWidget(self.count_label)

        title_row.addStretch()

        # FIXED: Multiple minimize approaches
        min_btn = QPushButton("–")
        min_btn.setFixedWidth(28)
        min_btn.setObjectName("minBtn")
        min_btn.clicked.connect(self._force_minimize)
        title_row.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedWidth(28)
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self._force_close)
        title_row.addWidget(close_btn)

        root.addLayout(title_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setProperty('class', 'DetailModeProgressBar')
        style_loader.apply_stylesheet(self.progress_bar)
        root.addWidget(self.progress_bar)

        # Logs area
        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setObjectName("logsDisplay")
        self.logs_display.setProperty('class', 'DetailModeLogsDisplay')
        style_loader.apply_stylesheet(self.logs_display)
        root.addWidget(self.logs_display, 1)

    def _force_minimize(self):
        """Force minimize with added isolation checks"""
        try:
            print("🔽 Forcing minimize of Validation Logs dialog...")
            
            # Ensure no parent before minimizing
            self.setParent(None)
            
            # Approach 1: Immediate window state change
            self.setWindowState(Qt.WindowMinimized)
            
            # Approach 2: Force through QWindow with state check
            if hasattr(self, 'windowHandle') and self.windowHandle():
                self.windowHandle().setWindowState(Qt.WindowMinimized)
            
            # New: Verify minimize state after a short delay
            QTimer.singleShot(100, self._verify_minimize_state)
            
        except Exception as e:
            print(f"Error in force minimize: {e}")
            self._emergency_minimize()

    def _verify_minimize_state(self):
        """Check if minimize succeeded and enforce isolation"""
        if self.windowState() != Qt.WindowMinimized:
            print("Minimize verification failed - retrying...")
            self.lower()
            self.setWindowState(Qt.WindowMinimized)
        else:
            print("Minimize verified as independent.")
            # Ensure no accidental raise or grouping
            self.setParent(None)

    def _force_close(self):
        """Force close the dialog completely independent of Detail Mode"""
        try:
            print("❌ Force closing Validation Logs dialog...")
            
            # Disconnect from any potential parent relationships
            self.setParent(None)
            
            # Force immediate close
            self.close()
            self.deleteLater()
            
        except Exception as e:
            print(f"Error in force close: {e}")
            # Emergency close
            self.hide()
            self.deleteLater()

    def _check_minimize_state(self):
        """Check if window is properly minimized"""
        if self.windowState() == Qt.WindowMinimized:
            self._minimize_timer.stop()

    # Public API (unchanged)
    def set_total_tasks(self, total: int) -> None:
        self.total_tasks = max(0, int(total))
        self.completed_tasks = 0
        self._update_progress()

    def set_progress(self, completed: int) -> None:
        self.completed_tasks = max(0, min(int(completed), self.total_tasks))
        self._update_progress()

    def add_log(self, message: str, log_type: str = "info") -> None:
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        color_map = {
            "info": "#c4dbf3",
            "success": "#57e063",
            "warning": "#ff9800",
            "error": "#f44336",
        }
        color = color_map.get(log_type, "#c4dbf3")
        html = f'<span style="color:{color};">[{timestamp}] {message}</span>'
        self.logs_display.append(html)
        cursor = self.logs_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.logs_display.setTextCursor(cursor)

    def _update_progress(self) -> None:
        total = max(1, self.total_tasks)
        completed = max(0, min(self.completed_tasks, total))
        percent = int((completed / total) * 100)
        self.progress_bar.setValue(percent)
        self.count_label.setText(f"{completed}/{self.total_tasks}")

    # CRITICAL: Override all window events to maintain complete independence
    def showEvent(self, event):
        """Show event with complete independence from Detail Mode"""
        super().showEvent(event)
        self._is_minimized = False
        
        # Force window to be completely independent
        self.setParent(None)
        self.raise_()
        
        print("📑 Validation Logs dialog shown with full independence")

    def closeEvent(self, event):
        """Independent close event - works regardless of Detail Mode state"""
        print("📑 Validation Logs dialog closing independently")
        
        # Ensure complete independence during close
        self.setParent(None)
        event.accept()

    def changeEvent(self, event):
        """Handle window state changes - force independence"""
        if event.type() == event.WindowStateChange:
            if self.windowState() == Qt.WindowMinimized:
                print("📑 Validation Logs dialog minimized successfully (independent)")
                self._is_minimized = True
            elif self.windowState() == Qt.WindowNoState:
                print("📑 Validation Logs dialog restored (independent)")
                self._is_minimized = False
                # Ensure independence after restore
                self.setParent(None)
                self.raise_()
        super().changeEvent(event)

    def event(self, event):
        """Override event handler to force independence from Detail Mode interference"""
        # Block any events that might create dependencies
        if event.type() in [event.WindowActivate, event.WindowDeactivate]:
            # Handle these independently
            return super().event(event)
        
        # For all other events, ensure we remain independent
        return super().event(event)

    def _create_restore_timer(self):
        """Create a way to restore the hidden window"""
        print("Window minimized/hidden. Click on taskbar or wait 10 seconds for auto-restore.")
        QTimer.singleShot(10000, self._auto_restore)  # Shorter auto-restore

    def _auto_restore(self):
        """Auto-restore the window"""
        if self._is_minimized and not self.isVisible():
            self.show()
            self.setWindowState(Qt.WindowNoState)
            self.setParent(None)  # Ensure independence
            self.raise_()
            self.activateWindow()
            self._is_minimized = False
            print("🔼 Validation Logs dialog auto-restored")

    # Helper method to restore window if hidden
    def restore_window(self):
        """Public method to restore window if hidden/minimized"""
        if self._is_minimized or not self.isVisible():
            self.show()
            self.setWindowState(Qt.WindowNoState)
            self.raise_()
            self.activateWindow()
            self._is_minimized = False
            return True
        return False