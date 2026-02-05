import os,sys
import json
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import *
import style_loader

class ChatMessage:
    def __init__(self, message, is_user=False, timestamp=None):
        self.message = message
        self.is_user = is_user
        self.timestamp = timestamp or QDateTime.currentDateTime().toString("hh:mm:ss")
def resource_path(relative_path):
    # When run from PyInstaller .exe, _MEIPASS is temp path to bundled files
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DraggableChatPanel(QWidget):
    """Draggable chat panel that can be shown/hidden from the right side"""
    
    # Signals
    panel_shown = pyqtSignal()
    panel_hidden = pyqtSignal()
    chat_message_sent = pyqtSignal(str)
    width_changed = pyqtSignal(int)
    position_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('class', 'ChatPanel')
        self.setMinimumWidth(250)
        self.setMaximumWidth(600)
        self.resize(600, 600)  # Start with maximum width initially
        self.parent_widget = parent
        self.is_visible = False
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_position = QPoint()
        self.resize_start_position = QPoint()
        self.resize_start_width = 10
        self.chat_history = []
        self.chat_history_file = "json_info/chat_history.json"
        
        # Voice integration state
        self.is_recording = False
        
        # Position state
        self.is_on_left = False
        
        self.setupUI()
        self._initialize_voice_integration()
        self.clear_chat_history()
        self.load_chat_history()
        self.hide_panel()
    
    def move_to_left(self):
        """Move chat panel to left side of screen"""
        if self.parent_widget:
            parent_rect = self.parent_widget.geometry()
            # Position on left side
            self.move(0, parent_rect.height() - self.height())
            self.is_on_left = True
            print("Chat panel moved to left")
    
    def move_to_right(self):
        """Move chat panel to right side of screen"""
        if self.parent_widget:
            parent_rect = self.parent_widget.geometry()
            # Position on right side
            self.move(parent_rect.width() - self.width(), parent_rect.height() - self.height())
            self.is_on_left = False
            print("Chat panel moved to right")
   
    def setupUI(self):
        class WhitePlaceholderTextEdit(QTextEdit):
            def __init__(self, placeholder="", parent=None):
                super().__init__(parent)
                self._placeholder = placeholder

            def paintEvent(self, event):
                super().paintEvent(event)
                if not self.toPlainText():
                    painter = QPainter(self.viewport())
                    painter.setPen(QColor("#ffffff"))  # white placeholder
                    painter.drawText(
                        self.rect().adjusted(5, 5, -5, -5),
                        Qt.AlignTop | Qt.AlignLeft,
                        self._placeholder
                    )
        """Setup the chat panel UI"""
        self.setFixedWidth(450)
        self.setMinimumHeight(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Resize handle (left edge for width adjustment)
        self.resize_handle = QWidget()
        self.resize_handle.setFixedWidth(8)
        self.resize_handle.setProperty('class', 'ChatResizeHandle')
        self.resize_handle.setCursor(Qt.SizeHorCursor)
        
        # Drag icon at left edge
        self.drag_icon = QLabel()
        self.drag_icon.setFixedSize(20, 20)
        self.drag_icon.setProperty('class', 'ChatDragIcon')
        try:
            drag_icon_path = os.path.join(os.path.dirname(__file__), "Icon", "drag_right.png")
            if os.path.exists(drag_icon_path):
                self.drag_icon.setPixmap(QPixmap(drag_icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
               
            else:
                self.drag_icon.setText("→")
                self.drag_icon.setStyleSheet("color: #17a2b8; font-weight: bold; font-size: 14px;")
        except:
            self.drag_icon.setText("→")
            self.drag_icon.setStyleSheet("color: #17a2b8; font-weight: bold; font-size: 14px;")
        
        # Chat header (top bar) - non-movable
        self.drag_handle = QWidget()
        self.drag_handle.setFixedHeight(35)
        self.drag_handle.setProperty('class', 'ChatDragHandle')
        self.drag_handle.setCursor(Qt.ArrowCursor)
        
        # Drag handle layout
        handle_layout = QHBoxLayout(self.drag_handle)
        handle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Resize icon removed - chat is not movable
        
        # XPath header button only (Chat functionality removed)
        self.xpath_button = QPushButton("XPath Variables")
        self.xpath_button.setProperty('class', 'XPathHeaderButton')
        self.xpath_button.setCheckable(True)
        self.xpath_button.setChecked(True)  # XPath is active by default
        self.xpath_button.clicked.connect(self.show_xpath_view)
        
        header_button_style = """
            QPushButton {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #666666;
                border-radius: 8px;
                border-bottom-left-radius: 0px;  /* Square bottom to connect with content */
                border-bottom-right-radius: 0px;
                border-bottom: none;  /* No bottom border to connect seamlessly */
                padding: 8px 12px;
                font-size: 14px;
                font-weight: normal;
                outline: none;
                margin: 0px;
            }
            QPushButton:checked {
                background-color: #000000;
                color: #ffffff;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom: none;
            }
            QPushButton:hover {
                background-color: #000000;  /* Keep same background */
                border-color: #888888;
            }
            QPushButton:checked:hover {
                background-color: #000000;
                border: 2px solid #17a2b8;
                border-bottom: none;
            }
        """

        self.xpath_button.setStyleSheet(header_button_style)
        handle_layout.addWidget(self.xpath_button)
        handle_layout.addStretch()
        
        # Hide button removed as requested
        
        layout.addWidget(self.drag_handle)
        
        # Chat content area
        self.chat_content = QWidget()
        self.chat_content.setProperty('class', 'ChatPanel')
        
        # Position drag icon at left edge
        def position_drag_icon():
            if self.isVisible():
                # Position at left edge when chat is open
                self.drag_icon.move(5, self.height() // 2 - 10)
                self.drag_icon.setParent(self)
                self.drag_icon.show()
            else:
                # Hide when chat is closed
                self.drag_icon.hide()
        
        # Store original show/hide events
        original_show = self.showEvent
        original_hide = self.hideEvent
        
        # Override show/hide events
        def custom_show_event(event):
            if original_show:
                original_show(event)
            position_drag_icon()
        
        def custom_hide_event(event):
            if original_hide:
                original_hide(event)
            self.drag_icon.hide()
        
        self.showEvent = custom_show_event
        self.hideEvent = custom_hide_event
        
        # Initial positioning
        QTimer.singleShot(100, position_drag_icon)
        
        content_layout = QVBoxLayout(self.chat_content)
        content_layout.setContentsMargins(10, 10, 10, 5)
        content_layout.setSpacing(8)
        
        # Chat display area (conversation log at top - scrollable)
        self.chat_display = QScrollArea()
        self.chat_display.setProperty('class', 'ChatDisplay')
        self.chat_display.setWidgetResizable(True)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_messages_widget = QWidget()
        self.chat_messages_layout = QVBoxLayout(self.chat_messages_widget)
        self.chat_messages_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_messages_layout.setSpacing(8)
        self.chat_messages_layout.addStretch()
        
        self.chat_display.setWidget(self.chat_messages_widget)
        content_layout.addWidget(self.chat_display, 1)  # Takes most space
        
        # Voice status label (above input area)
        self.voice_status_label = QLabel("")
        self.voice_status_label.setProperty('class', 'ChatVoiceStatus')
        self.voice_status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 2px 5px;
                margin-left: 12px;
            }
        """)
        self.voice_status_label.hide()
        content_layout.addWidget(self.voice_status_label)
        
        # Chat input area at bottom - vertical layout
        input_container = QWidget()
        input_container.setProperty('class', 'ChatInputContainer')
        input_container.setFixedHeight(100)
        
        # Create main vertical layout for input area
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)
        
        # Text input at top - larger area
        self.chat_input = QTextEdit()
        # self.chat_input.setProperty('class', 'ChatInput')
        # self.chat_input.setFixedHeight(60)
        # self.chat_input.setPlaceholderText("Type your message or click mic to speak...")
        

        # self.chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.chat_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # # Add text input to layout
        # input_layout.addWidget(self.chat_input)
        # Text input at top - larger area
        self.chat_input = WhitePlaceholderTextEdit("Type your message or click mic to speak...")
        self.chat_input.setProperty('class', 'ChatInput')
        self.chat_input.setFixedHeight(60)

        self.chat_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add text input to layout
        input_layout.addWidget(self.chat_input)

        
        # Bottom row with buttons
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # Attach button with icon and text
        self.attach_button = QPushButton()
        self.attach_button.setFixedSize(120, 35)
        self.attach_button.setToolTip("Attach files (PDF, TXT, Images)")
        self.attach_button.clicked.connect(self.open_file_dialog)
        
        # Try to set attach icon
        from PyQt5.QtGui import QIcon
        from PyQt5.QtCore import QSize
        try:
            attach_icon_path = "styles/Icon/attach.png"
            self.attach_button.setIcon(QIcon(resource_path(attach_icon_path)))
            self.attach_button.setIconSize(QSize(20, 20))
            self.attach_button.setText("Attach")
        except Exception as e:
            self.attach_button.setText("📎 Attach")
        
        # Attach button styling
        self.attach_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(42, 42, 42, 220);
                border: 1px solid #404040;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(58, 58, 58, 240);
                border-color: #0ea5e9;
            }
            QPushButton:pressed {
                background-color: rgba(74, 74, 74, 240);
            }
        """)
        
        # Speak button with icon and text
        self.mic_button = QPushButton()
        self.mic_button.setFixedSize(120, 35)
        self.mic_button.setToolTip("Click to record voice input")
        
        # Try to set speak icon
        try:
            speak_icon_path = "styles/Icon/speak.png"
            self.mic_button.setIcon(QIcon(resource_path(speak_icon_path)))
            self.mic_button.setIconSize(QSize(20, 20))
            self.mic_button.setText("Speak")
        except:
            self.mic_button.setText("🎤 Speak")
        
        # Speak button styling
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(42, 42, 42, 220);
                border: 1px solid #404040;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(58, 58, 58, 240);
                border-color: #0ea5e9;
            }
            QPushButton:pressed {
                background-color: rgba(74, 74, 74, 240);
            }
            QPushButton[recording="true"] {
                background-color: rgba(220, 38, 38, 240);
                border-color: #ef4444;
            }
            QPushButton[recording="true"]:hover {
                background-color: rgba(185, 28, 28, 240);
            }
        """)
        
        # Send button - transparent with icon only
        send_btn = QPushButton()
        send_btn.setProperty('class', 'ChatSendButton')
        send_btn.clicked.connect(self.send_message)
        send_btn.setFixedSize(40, 35)
        send_btn.setToolTip("Send message")
        
        # Set send button icon
        try:
            icon_path = "styles/Icon/sent_task.png"
            send_btn.setIcon(QIcon(resource_path(icon_path)))
            send_btn.setIconSize(QSize(50, 50))
        except Exception as e:
            print(f"Error loading send icon: {e}")
            send_btn.setText("➤")
        
        # Send button styling - transparent background
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #0ea5e9;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(14, 165, 233, 0.1);
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: rgba(14, 165, 233, 0.2);
            }
        """)
        
        # Add buttons to button row
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.mic_button)
        button_layout.addStretch()  # Push send button to right
        button_layout.addWidget(send_btn)
        
        # Add button row to main layout
        input_layout.addWidget(button_row)
        
        content_layout.addWidget(input_container, 0)  # Fixed size at bottom
        layout.addWidget(self.chat_content)
        
        # Hide chat content by default (functionality moved to Generated Tasks tab)
        self.chat_content.hide()
        
        # XPath display area (now shown by default, chat functionality removed)
        self.xpath_content = QWidget()
        self.xpath_content.setProperty('class', 'ChatPanel')
        self.xpath_content.show()  # Show XPath by default
        
        xpath_layout = QVBoxLayout(self.xpath_content)
        xpath_layout.setContentsMargins(10, 10, 10, 5)
        xpath_layout.setSpacing(8)
        
        # XPath header with controls
        xpath_header_layout = QVBoxLayout()
        
        # Title and refresh button row
        title_row = QHBoxLayout()
        xpath_header_label = QLabel("XPath Configuration")
        xpath_header_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        self.refresh_xpath_btn = QPushButton()
        self.refresh_xpath_btn.setFixedSize(32, 32)
        self.refresh_xpath_btn.setToolTip("Refresh XPath data")
        from PyQt5.QtGui import QIcon
        from PyQt5.QtCore import QSize
        import sys
        import os
        
        
        self.refresh_xpath_btn.setIcon(QIcon(resource_path("styles/Icon/refresh.png")))
        self.refresh_xpath_btn.setIconSize(QSize(20, 20))
        self.refresh_xpath_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 16px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-color: #17a2b8;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: #4CAF50;
            }
        """)
        self.refresh_xpath_btn.clicked.connect(self.refresh_xpath_data)
        
        title_row.addWidget(xpath_header_label)
        title_row.addStretch()
        title_row.addWidget(self.refresh_xpath_btn)
        xpath_header_layout.addLayout(title_row)
        
        # Search bar
        self.xpath_search = QLineEdit()
        self.xpath_search.setPlaceholderText(" Search XPath keys or values...")
        self.xpath_search.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                margin: 2px 0;
            }
            QLineEdit:focus {
                border-color: #17a2b8;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.xpath_search.textChanged.connect(self.filter_xpath_entries)
        xpath_header_layout.addWidget(self.xpath_search)
        
        # Sort and filter controls
        controls_row = QHBoxLayout()
        
        # Sort dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Sort by Keys A-Z",
            "Sort by Keys Z-A", 
            "Sort by Values A-Z",
            "Sort by Values Z-A"
        ])
        dropdown_style = """
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a4a4a, stop:1 #3a3a3a);
                border: 1px solid #666666;
                border-radius: 8px;
                padding: 8px 16px 8px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                min-width: 120px;
                min-height: 16px;
            }
            QComboBox:hover {
                border-color: #17a2b8;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
            QComboBox:focus {
                border-color: #4CAF50;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #666666;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a5a5a, stop:1 #4a4a4a);
            }
            QComboBox::drop-down:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a6a6a, stop:1 #5a5a5a);
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #cccccc;
                margin: 0px 2px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 6px;
                selection-background-color: #17a2b8;
                selection-color: white;
                color: white;
                font-size: 12px;
                padding: 2px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 12px;
                border-bottom: 1px solid #555555;
                min-height: 18px;
            }
            QComboBox QAbstractItemView::item:last {
                border-bottom: none;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #17a2b8;
                color: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """
        self.sort_combo.setStyleSheet(dropdown_style)
        self.sort_combo.currentTextChanged.connect(self.sort_xpath_entries)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Show All",
            "Show Not_assigned Only",
            "Show Assigned Only"
        ])
        self.filter_combo.setStyleSheet(dropdown_style)
        self.filter_combo.currentTextChanged.connect(self.filter_xpath_entries)
        
        controls_row.addWidget(QLabel("Sort:"))
        controls_row.addWidget(self.sort_combo)
        controls_row.addWidget(QLabel("Filter:"))
        controls_row.addWidget(self.filter_combo)
        controls_row.addStretch()
        
        # Style the labels
        for i in range(controls_row.count()):
            widget = controls_row.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold;")
        
        xpath_header_layout.addLayout(controls_row)
        xpath_layout.addLayout(xpath_header_layout)
        
        # XPath display scroll area
        self.xpath_display = QScrollArea()
        self.xpath_display.setProperty('class', 'ChatDisplay')
        self.xpath_display.setWidgetResizable(True)
        self.xpath_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.xpath_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # XPath list widget
        self.xpath_list_widget = QWidget()
        self.xpath_list_layout = QVBoxLayout(self.xpath_list_widget)
        self.xpath_list_layout.setContentsMargins(5, 5, 5, 5)
        self.xpath_list_layout.setSpacing(8)
        self.xpath_list_layout.addStretch()
        
        self.xpath_display.setWidget(self.xpath_list_widget)
        xpath_layout.addWidget(self.xpath_display, 1)
        
        # XPath status label
        self.xpath_status_label = QLabel("No XPath data available")
        self.xpath_status_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 5px;
                text-align: center;
            }
        """)
        xpath_layout.addWidget(self.xpath_status_label)
        
        layout.addWidget(self.xpath_content)
        
        # Initialize XPath data
        self.xpath_data = {}
        
        # Apply styles
        style_loader.apply_stylesheet(self)
        
        # Connect enter key to send
        self.chat_input.installEventFilter(self)
        
        # Connect voice button after UI setup
        QTimer.singleShot(100, self._connect_voice_button)

    def clear_chat_history(self):
        """Clear chat history both in memory and file"""
        try:
            # Clear in-memory history
            self.chat_history = []
            
            # Clear chat history file
            import json
            import os
            
            if os.path.exists(self.chat_history_file):
                # Write empty list to file
                with open(self.chat_history_file, 'w') as f:
                    json.dump([], f)
                print(f"✅ Chat history file '{self.chat_history_file}' cleared")
            else:
                # Create empty file if it doesn't exist
                with open(self.chat_history_file, 'w') as f:
                    json.dump([], f)
                print(f"✅ Chat history file '{self.chat_history_file}' created as empty")
                
            # Clear UI chat messages if the UI is already initialized
            if hasattr(self, 'chat_messages_area'):
                self.clear_chat_ui()
                
        except Exception as e:
            print(f"❌ Error clearing chat history: {e}")   
            
    def _initialize_voice_integration(self):
        """Initialize voice integration with Gemini API."""
        try:
            from voice_integration_thread import VoiceIntegrationThread
            import config
            
            # Get API key
            GEMINI_API_KEY = getattr(config, 'API_KEY', None)
            
            if not GEMINI_API_KEY:
                print("⚠️ Warning: No Gemini API key found in config")
                return
            
            # Create voice thread
            self.voice_thread = VoiceIntegrationThread(GEMINI_API_KEY)
            
            # Connect voice thread signals
            self.voice_thread.recording_started.connect(self._on_recording_started)
            self.voice_thread.recording_stopped.connect(self._on_recording_stopped)
            self.voice_thread.transcription_ready.connect(self._on_transcription_ready)
            self.voice_thread.error_occurred.connect(self._on_voice_error)
            self.voice_thread.processing_started.connect(self._on_processing_started)
            self.voice_thread.processing_finished.connect(self._on_processing_finished)
            
            print("✅ Voice integration initialized successfully")
            
        except Exception as e:
            print(f"❌ Voice integration failed: {e}")
            # Voice button will be disabled in _connect_voice_button
    
    def _connect_voice_button(self):
        """Connect the microphone button after UI is set up."""
        if hasattr(self, 'voice_thread') and hasattr(self, 'mic_button'):
            # Connect microphone button
            self.mic_button.clicked.connect(self._toggle_voice_recording)
            print("🔗 Voice button connected successfully")
        else:
            # Disable mic button if voice integration failed
            if hasattr(self, 'mic_button'):
                self.mic_button.setEnabled(False)
                self.mic_button.setToolTip("Voice integration unavailable")
                print("❌ Voice button disabled - integration unavailable")

    def _toggle_voice_recording(self):
        """Toggle voice recording on/off."""
        if not hasattr(self, 'voice_thread'):
            return
        
        if self.is_recording:
            # Stop recording
            self.voice_thread.stop_recording()
        else:
            # Start recording
            # Set context for the conversation
            context = {
                'generate_response': False,  # Just transcribe, don't generate responses
                'chat_history': [msg.message for msg in self.chat_history],
                'current_tasks': [],
            }
            self.voice_thread.set_context(context)
            self.voice_thread.start_recording()

    def _on_recording_started(self):
        """Handle recording started event."""
        self.is_recording = True
        self.mic_button.setProperty("recording", True)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Recording... Click to stop")
        
        self.voice_status_label.setText("🔴 Recording... Click mic to stop")
        self.voice_status_label.show()

    def _on_recording_stopped(self):
        """Handle recording stopped event."""
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        self.mic_button.setToolTip("Click to record voice input")
        
        self.voice_status_label.setText("⏳ Processing audio...")

    def _on_processing_started(self):
        """Handle processing started event."""
        self.voice_status_label.setText("🤖 Transcribing......")

    def _on_processing_finished(self):
        """Handle processing finished event."""
        QTimer.singleShot(2000, self.voice_status_label.hide)

    def _on_transcription_ready(self, text):
        """Handle transcription ready event."""
        # Add transcribed text to the chat input field
        current_text = self.chat_input.toPlainText().strip()
        if current_text:
            # Append to existing text
            self.chat_input.setPlainText(current_text + " " + text)
        else:
            # Set as new text
            self.chat_input.setPlainText(text)
        
        # Move cursor to end
        cursor = self.chat_input.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_input.setTextCursor(cursor)
        
        self.voice_status_label.setText("✅ Transcription complete")
        
        # Auto-hide status after 2 seconds
        QTimer.singleShot(2000, self.voice_status_label.hide)

    def _on_voice_error(self, error_msg):
        """Handle voice error event."""
        self.is_recording = False
        self.mic_button.setProperty("recording", False)
        self.mic_button.style().unpolish(self.mic_button)
        self.mic_button.style().polish(self.mic_button)
        
        self.voice_status_label.setText(f"❌ {error_msg}")
        self.voice_status_label.show()
        
        # Auto-hide error after 4 seconds
        QTimer.singleShot(4000, self.voice_status_label.hide)

    def show_xpath_view(self):
        """Show XPath view (chat functionality removed)"""
        self.xpath_button.setChecked(True)
        if hasattr(self, 'chat_content'):
            self.chat_content.hide()
        self.xpath_content.show()
        print("🔧 Switched to XPath view")
        
        # Refresh XPath display when switching to XPath view
        self.refresh_xpath_data()
    
    def refresh_xpath_data(self):
        """Refresh XPath data from JSON file"""
        import json
        import os
        
        json_path = "json_info/json_xpath.json"
        self.xpath_data = {}
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.xpath_data = json.load(f)
                print(f"🔧 Loaded {len(self.xpath_data)} XPath entries")
            except Exception as e:
                print(f"❌ Error loading XPath JSON: {e}")
                self.xpath_data = {}
        
        # Store original data for filtering/sorting
        self.original_xpath_data = self.xpath_data.copy()
        self.filtered_xpath_data = self.xpath_data.copy()
        
        self.update_xpath_display()
    
    def save_xpath_data(self):
        """Save XPath data to JSON file in real-time"""
        import json
        import os
        
        json_path = "json_info/json_xpath.json"
        
        try:
            # Ensure directory exists
            os.makedirs("json_info", exist_ok=True)
            
            # Save the data
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.xpath_data, f, indent=4, ensure_ascii=False)
            print(f"💾 Saved XPath data to {json_path}")
            
        except Exception as e:
            print(f"❌ Error saving XPath JSON: {e}")
    
    def filter_xpath_entries(self):
        """Filter XPath entries based on search text and filter combo"""
        search_text = self.xpath_search.text().lower()
        filter_option = self.filter_combo.currentText()
        
        # Start with original data
        filtered_data = {}
        
        for key, value in self.original_xpath_data.items():
            # Apply search filter
            if search_text:
                if (search_text not in key.lower() and 
                    search_text not in str(value).lower()):
                    continue
            
            # Apply dropdown filter
            if filter_option == "Show Not_assigned Only":
                if str(value).lower() != "not_assigned":
                    continue
            elif filter_option == "Show Assigned Only":
                if str(value).lower() == "not_assigned":
                    continue
            # "Show All" - no additional filtering
            
            filtered_data[key] = value
        
        self.filtered_xpath_data = filtered_data
        self.sort_xpath_entries()
    
    def sort_xpath_entries(self):
        """Sort XPath entries based on sort combo selection"""
        sort_option = self.sort_combo.currentText()
        
        if sort_option == "Sort by Keys A-Z":
            sorted_items = sorted(self.filtered_xpath_data.items(), key=lambda x: x[0].lower())
        elif sort_option == "Sort by Keys Z-A":
            sorted_items = sorted(self.filtered_xpath_data.items(), key=lambda x: x[0].lower(), reverse=True)
        elif sort_option == "Sort by Values A-Z":
            sorted_items = sorted(self.filtered_xpath_data.items(), key=lambda x: str(x[1]).lower())
        elif sort_option == "Sort by Values Z-A":
            sorted_items = sorted(self.filtered_xpath_data.items(), key=lambda x: str(x[1]).lower(), reverse=True)
        else:
            sorted_items = list(self.filtered_xpath_data.items())
        
        # Convert back to dict maintaining order
        self.filtered_xpath_data = dict(sorted_items)
        self.update_xpath_display()
    
    def update_xpath_display(self):
        """Update the XPath display with filtered and sorted data"""
        data_to_display = getattr(self, 'filtered_xpath_data', self.xpath_data)
        print(f"🔄 update_xpath_display called with {len(data_to_display)} filtered XPath entries")
        
        # Clear existing XPath widgets
        for i in reversed(range(self.xpath_list_layout.count() - 1)):
            child = self.xpath_list_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not data_to_display:
            # No XPath data to display
            total_count = len(getattr(self, 'original_xpath_data', {}))
            if total_count > 0:
                self.xpath_status_label.setText(f"No entries match current filter (Total: {total_count})")
            else:
                self.xpath_status_label.setText("No XPath data available")
            return
        
        # Update count label
        count = len(data_to_display)
        total_count = len(getattr(self, 'original_xpath_data', data_to_display))
        if count == total_count:
            self.xpath_status_label.setText(f"{count} XPath entry{'ies' if count != 1 else ''} available")
        else:
            self.xpath_status_label.setText(f"Showing {count} of {total_count} XPath entries")
        
        # Add XPath widgets
        for xpath, info in data_to_display.items():
            xpath_widget = self.create_editable_xpath_widget(xpath, info)
            # Insert before stretch
            self.xpath_list_layout.insertWidget(
                self.xpath_list_layout.count() - 1, xpath_widget
            )
        
        print(f"📊 Updated XPath display with {count} entries")
    
    def create_editable_xpath_widget(self, xpath, info):
        """Create an editable widget for a single XPath entry"""
        widget = QWidget()
        main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(12, 6, 12, 6)
        main_layout.setSpacing(8)
        
        # Left side - XPath key label (non-editable) with fixed width for alignment
        xpath_label = QLabel(f"{xpath}:")
        xpath_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 8px;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                border-left: 3px solid #17a2b8;
            }
        """)
        xpath_label.setWordWrap(True)
        xpath_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        xpath_label.setFixedWidth(180)  # Fixed width for alignment
        main_layout.addWidget(xpath_label)
        
        # Right side - Editable value field
        value_edit = QLineEdit(str(info))
        value_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                min-height: 18px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: #353538;
            }
            QLineEdit:hover {
                border-color: #17a2b8;
                background-color: #353538;
            }
        """)
        
        # Add context menu for delete option
        value_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        value_edit.customContextMenuRequested.connect(lambda pos: self.show_xpath_context_menu(pos, xpath, value_edit))
        
        # Set placeholder and styling based on value
        if str(info).lower() == "not_assigned":
            value_edit.setPlaceholderText("Enter XPath value...")
            value_edit.setStyleSheet(value_edit.styleSheet() + """
                QLineEdit {
                    border-color: #ff6b6b;
                    background-color: rgba(255, 107, 107, 0.1);
                }
            """)
        
        # Connect real-time saving
        def on_value_changed():
            new_value = value_edit.text().strip()
            if new_value != str(info):
                # Update the data
                self.xpath_data[xpath] = new_value
                self.original_xpath_data[xpath] = new_value
                
                # Save to JSON file immediately
                self.save_xpath_data()
                
                # Update styling based on new value
                if new_value.lower() == "not_assigned" or not new_value:
                    value_edit.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d30;
                            border: 1px solid #ff6b6b;
                            border-radius: 6px;
                            padding: 8px 12px;
                            color: white;
                            font-size: 12px;
                            font-family: 'Consolas', 'Monaco', monospace;
                            background-color: rgba(255, 107, 107, 0.1);
                            min-height: 18px;
                        }
                        QLineEdit:focus {
                            border-color: #ff6b6b;
                            background-color: rgba(255, 107, 107, 0.15);
                        }
                    """)
                else:
                    value_edit.setStyleSheet("""
                        QLineEdit {
                            background-color: #2d2d30;
                            border: 1px solid #4CAF50;
                            border-radius: 6px;
                            padding: 8px 12px;
                            color: white;
                            font-size: 12px;
                            font-family: 'Consolas', 'Monaco', monospace;
                            background-color: rgba(76, 175, 80, 0.1);
                            min-height: 18px;
                        }
                        QLineEdit:focus {
                            border-color: #4CAF50;
                            background-color: rgba(76, 175, 80, 0.15);
                        }
                    """)
                
                print(f"💾 Updated XPath '{xpath}' = '{new_value}'")
        
        value_edit.textChanged.connect(on_value_changed)
        value_edit.editingFinished.connect(on_value_changed)
        
        main_layout.addWidget(value_edit, 1)  # Give value field more space
        
        # Add bottom border to widget for separation
        widget.setStyleSheet("""
            QWidget {
                border-bottom: 1px solid #333333;
                margin-bottom: 4px;
                padding-bottom: 4px;
            }
        """)
        
        return widget
    
    def show_xpath_context_menu(self, pos, xpath, value_edit):
        """Show context menu for XPath entry with delete option"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f44336;
                color: white;
            }
        """)
        
        # Delete action
        delete_action = context_menu.addAction("🗑️ Delete XPath Entry")
        delete_action.triggered.connect(lambda: self.delete_xpath_entry(xpath))
        
        # Show context menu at cursor position
        global_pos = value_edit.mapToGlobal(pos)
        context_menu.exec_(global_pos)
    
    def delete_xpath_entry(self, xpath):
        """Delete XPath entry from data and refresh display"""
        if xpath in self.xpath_data:
            del self.xpath_data[xpath]
            if hasattr(self, 'original_xpath_data') and xpath in self.original_xpath_data:
                del self.original_xpath_data[xpath]
            self.save_xpath_data()
            self.filter_xpath_entries()  # Refresh display
            print(f"🗑️ Deleted XPath entry: {xpath}")

    def create_xpath_widget(self, xpath, info):
        """Legacy method - replaced by create_editable_xpath_widget"""
        return self.create_editable_xpath_widget(xpath, info)

    # Variable manager functionality removed - replaced with XPath functionality

    def cleanup_voice(self):
        """Clean up voice resources when closing."""
        if hasattr(self, 'voice_thread'):
            self.voice_thread.cleanup()
            print("🔧 Voice resources cleaned up")
        
    def eventFilter(self, obj, event):
        """Handle enter key in chat input"""
        if obj == self.chat_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for resizing only (no dragging)"""
        if event.button() == Qt.LeftButton:
            # Check if clicking on resize area (left edge)
            if event.x() <= 10:
                self.is_resizing = True
                self.resize_start_position = event.globalPos()
                self.resize_start_width = self.width()
                event.accept()
                return
        super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing only (no dragging)"""
        if event.buttons() == Qt.LeftButton:
            if self.is_resizing:
                # Handle width resizing
                delta_x = event.globalPos().x() - self.resize_start_position.x()
                new_width = max(250, min(600, self.resize_start_width - delta_x))
                
                # Update width
                old_width = self.width()
                self.setFixedWidth(new_width)
                
                # Emit signal if width changed significantly
                if abs(new_width - old_width) > 5:
                    self.width_changed.emit(new_width)
                
                # Always emit position change during resize
                self.position_changed.emit()
                
                event.accept()
                return
        
        # Update cursor based on position
        if event.x() <= 10:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_resizing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def toggle_panel(self):
        """Toggle panel visibility"""
        if self.isVisible():
            self.hide()
            self.panel_hidden.emit()
        else:
            # Always set to maximum width when opening
            self.setFixedWidth(600)
            self.show()
            self.panel_shown.emit()
            
    def show_panel(self):
        """Show the chat panel"""
        # Always set to maximum width when showing
        self.setFixedWidth(600)
        self.show()
        self.panel_shown.emit()
        
    def hide_panel(self):
        """Hide the chat panel"""
        self.hide()
        self.panel_hidden.emit()
            
    def add_message(self, message, is_user=False):
        """Add a message to the chat"""
        chat_msg = ChatMessage(message, is_user)
        self.chat_history.append(chat_msg)
       
        # Create message widget
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
       
        # Message bubble
        bubble = QLabel(message)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(343)   # max width for wrapping
        bubble.setMinimumHeight(0)    # let it shrink naturally

        if is_user:
            bubble.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                                stop:0 #5FCCF5,
                                                stop:0.2855 #00BBF2,
                                                stop:0.993 #005B7F);
                    color: #FFFFFF;
                    border-radius: {20 if len(message) > 5 else 15}px;  /* pill for short text */
                    padding: 8px 16px;
                    font-family: 'Asen Pro';
                    font-weight: 600;
                    font-size: 16px;
                    letter-spacing: 0.05em;
                }}
    """)
            bubble.setWordWrap(True)         # Allow multi-line
            bubble.setMaximumWidth(343)  
 
            msg_layout.addStretch()
            msg_layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background: transparent;   /* no background */
                    color: #FFFFFF;           /* white text */
                    font-family: 'Asen Pro';
                    font-style: normal;
                    font-weight: 600;
                    font-size: 14px;
                    line-height: 21px;        /* 150% line spacing */
                    letter-spacing: 0.02em;   /* optional for clarity */
                    padding: 4px 0;           /* top/bottom breathing space */
                }
            """)
            bubble.setWordWrap(True)          # allow multiline wrapping
            bubble.setMaximumWidth(551)       # match Figma width
            msg_layout.addWidget(bubble)
            msg_layout.addStretch()
        # Insert before stretch
        self.chat_messages_layout.insertWidget(
            self.chat_messages_layout.count() - 1, msg_widget
        )
       
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
       
        # Save history
        self.save_chat_history()
            
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        """Send a chat message"""
        message = self.chat_input.toPlainText().strip()
        if message:
            self.add_message(message, is_user=True)
            self.chat_input.clear()
            self.chat_message_sent.emit(message)
            
            # Add a response (you can customize this)
            # QTimer.singleShot(1000, lambda: self.add_message(
            #     "I'll help you restructure the tasks based on your request.", 
            #     is_user=False
            # ))
            
    def load_chat_history(self):
        """Load chat history from file"""
        try:
            if os.path.exists(self.chat_history_file):
                with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                for msg_data in history_data:
                    self.add_message(msg_data['message'], msg_data['is_user'])
                    
        except Exception as e:
            print(f"Error loading chat history: {e}")
            
    def save_chat_history(self):
        """Save chat history to file"""
        try:
            history_data = []
            for msg in self.chat_history:
                history_data.append({
                    'message': msg.message,
                    'is_user': msg.is_user,
                    'timestamp': msg.timestamp
                })
                
            with open(self.chat_history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving chat history: {e}")
            
    def clear_history(self):
        """Clear chat history"""
        self.chat_history.clear()
        
        # Clear UI
        for i in reversed(range(self.chat_messages_layout.count() - 1)):
            child = self.chat_messages_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        # Save empty history
        self.save_chat_history()

    def open_file_dialog(self):
        """Open file dialog to select files for attachment."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # Define supported file types
            file_filter = "Supported Files (*.pdf *.txt *.png *.jpg *.jpeg *.gif *.bmp);;PDF Files (*.pdf);;Text Files (*.txt);;Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
            
            # Open file dialog
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files to Attach",
                "",
                file_filter
            )
            
            if file_paths:
                # Process selected files
                self.process_attached_files(file_paths)
                
        except Exception as e:
            print(f"Error opening file dialog: {e}")
            # Show error message to user
            self.add_message(f"Error selecting files: {str(e)}", is_user=False)
    
    def process_attached_files(self, file_paths):
        """Process the selected attached files."""
        try:
            attached_files = []
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    # Check file size (limit to 10MB)
                    if file_size > 10 * 1024 * 1024:
                        self.add_message(f"File '{file_name}' is too large (max 10MB). Skipping.", is_user=False)
                        continue
                    
                    attached_files.append({
                        'path': file_path,
                        'name': file_name,
                        'size': file_size
                    })
            
            if attached_files:
                # Create attachment message
                attachment_text = "📎 Attached files:\n"
                for file_info in attached_files:
                    size_mb = file_info['size'] / (1024 * 1024)
                    attachment_text += f"• {file_info['name']} ({size_mb:.1f} MB)\n"
                
                # Add attachment message to chat
                self.add_message(attachment_text, is_user=True)
                
                # Store attachments for processing (you can extend this as needed)
                self.current_attachments = attached_files
                
                # Optionally process files immediately or wait for user message
                self.add_message("Files attached successfully. You can now send a message to process them.", is_user=False)
            else:
                self.add_message("No valid files were selected.", is_user=False)
                
        except Exception as e:
            print(f"Error processing attached files: {e}")
            self.add_message(f"Error processing files: {str(e)}", is_user=False)

    def closeEvent(self, event):
        """Handle close event to cleanup voice resources."""
        self.cleanup_voice()
        super().closeEvent(event)

