from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame, QGroupBox, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QRectF
from PyQt5.QtGui import QMovie, QColor, QLinearGradient
import os
import sys
from PyQt5.QtGui import QPixmap


def resource_path(relative_path):
    # When run from PyInstaller .exe, _MEIPASS is temp path to bundled files
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DroidAgentProcessingWidget(QGroupBox):
    """Dynamic status widget with multiple states and animations"""
    processing_stopped = pyqtSignal()
    
    # Status states
    STATE_OFF = "off"
    STATE_TASK_GENERATING = "task_generating"  # New: When Enter & Process or Upload & Process clicked
    STATE_READY_TO_PROCESS = "ready_to_process"  # New: After task generation completed (if detail mode skipped)
    STATE_PROCESSING = "processing"  # Renamed to "Pre Processing"
    STATE_READY_FOR_EXECUTION = "ready_for_execution"  # New: After Start Processing completed
    STATE_DETAIL_MODE = "detail_mode"
    STATE_OUTPUTTING = "outputting"
    STATE_PROCESS_PENDING = "process_pending"
    STATE_MODIFYING_CODE = "modifying_code"
    STATE_PROCESS_EXECUTING = "process_executing"  # New: When Execute Code button is clicked
    STATE_WAITING = "waiting"  # New: After code execution completed
    STATE_SYNCING_CHANGES = "syncing_changes"  # New: When Sync Changes button is clicked
    
    def __init__(self, scale_factor=1.0):
        super().__init__()
        self.scale_factor = scale_factor
        self.current_state = self.STATE_OFF
        self.detail_sts_called=False
        self.movies = {}
        self.setup_ui()
        self.load_assets()
        # Initialize with OFF state - ensure assets are loaded first
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.set_state(self.STATE_OFF))
        
    def setup_ui(self):
        """Setup UI to match the new design exactly"""
        self.setFixedSize(int(455 * self.scale_factor), int(356 * self.scale_factor))  # Match CSS width/height
        
        # Dark theme styling for the main box
        self.setStyleSheet(f"""
            QGroupBox {{
                background-color: #000000;
                border-radius: {int(20 * self.scale_factor)}px;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title section (Nav bar)
        title_frame = QFrame()
        title_frame.setFixedHeight(int(60 * self.scale_factor))  # Match CSS height
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #000000;
                border-top-left-radius: {int(20 * self.scale_factor)}px;
                border-top-right-radius: {int(20 * self.scale_factor)}px;
            }}
        """)
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(
            int(15 * self.scale_factor), 
            int(10 * self.scale_factor), 
            int(15 * self.scale_factor), 
            int(10 * self.scale_factor)
        )
        
        # "DROID AGENT" title
        self.title_label = QLabel("DROID AGENT")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-family: Arial, sans-serif;
                font-size: {int(16 * self.scale_factor)}px;
                font-weight: bold;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: transparent;")
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # GIF and status label
        gif_status_layout = QHBoxLayout()
        gif_status_layout.setAlignment(Qt.AlignVCenter)
        gif_status_layout.setSpacing(int(20 * self.scale_factor))
        
        # GIF label (Droidal-eye or Progress spinner)
        self.gif_label = QLabel()
        self.gif_label.setFixedSize(int(166 * self.scale_factor), int(166 * self.scale_factor))  # Match CSS
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent; border: none;")
        self.gif_label.setScaledContents(True)  # Enable automatic scaling
        
        # Status label (WRITING CODE...)
        self.status_label = QLabel("WRITING CODE...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                font-family: 'Arial';  # Approximate 'Asen Pro'
                font-weight: 600;
                font-size: {int(14 * self.scale_factor)}px;
                letter-spacing: {int(0.05 * self.scale_factor)}em;
                background: transparent;
            }}
        """)
        
        gif_status_layout.addWidget(self.gif_label)
        gif_status_layout.addStretch()
        gif_status_layout.addWidget(self.status_label)
        
        # Close button (Rectangle 17 and Frame)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(int(36 * self.scale_factor), int(36 * self.scale_factor))  # Match CSS
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #474747;
                border: none;
                color: #FFFFFF;
                font-size: {int(16 * self.scale_factor)}px;
                font-weight: bold;
                border-radius: {int(10 * self.scale_factor)}px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #5a5a5a;
            }}
            QPushButton:pressed {{
                background-color: #6e6e6e;
            }}
        """)
        self.close_btn.clicked.connect(self.stop_processing)
        
        # Full width progress bar (separate from other elements)
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(int(8 * self.scale_factor))  # Small gap between bar & button

        # Ultra-thin progress bar with custom sliding animation
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # Use determinate mode for custom animation
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)  # Ultra thin like in reference image
        self.progress_bar.setMaximumHeight(2)
        self.progress_bar.setMinimumHeight(2)
        self.progress_bar.setFixedWidth(int(320 * self.scale_factor))

        # self.progress_bar.setStyleSheet(f"""
        # QProgressBar {{
        #     border: none;
        #     border-radius: 0px;
        #     background-color: rgba(0, 0, 0, 0.8);
        #     height: 12px;
        #     min-height: 12px;
        #     max-height: 12px;
        # }}
        # QProgressBar::chunk {{
        #     border-radius: 0px;
        #     background-color: #00BAF1;
        #     height: 12px;
        #     max-height: 12px;
        #     margin: 0px;
        #     width: 40px;
        # }}
        # """)
        self.progress_bar.setStyleSheet("""
    QProgressBar {
        border: none;
        border-radius: 6px;  /* Rounded edges */
        background-color: rgba(0, 0, 0, 0.8);
        height: 12px;
        min-height: 12px;
        max-height: 12px;
    }
    QProgressBar::chunk {
        border-radius: 6px;  /* Match with parent radius */
        background: qlineargradient(
            spread:pad, x1:0, y1:0, x2:1, y2:0,
            stop:0 #004361,
            stop:0.39 #00BAF1,
            stop:0.55 #5ECBF4
        );
        margin: 0px;
        box-shadow: 0px 0px 6px #57C8E8; /* Glow effect */
    }
""")

        shadow = QGraphicsDropShadowEffect()
        shadow.setColor(QColor("#57C8E8"))
        shadow.setBlurRadius(4 * self.scale_factor)
        shadow.setOffset(0, 0)
        self.progress_bar.setGraphicsEffect(shadow)

        # Add bar + button side by side
        progress_layout.addWidget(self.progress_bar, 1)   # Expands
        progress_layout.addWidget(self.close_btn, 0)     # Fixed size

        # Add to content layout
        content_layout.addLayout(gif_status_layout)
        content_layout.addLayout(progress_layout)
        content_layout.addStretch()
        
        # Add to main layout
        main_layout.addWidget(title_frame)
        main_layout.addWidget(content_frame, 1)
        
        # Start progress animation but don't start timer yet (OFF state)
        self.setup_progress_animation()

    def load_assets(self):
        """Load all GIFs and images for different states"""
        assets = {
            self.STATE_OFF: "styles\\Icon\\Off.png",
            self.STATE_TASK_GENERATING: "styles\\gif\\Progress spinner.gif",  # Task generation progress
            self.STATE_READY_TO_PROCESS: "styles\\Icon\\process_pending.png",  # Ready to process
            self.STATE_PROCESSING: "styles\\gif\\Progress spinner.gif",  # Pre Processing (same spinner)
            self.STATE_READY_FOR_EXECUTION: "styles\\Icon\\offline-eye.png",  # Ready for execution
            self.STATE_DETAIL_MODE: "styles\\Icon\\DetailMode_Sts.png",
            self.STATE_OUTPUTTING: "styles\\gif\\Colour-eye_1.gif",
            self.STATE_PROCESS_PENDING: "styles\\Icon\\process_pending.png",
            self.STATE_MODIFYING_CODE: "styles\\gif\\Colour-eye_1.gif",
            self.STATE_PROCESS_EXECUTING: "styles\\gif\\Colour-eye_1.gif",  # Process Executing with Colour-eye_1.gif
            self.STATE_WAITING: "styles\\Icon\\offline-eye.png",  # Waiting with process_pending.png
            self.STATE_SYNCING_CHANGES: "styles\\gif\\Progress spinner.gif"  # Syncing Changes with Progress spinner.gif
        }
        
        gif_size = int(166 * self.scale_factor)
        
        for state, asset_path in assets.items():
            full_path = resource_path(asset_path)
            print(f"Loading asset for {state}: {asset_path} -> {full_path}")
            print(f"File exists: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                try:
                    if asset_path.endswith('.gif'):
                        # Load as animated GIF
                        movie = QMovie(full_path)
                        print(f"GIF movie valid: {movie.isValid()}")
                        if movie.isValid():
                            movie.setScaledSize(QSize(gif_size, gif_size))
                            self.movies[state] = movie
                            print(f"✅ Successfully loaded GIF for {state}")
                        else:
                            print(f"❌ Invalid GIF movie for {state}")
                            self.movies[state] = None
                    else:
                        # Load as static image
                        pixmap = QPixmap(full_path)
                        print(f"Pixmap null: {pixmap.isNull()}, size: {pixmap.size()}")
                        if not pixmap.isNull():
                            # Don't scale here - let the label handle scaling
                            self.movies[state] = pixmap
                            print(f"✅ Successfully loaded PNG for {state}, original size: {pixmap.size()}")
                        else:
                            print(f"❌ Null pixmap for {state}")
                            self.movies[state] = None
                except Exception as e:
                    print(f"❌ Error loading asset {asset_path}: {e}")
                    self.movies[state] = None
            else:
                print(f"Asset not found: {full_path}")
                self.movies[state] = None
        
    def set_state(self, state):
        """Set the widget to a specific state with appropriate visual and message"""
        print(f"🔄 Changing state from {self.current_state} to {state}")
        self.current_state = state
        
        # Stop any currently playing animations
        current_movie = self.gif_label.movie()
        if current_movie:
            current_movie.stop()
        
        # State-specific messages
        messages = {
            self.STATE_OFF: "OFF",
            self.STATE_TASK_GENERATING: "Generating Steps",  # New message for task generation
            self.STATE_READY_TO_PROCESS: "Ready to Process",  # New message when ready to process
            self.STATE_PROCESSING: "Pre Processing",  # Changed from "PROCESSING" to "Pre Processing"
            self.STATE_READY_FOR_EXECUTION: "Ready for Execution",  # New message after processing completed
            self.STATE_DETAIL_MODE: "DETAIL MODE",
            self.STATE_OUTPUTTING: "Restructuring Steps",
            self.STATE_PROCESS_PENDING: "PROGRESS PENDING",
            self.STATE_MODIFYING_CODE: "MODIFYING CODE",
            self.STATE_PROCESS_EXECUTING: "Process Executing",  # New message for code execution
            self.STATE_WAITING: "Waiting",  # New message for waiting state
            self.STATE_SYNCING_CHANGES: "Syncing Changes"  # New message for syncing changes
        }
        
        # Set status message
        self.status_label.setText(messages.get(state, "UNKNOWN"))
        print(f"📝 Status message set to: {messages.get(state, 'UNKNOWN')}")
        
        # Set visual asset
        asset = self.movies.get(state)
        print(f"Setting state {state}, asset: {asset}, type: {type(asset)}")
        
        if asset:
            if isinstance(asset, QMovie):
                # Animated GIF
                print(f"Setting GIF movie for {state}")
                self.gif_label.setMovie(asset)
                self.gif_label.setText("")  # Clear any text
                asset.start()
                print(f"GIF started, frame count: {asset.frameCount()}")
            elif isinstance(asset, QPixmap):
                # Static image (QPixmap)
                print(f"Setting pixmap for {state}, size: {asset.size()}")
                self.gif_label.setMovie(None)  # Clear any movie first
                self.gif_label.setText("")  # Clear any text
                # Scale the pixmap to fit the label size
                label_size = self.gif_label.size()
                if label_size.width() > 0 and label_size.height() > 0:
                    scaled_pixmap = asset.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    # Fallback to fixed size if label size is not available
                    target_size = int(166 * self.scale_factor)
                    scaled_pixmap = asset.scaled(target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.gif_label.setPixmap(scaled_pixmap)
                self.gif_label.setAlignment(Qt.AlignCenter)
                print(f"✅ Pixmap set for {state}, scaled to: {scaled_pixmap.size()}")
                # Force widget update
                self.gif_label.update()
                self.update()
            else:
                print(f"Unknown asset type for {state}: {type(asset)}")
                self.gif_label.setText("?")
        else:
            # Fallback to text emoji - this should NOT happen for valid states
            print(f"❌ CRITICAL: No asset found for {state}, this indicates a loading problem!")
            print(f"Available assets: {list(self.movies.keys())}")
            print(f"Asset values: {[(k, type(v)) for k, v in self.movies.items()]}")
            
            # Force reload assets if none found
            if not any(self.movies.values()):
                print("🔄 No assets loaded, attempting reload...")
                self.load_assets()
                asset = self.movies.get(state)
                if asset:
                    print(f"✅ Asset found after reload: {type(asset)}")
                    # Retry setting the asset
                    if isinstance(asset, QPixmap):
                        self.gif_label.setMovie(None)
                        self.gif_label.setText("")
                        # Scale the reloaded pixmap properly
                        label_size = self.gif_label.size()
                        if label_size.width() > 0 and label_size.height() > 0:
                            scaled_pixmap = asset.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        else:
                            target_size = int(166 * self.scale_factor)
                            scaled_pixmap = asset.scaled(target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.gif_label.setPixmap(scaled_pixmap)
                        self.gif_label.update()
                        self.update()
                        return
            
            # Final fallback
            fallback_emojis = {
                self.STATE_OFF: "⚫",
                self.STATE_TASK_GENERATING: "⚡",
                self.STATE_READY_TO_PROCESS: "✅",
                self.STATE_PROCESSING: "⚡",
                self.STATE_READY_FOR_EXECUTION: "✅",
                self.STATE_DETAIL_MODE: "",
                self.STATE_OUTPUTTING: "📤",
                self.STATE_PROCESS_PENDING: "⏸️",
                self.STATE_MODIFYING_CODE: "📝",
                self.STATE_PROCESS_EXECUTING: "🚀",
                self.STATE_WAITING: "⏳",
                self.STATE_SYNCING_CHANGES: "🔄"
            }
            self.gif_label.setText(fallback_emojis.get(state, "?"))
            self.gif_label.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF;
                    font-size: {int(48 * self.scale_factor)}px;
                    background: transparent;
                    border: none;
                }}
            """)
            self.gif_label.setMovie(None)
            self.gif_label.setPixmap(QPixmap())
        
        # Show/hide progress elements based on state
        if state == self.STATE_OFF:
            self.progress_bar.hide()
            self.close_btn.hide()
            # Stop animation when OFF
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()
            self.progress_bar.setValue(0)
        elif state in [self.STATE_READY_TO_PROCESS, self.STATE_READY_FOR_EXECUTION, self.STATE_WAITING]:
            # Hide loading bar for Ready states and Waiting state - no progress needed
            self.progress_bar.hide()
            self.close_btn.hide()
            # Stop animation for ready states
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()
            self.progress_bar.setValue(0)
        elif state == self.STATE_PROCESS_PENDING:
            self.progress_bar.show()
            self.close_btn.show()
            # Show paused progress bar for pending state
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()  # Stop animation to show paused state
            # Set progress bar to a fixed value to show "paused" state
            self.progress_bar.setValue(50)  # Show half-filled bar to indicate pending
        else:
            # Show progress bar for active processing states
            self.progress_bar.show()
            self.close_btn.show()
            # Start sliding animation when active
            if hasattr(self, 'progress_timer'):
                self.progress_timer.start(50)  # 50ms intervals for smooth animation
    
    def set_off_state(self):
        """Set to OFF state"""
        self.set_state(self.STATE_OFF)
    
    def set_task_generating_state(self):
        """Set to TASK GENERATING state - when Enter & Process or Upload & Process clicked"""
        self.set_state(self.STATE_TASK_GENERATING)
    
    def set_ready_to_process_state(self):
        """Set to READY TO PROCESS state - after task generation completed (detail mode skipped)"""
        self.set_state(self.STATE_READY_TO_PROCESS)
    
    def set_processing_state(self):
        """Set to PRE PROCESSING state - when Start Processing button clicked"""
        self.set_state(self.STATE_PROCESSING)
    
    def set_ready_for_execution_state(self):
        """Set to READY FOR EXECUTION state - after Start Processing completed"""
        self.set_state(self.STATE_READY_FOR_EXECUTION)
    
    def set_detail_mode_state(self):
        """Set to DETAIL MODE state"""
        self.detail_sts_called=True
        self.set_state(self.STATE_DETAIL_MODE)
    
    def set_outputting_state(self):
        """Set to OUTPUTTING RESPONSE state"""
        self.set_state(self.STATE_OUTPUTTING)
    
    def set_process_pending_state(self):
        """Set to PROCESS PENDING state - shows when detail mode popup is closed"""
        self.set_state(self.STATE_PROCESS_PENDING)
    
    def set_modifying_code_state(self):
        """Set to MODIFYING CODE state - shows when sent button is clicked in code chat"""
        self.set_state(self.STATE_MODIFYING_CODE)
    
    def set_process_executing_state(self):
        """Set to PROCESS EXECUTING state - shows when Execute Code button is clicked"""
        self.set_state(self.STATE_PROCESS_EXECUTING)
    
    def set_waiting_state(self):
        """Set to WAITING state - shows after code execution completed"""
        self.set_state(self.STATE_WAITING)
    
    def set_syncing_changes_state(self):
        """Set to SYNCING CHANGES state - shows when Sync Changes button is clicked"""
        self.set_state(self.STATE_SYNCING_CHANGES)
            
    def setup_progress_animation(self):
        """Setup sliding progress bar animation like in reference image"""
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.animate_progress)
        self.progress_value = 0
        self.progress_direction = 1
        self.animation_speed = 3  # Speed of the sliding animation
        
    def animate_progress(self):
        """Create sliding animation effect - thin blue line moves across dark background"""
        self.progress_value += self.animation_speed
        
        # Reset to start when reaching end (continuous sliding effect)
        if self.progress_value > 100:
            self.progress_value = 0
            
        self.progress_bar.setValue(self.progress_value)
    
    def start_processing(self):
        """Switch to processing state"""
        self.set_processing_state()
        
    def stop_processing(self):
        """Stop processing and return to OFF state"""
        # Stop all animations
        for movie in self.movies.values():
            if isinstance(movie, QMovie):
                movie.stop()
        self.set_off_state()
        self.progress_bar.setValue(0)
        self.processing_stopped.emit()
        
    def restart_animations(self):
        """Restart all animations"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.start(50)
            
        # Restart current state animation
        if self.current_state in self.movies:
            asset = self.movies[self.current_state]
            if isinstance(asset, QMovie):
                asset.start()

# Example usage
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    droid_widget = DroidAgentProcessingWidget()
    layout.addWidget(droid_widget)
    window.show()
    sys.exit(app.exec_())