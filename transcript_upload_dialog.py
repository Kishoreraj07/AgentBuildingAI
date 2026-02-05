# transcript_upload_dialog.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QTextEdit, QWidget, QGraphicsDropShadowEffect, QScrollArea)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor
import os

# Import your existing style loader (adjust path if needed)
try:
    from style_loader import apply_stylesheet
except ImportError:
    def apply_stylesheet(widget):
        pass


class TranscriptUploadDialog(QDialog):
    """Custom dialog for multiple transcript uploads, additional docs, and custom prompt input - AgentFlow Style"""
    
    def __init__(self, parent=None, video_count=1):
        super().__init__(parent)
        self.video_count = video_count
        self.transcript_paths = [None] * video_count
        self.additional_docs = []  # NEW: List of additional document paths
        self.custom_prompt = ""
        self.draggable = True
        self.mouse_pressed = False
        self.mouse_position = None
        
        # Store references to file labels and browse buttons
        self.file_labels = []
        self.browse_buttons = []
        self.file_rows = []
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Dynamic height based on video count + additional docs section
        base_height = 520  # Increased from 420
        height_per_video = 60
        total_height = base_height + (self.video_count * height_per_video)
        self.setFixedSize(600, min(total_height, 750))  # Max 750px height
        
        container = QWidget(self)
        container.setGeometry(0, 0, 600, min(total_height, 750))
        container.setStyleSheet("""
            QWidget {
                background-color: #18181b;
                border: 1px solid #404040;
                border-radius: 16px;
                color: #e4e4e4;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(22, 18, 22, 22)
        
        # ========== TITLE BAR ==========
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        title = QLabel("Configure Video Processing")
        title.setStyleSheet("color: #e4e4e4; font-size: 16px; font-weight: bold; font-family: 'Asen Pro';")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #e4e4e4; border: none; font-size: 18px; border-radius: 16px; }
            QPushButton:hover { background-color: #ff4444; color: white; }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)
        layout.addSpacing(24)
        
        # ========== SCROLLABLE CONTAINER ==========
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4ecdc4;
                border-radius: 5px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # ========== MAIN CONTAINER ==========
        combined_container = QWidget()
        combined_container.setStyleSheet("""
            QWidget { background-color: #2a2a2a; border: 2px solid #404040; border-radius: 12px; padding: 16px; }
        """)
        combined_layout = QVBoxLayout(combined_container)
        combined_layout.setSpacing(20)
        combined_layout.setContentsMargins(16, 16, 16, 16)
        
        # ========== TRANSCRIPT SECTION ==========
        transcript_header = QLabel(f"Upload Transcripts (Optional) - {self.video_count} Video{'s' if self.video_count > 1 else ''}")
        transcript_header.setStyleSheet("color: #4ecdc4; font-weight: bold; font-size: 16px; padding: 8px 0; border-bottom: 1px solid #404040; margin-bottom: 8px; font-family: 'Asen Pro';")
        combined_layout.addWidget(transcript_header)
        
        # Create file row for each video
        for i in range(self.video_count):
            file_row = QHBoxLayout()
            file_row.setSpacing(12)
            
            # Video number label (if multiple videos)
            if self.video_count > 1:
                video_num_label = QLabel(f"Video {i+1}:")
                video_num_label.setStyleSheet("color: #888888; font-size: 14px; font-weight: bold; min-width: 60px;")
                file_row.addWidget(video_num_label)
            
            # File label
            file_label = QLabel("No file selected")
            file_label.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e; color: #888888; padding: 10px 12px;
                    border-radius: 6px; border: 1px solid #333333; font-size: 14px; font-family: 'Asen Pro';
                }
            """)
            file_label.setMinimumHeight(40)
            file_row.addWidget(file_label, 1)
            
            # Browse button
            browse_btn = QPushButton("Browse")
            browse_btn.setFixedSize(100, 40)
            browse_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4ecdc4; color: #1e1e1e; border: none; border-radius: 6px;
                    padding: 8px 20px; font-weight: bold; font-size: 14px; font-family: 'Asen Pro';
                }
                QPushButton:hover { background-color: #45b7aa; }
                QPushButton:pressed { background-color: #3da89e; }
            """)
            browse_btn.clicked.connect(lambda checked, idx=i: self.browse_transcript(idx))
            file_row.addWidget(browse_btn)
            
            combined_layout.addLayout(file_row)
            
            # Store references
            self.file_labels.append(file_label)
            self.browse_buttons.append(browse_btn)
            self.file_rows.append(file_row)
        
        combined_layout.addSpacing(16)
        
        # ========== NEW: ADDITIONAL DOCS SECTION ==========
        additional_docs_header = QLabel("Additional Supporting Documents (Optional)")
        additional_docs_header.setStyleSheet("color: #4ecdc4; font-weight: bold; font-size: 16px; padding: 8px 0; border-bottom: 1px solid #404040; margin-bottom: 8px; font-family: 'Asen Pro';")
        combined_layout.addWidget(additional_docs_header)
        
        # Additional docs file row
        docs_row = QHBoxLayout()
        docs_row.setSpacing(12)
        
        self.additional_docs_label = QLabel("No documents selected")
        self.additional_docs_label.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e; color: #888888; padding: 10px 12px;
                border-radius: 6px; border: 1px solid #333333; font-size: 14px; font-family: 'Asen Pro';
            }
        """)
        self.additional_docs_label.setMinimumHeight(40)
        docs_row.addWidget(self.additional_docs_label, 1)
        
        browse_docs_btn = QPushButton("Browse")
        browse_docs_btn.setFixedSize(100, 40)
        browse_docs_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ecdc4; color: #1e1e1e; border: none; border-radius: 6px;
                padding: 8px 20px; font-weight: bold; font-size: 14px; font-family: 'Asen Pro';
            }
            QPushButton:hover { background-color: #45b7aa; }
            QPushButton:pressed { background-color: #3da89e; }
        """)
        browse_docs_btn.clicked.connect(self.browse_additional_docs)
        docs_row.addWidget(browse_docs_btn)
        
        combined_layout.addLayout(docs_row)
        combined_layout.addSpacing(16)
        
        # ========== CUSTOM PROMPT SECTION ==========
        prompt_header = QLabel("Custom Prompt (Optional)")
        prompt_header.setStyleSheet("color: #4ecdc4; font-weight: bold; font-size: 16px; padding: 8px 0; border-bottom: 1px solid #404040; margin-bottom: 8px; font-family: 'Asen Pro';")
        combined_layout.addWidget(prompt_header)
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Enter custom instructions for processing...\n\nExample: 'Focus on security-related steps' or 'Include detailed error handling'")
        self.prompt_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; border: 1px solid #333333; border-radius: 6px;
                color: #e4e4e4; padding: 10px; font-size: 14px; font-family: 'Asen Pro';
            }
            QTextEdit:focus { border: 2px solid #4ecdc4; }
        """)
        self.prompt_text.setMinimumHeight(100)
        self.prompt_text.setMaximumHeight(120)
        combined_layout.addWidget(self.prompt_text)
        
        scroll_layout.addWidget(combined_container)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # ========== BOTTOM BUTTONS ==========
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(120, 40)
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: #2C2C2C; color: #e4e4e4; border: 1px solid #444444; border-radius: 6px; font-size: 16px; font-weight: 500; }
            QPushButton:hover { background-color: #3a3a3a; border-color: #555555; }
            QPushButton:pressed { background-color: #252525; }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        proceed_btn = QPushButton("Proceed")
        proceed_btn.setFixedSize(120, 40)
        proceed_btn.setStyleSheet("""
            QPushButton { background-color: #4ecdc4; color: #1e1e1e; border: none; border-radius: 6px; font-weight: bold; font-size: 16px; }
            QPushButton:hover { background-color: #45b7aa; }
            QPushButton:pressed { background-color: #3da89e; }
        """)
        proceed_btn.clicked.connect(self.accept)
        button_layout.addWidget(proceed_btn)
        
        layout.addLayout(button_layout)
        
        self.setGraphicsEffect(self.create_shadow_effect())

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 160))
        return shadow

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.mouse_position = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self.draggable and self.mouse_pressed:
            self.move(event.globalPos() - self.mouse_position)
            event.accept()

    def browse_transcript(self, video_index):
        """Open file dialog for specific video transcript"""
        dialog = QFileDialog(self)
        dialog.setWindowTitle(f"Select Transcript File for Video {video_index + 1}")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Transcript Files (*.txt *.srt *.vtt *.docx *.json);;All Files (*)")

        dialog.setDirectory(os.path.expanduser("~"))
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setProperty('class', 'CustomFileDialog')
        apply_stylesheet(dialog)

        urls = []
        paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~")
        ]
        for path in paths:
            if os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))
        dialog.setSidebarUrls(urls)

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.transcript_paths[video_index] = selected[0]
                file_name = os.path.basename(self.transcript_paths[video_index])
                self.file_labels[video_index].setText(file_name)
                self.file_labels[video_index].setStyleSheet("""
                    QLabel {
                        background-color: #1a4a47;
                        color: #4ecdc4;
                        padding: 10px 12px;
                        border-radius: 6px;
                        border: 1px solid #4ecdc4;
                        font-size: 14px;
                        font-weight: 500;
                        font-family: 'Asen Pro';
                    }
                """)

    def browse_additional_docs(self):
        """Open file dialog for additional supporting documents (multiple selection allowed)"""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Additional Supporting Documents")
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.ExistingFiles)  # Allow multiple files
        dialog.setNameFilter("Document Files (*.txt *.docx *.pdf *.doc);;All Files (*)")

        dialog.setDirectory(os.path.expanduser("~"))
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setProperty('class', 'CustomFileDialog')
        apply_stylesheet(dialog)

        urls = []
        paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~")
        ]
        for path in paths:
            if os.path.exists(path):
                urls.append(QUrl.fromLocalFile(path))
        dialog.setSidebarUrls(urls)

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.additional_docs = selected
                doc_count = len(self.additional_docs)
                
                if doc_count == 1:
                    file_name = os.path.basename(self.additional_docs[0])
                    self.additional_docs_label.setText(file_name)
                else:
                    self.additional_docs_label.setText(f"{doc_count} documents selected")
                
                self.additional_docs_label.setStyleSheet("""
                    QLabel {
                        background-color: #1a4a47;
                        color: #4ecdc4;
                        padding: 10px 12px;
                        border-radius: 6px;
                        border: 1px solid #4ecdc4;
                        font-size: 14px;
                        font-weight: 500;
                        font-family: 'Asen Pro';
                    }
                """)

    def get_results(self):
        """Return transcript paths, additional docs, and custom prompt"""
        self.custom_prompt = self.prompt_text.toPlainText().strip()
        return self.transcript_paths, self.additional_docs, self.custom_prompt