class ChatToggleButton(QPushButton):
    """Button to show/hide chat panel with drag icons"""
    
    def __init__(self, chat_panel, parent=None):
        super().__init__(parent)
        self.chat_panel = chat_panel
        self.parent_window = parent
        self.setProperty('class', 'ChatToggleButton')
        self.setFixedSize(30, 60)  # Compact size
        self.setToolTip("Click to show/hide chat")
        self.clicked.connect(self.toggle_chat)
        
        # Set initial icon (drag left to show)
        self.update_icon()
        
        # Apply styles
        style_loader.apply_stylesheet(self)
        
        # Connect to panel visibility changes
        self.chat_panel.panel_shown.connect(self.update_icon)
        self.chat_panel.panel_hidden.connect(self.update_icon)
        
        # Show the button
        self.show()
        self.raise_()
        
    def update_icon(self):
        """Update icon based on panel state"""
        try:
            if self.chat_panel.isVisible():
                # Panel is visible, show simple arrow to hide
                self.setText("→")
                self.setToolTip("Hide chat")
            else:
                # Panel is hidden, show simple arrow to show
                self.setText("←")
                self.setToolTip("Show chat")
                
            # Remove icon loading since we're using text arrows now
            if False:
                self.setIcon(QIcon(icon_path))
                self.setIconSize(QSize(30, 30))
            else:
                # Fallback to text if icons not found
                self.setText("💬" if not self.chat_panel.isVisible() else "✖")
        except Exception as e:
            print(f"Error updating chat toggle icon: {e}")
            self.setText("💬")
            
    def position_on_edge(self):
        """Position button on right edge of parent window"""
        if self.parent_window:
            # Position on right edge of content area, not window
            if hasattr(self.parent_window, 'content_area'):
                content_rect = self.parent_window.content_area.geometry()
                # Position at right edge of content area
                x = content_rect.right() - self.width() - 5
                y = content_rect.top() + (content_rect.height() - self.height()) // 2
                self.move(x, y)
            else:
                # Fallback to window positioning
                x = self.parent_window.width() - self.width() - 10
                y = (self.parent_window.height() - self.height()) // 2
                self.move(x, y)
            
            self.raise_()  # Bring to front
            self.show()  # Ensure visibility
            self.setVisible(True)  # Force visibility
            
    def toggle_chat(self):
        """Toggle chat panel"""
        self.chat_panel.toggle_panel()
        
    def resizeEvent(self, event):
        """Handle resize to maintain edge position"""
        super().resizeEvent(event)
        self.position_on_edge()