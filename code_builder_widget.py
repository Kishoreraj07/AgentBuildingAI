from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                             QTreeWidgetItem, QLabel, QSplitter, QFrame, QScrollArea,
                             QStyledItemDelegate, QStyle, QPushButton, QLineEdit, 
                             QComboBox, QTextEdit, QSpinBox)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QPen, QColor, QFont

class DraggableTreeWidget(QTreeWidget):
    """Custom QTreeWidget that supports drag operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDragDropMode(QTreeWidget.DragOnly)
        
    def startDrag(self, supportedActions):
        """Override to handle drag start"""
        item = self.currentItem()
        if item and item.parent():  # Only allow dragging child items (activities)
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.text(0))
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)
    
    def drawBranches(self, painter, rect, index):
        """Custom branch drawing with + and - symbols"""
        item = self.itemFromIndex(index)
        if item and item.childCount() > 0:
            # Draw custom + or - symbol
            painter.save()
            
            # Position for the symbol (very close to left edge)
            x_pos = rect.left() + 8
            y_center = rect.center().y()
            
            # Draw the + or - symbol with white color
            painter.setPen(QPen(QColor("#ffffff"), 2))
            
            # Draw horizontal line (for both + and -)
            painter.drawLine(
                x_pos - 5,
                y_center,
                x_pos + 5,
                y_center
            )
            
            # Draw vertical line for + only (when collapsed)
            if not item.isExpanded():
                painter.drawLine(
                    x_pos,
                    y_center - 5,
                    x_pos,
                    y_center + 5
                )
            
            painter.restore()


class ActivityWidget(QFrame):
    """Widget representing a single activity with controls"""
    
    activity_clicked = pyqtSignal(object)
    activity_removed = pyqtSignal(object)
    activity_commented = pyqtSignal(object, bool)
    add_activity_after = pyqtSignal(object)
    
    def __init__(self, activity_name, parent=None):
        super().__init__(parent)
        self.activity_name = activity_name
        self.is_commented = False
        self.activity_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the activity widget UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border: 0px solid #555555;
                border-radius: 8px;
                padding: 0px;
            }
            QFrame:hover {
                border-color: #666666;
            }
        """)
        
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        
        # Activity name (no radio indicator)
        self.name_label = QLabel(self.activity_name.strip())
        self.name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: normal;
                background: transparent;
                padding: 0px;
            }
        """)
        layout.addWidget(self.name_label, 1)
        
        # Control buttons container
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add button (+)
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4a9eff;
                border: none;
                border-radius: 0px;
                font-size: 30px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #6bb3ff;
            }
        """)
        self.add_btn.clicked.connect(self.on_add_clicked)
        buttons_layout.addWidget(self.add_btn)
        
        # Remove button (×)
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: 0px;
                font-size: 28px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #cccccc;
            }
        """)
        self.remove_btn.clicked.connect(self.on_remove_clicked)
        buttons_layout.addWidget(self.remove_btn)
        
        # Comment button (#)
        self.comment_btn = QPushButton("#")
        self.comment_btn.setFixedSize(24, 24)
        self.comment_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #50fa7b;
                border: none;
                border-radius: 0px;
                font-size: 24px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #70ff9b;
            }
        """)
        self.comment_btn.clicked.connect(self.on_comment_clicked)
        buttons_layout.addWidget(self.comment_btn)
        
        layout.addLayout(buttons_layout)
        
    def mousePressEvent(self, event):
        """Handle click on activity"""
        if event.button() == Qt.LeftButton:
            self.activity_clicked.emit(self)
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a3a3a;
                    border: 0px solid #3b9cde;
                    border-radius: 8px;
                    padding: 0px;
                }
            """)
    
    def on_add_clicked(self):
        """Handle add button click"""
        self.add_activity_after.emit(self)
    
    def on_remove_clicked(self):
        """Handle remove button click"""
        self.activity_removed.emit(self)
    
    def on_comment_clicked(self):
        """Handle comment button click"""
        self.is_commented = not self.is_commented
        if self.is_commented:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a3a3a;
                    border: 0px solid #555555;
                    border-radius: 8px;
                    padding: 0px;
                    opacity: 0.5;
                }
            """)
            self.name_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 14px;
                    font-weight: normal;
                    text-decoration: line-through;
                    background: transparent;
                    padding: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a3a3a;
                    border: 0px solid #555555;
                    border-radius: 8px;
                    padding: 0px;
                }
            """)
            self.name_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: normal;
                    background: transparent;
                    padding: 0px;
                }
            """)
        self.activity_commented.emit(self, self.is_commented)
    
    def deselect(self):
        """Deselect the activity"""
        self.setStyleSheet("""
            QFrame {
                background-color: #3a3a3a;
                border: 0px solid #555555;
                border-radius: 8px;
                padding: 0px;
            }
            QFrame:hover {
                border-color: #666666;
            }
        """)
    
    def set_activity_data(self, data):
        """Store activity configuration data"""
        self.activity_data = data


class DropArea(QFrame):
    """Custom drop area widget for the middle section"""
    
    activity_dropped = pyqtSignal(str)
    activity_selected = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
        """)
        
        # Layout for dropped activities
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Placeholder label
        self.placeholder = QLabel("Drag and drop activities here")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
                font-style: italic;
            }
        """)
        self.main_layout.addWidget(self.placeholder)
        self.main_layout.addStretch()
        
        self.activities = []
        self.selected_activity = None
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #252525;
                    border: 2px dashed #17a2b8;
                    border-radius: 8px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
        """)
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasText():
            activity_name = event.mimeData().text()
            self.add_activity(activity_name)
            event.acceptProposedAction()
            
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 2px dashed #555555;
                border-radius: 8px;
            }
        """)
    
    def add_activity(self, activity_name, index=None):
        """Add an activity to the drop area"""
        # Hide placeholder if this is the first activity
        if not self.activities:
            self.placeholder.hide()
        
        # Create activity widget
        activity_widget = ActivityWidget(activity_name)
        activity_widget.activity_clicked.connect(self.on_activity_clicked)
        activity_widget.activity_removed.connect(self.remove_activity)
        activity_widget.activity_commented.connect(self.on_activity_commented)
        activity_widget.add_activity_after.connect(self.on_add_activity_after)
        
        # Insert at specific index or at the end
        if index is None:
            insert_position = len(self.activities)
        else:
            insert_position = index
        
        self.main_layout.insertWidget(insert_position, activity_widget)
        self.activities.insert(insert_position, activity_widget)
        
        self.activity_dropped.emit(activity_name)
        
        # Auto-select the new activity
        self.on_activity_clicked(activity_widget)
    
    def remove_activity(self, activity_widget):
        """Remove an activity from the drop area"""
        if activity_widget in self.activities:
            self.activities.remove(activity_widget)
            self.main_layout.removeWidget(activity_widget)
            activity_widget.deleteLater()
            
            # Show placeholder if no activities left
            if not self.activities:
                self.placeholder.show()
            
            # Clear selection if removed activity was selected
            if self.selected_activity == activity_widget:
                self.selected_activity = None
                self.activity_selected.emit(None)
    
    def on_activity_clicked(self, activity_widget):
        """Handle activity selection"""
        # Deselect previous activity
        if self.selected_activity and self.selected_activity != activity_widget:
            self.selected_activity.deselect()
        
        self.selected_activity = activity_widget
        self.activity_selected.emit(activity_widget)
    
    def on_activity_commented(self, activity_widget, is_commented):
        """Handle activity comment toggle"""
        pass
    
    def on_add_activity_after(self, activity_widget):
        """Add new activity after the specified activity"""
        # Find the index of the current activity
        if activity_widget in self.activities:
            current_index = self.activities.index(activity_widget)
            # For now, add a placeholder - in real use, you'd open a dialog to select activity
            self.add_activity("New Activity", current_index + 1)


class CodeBuilderWidget(QWidget):
    """Main Code Builder Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # LEFT PANEL - Activity Tree
        left_panel = self.create_left_panel()
        
        # MIDDLE PANEL - Drop Area
        middle_panel = self.create_middle_panel()
        
        # RIGHT PANEL - Properties
        right_panel = self.create_right_panel()
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes (25%, 50%, 25%)
        splitter.setSizes([300, 600, 300])
        
        main_layout.addWidget(splitter)
    
    def create_left_panel(self):
        """Create left panel with activity categories"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #282727;
                border-right: 1px solid #3c3c3c;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("Activities")
        header.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(header)
        
        # Tree widget
        self.activity_tree = DraggableTreeWidget()
        self.activity_tree.setHeaderHidden(True)
        self.activity_tree.setIndentation(20)
        self.activity_tree.setAnimated(True)
        self.activity_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #282727;
                border: none;
                color: #ffffff;
                font-size: 13px;
                outline: none;
                show-decoration-selected: 0;
            }
            QTreeWidget::item {
                padding: 8px 12px;
                border: none;
                min-height: 20px;
                background-color: #363535;
                border-radius: 4px;
                margin: 2px 8px;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background-color: #404040;
            }
            QTreeWidget::item:selected {
                background-color: #404040;
                color: #ffffff;
                border: none;
                outline: none;
            }
            QTreeWidget::item:selected:active {
                background-color: #404040;
                border: none;
            }
            QTreeWidget::item:selected:!active {
                background-color: #404040;
                border: none;
            }
            QTreeWidget::item:focus {
                background-color: #404040;
                border: none;
                outline: none;
            }
            QTreeWidget::branch {
                background-color: transparent;
            }
        """)
        
        # Add categories and activities
        self.populate_activity_tree()
        
        layout.addWidget(self.activity_tree)
        
        return panel
    
    def populate_activity_tree(self):
        """Populate the activity tree with categories"""
        categories = {
            "Web": [
                "launch_url"
            ],
            "Citrix": [
                "Citrix Click", "Citrix Type", "Citrix Get Text",
                "Citrix Wait", "Citrix Scroll"
            ],
            "Desktop": [
                "Desktop Click", "Desktop Type", "Desktop Get Text",
                "Desktop Wait", "Desktop Scroll"
            ],
            "Excel": [
                "Open Workbook", "Close Workbook", "Read Cell",
                "Write Cell", "Read Range", "Write Range"
            ],
            "Pdf": [
                "Read PDF", "Extract Text", "Extract Tables",
                "Merge PDF", "Split PDF"
            ],
            "OCR": [
                "OCR Text", "OCR Image", "OCR Region",
                "OCR Document"
            ],
            "Queue": [
                "Add Queue Item", "Get Queue Item", "Set Transaction Status",
                "Get Transaction", "Bulk Add Queue Items"
            ]
        }
        
        for category, activities in categories.items():
            category_item = QTreeWidgetItem(self.activity_tree)
            category_item.setText(0, category)
            category_item.setExpanded(False)
            
            # Style category item - make it white and bold
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            category_item.setForeground(0, QColor("#ffffff"))
            
            for activity in activities:
                activity_item = QTreeWidgetItem(category_item)
                activity_item.setText(0, activity)
                # Set child items to white color
                activity_item.setForeground(0, QColor("#ffffff"))
    
    def create_middle_panel(self):
        """Create middle panel with drop area"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Scroll area for drop zone
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Drop area
        self.drop_area = DropArea()
        self.drop_area.activity_dropped.connect(self.on_activity_dropped)
        self.drop_area.activity_selected.connect(self.on_activity_selected)
        
        scroll_area.setWidget(self.drop_area)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_right_panel(self):
        """Create right panel for activity properties"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-left: 1px solid #3c3c3c;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Properties")
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(header)
        
        # Scroll area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Properties container
        self.properties_container = QWidget()
        self.properties_container.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                border-radius: 8px;
            }
        """)
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(15, 15, 15, 15)
        self.properties_layout.setSpacing(15)
        
        # Placeholder
        self.properties_placeholder = QLabel("Select an activity to view properties")
        self.properties_placeholder.setAlignment(Qt.AlignCenter)
        self.properties_placeholder.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 13px;
                padding: 20px;
            }
        """)
        self.properties_layout.addWidget(self.properties_placeholder)
        self.properties_layout.addStretch()
        
        scroll_area.setWidget(self.properties_container)
        layout.addWidget(scroll_area)
        
        return panel
    
    def on_activity_dropped(self, activity_name):
        """Handle activity drop event"""
        print(f"Activity dropped: {activity_name}")
    
    def on_activity_selected(self, activity_widget):
        """Handle activity selection - show properties in right panel"""
        # Clear previous properties
        while self.properties_layout.count() > 0:
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if activity_widget is None:
            # Show placeholder
            self.properties_placeholder = QLabel("Select an activity to view properties")
            self.properties_placeholder.setAlignment(Qt.AlignCenter)
            self.properties_placeholder.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 13px;
                    padding: 20px;
                }
            """)
            self.properties_layout.addWidget(self.properties_placeholder)
            self.properties_layout.addStretch()
            return
        
        # Get activity name and show relevant properties
        activity_name = activity_widget.activity_name.strip()
        
        # Activity title
        title_label = QLabel(activity_name.upper())
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: #2d2d30;
                border-radius: 4px;
            }
        """)
        self.properties_layout.addWidget(title_label)
        
        # Add properties based on activity type
        self.add_activity_properties(activity_name, activity_widget)
        
        self.properties_layout.addStretch()
    
    def add_activity_properties(self, activity_name, activity_widget):
        """Add property fields based on activity type"""
        
        # Define properties for different activities
        activity_properties = {
            "launch_url": [
                {"label": "Enter URL", "type": "text", "placeholder": "https://example.com"}
            ],
            "Message_box":[
                {"label": "Msg", "type": "text", "placeholder": "Enter message"}
            ]
        }
        
        # Get properties for this activity or use default
        properties = activity_properties.get(activity_name, [
            {"label": "Configuration", "type": "text", "placeholder": "Enter configuration"}
        ])
        
        # Create property fields
        for prop in properties:
            # Label
            label = QLabel(prop["label"])
            label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 5px 0px;
                }
            """)
            self.properties_layout.addWidget(label)
            
            # Input field based on type
            if prop.get("type") == "combo":
                field = QComboBox()
                field.addItems(prop["options"])
                field.setStyleSheet("""
                    QComboBox {
                        background-color: #1e1e1e;
                        color: white;
                        border: 2px solid #ffa500;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                    }
                    QComboBox:hover {
                        border-color: #ffb733;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #2d2d30;
                        color: white;
                        selection-background-color: #17a2b8;
                    }
                """)
            elif prop.get("type") == "number":
                field = QSpinBox()
                field.setMinimum(0)
                field.setMaximum(9999)
                field.setValue(prop.get("default", 0))
                field.setStyleSheet("""
                    QSpinBox {
                        background-color: #1e1e1e;
                        color: white;
                        border: 2px solid #ffa500;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                    }
                    QSpinBox:hover {
                        border-color: #ffb733;
                    }
                """)
            else:  # text
                field = QLineEdit()
                field.setPlaceholderText(prop.get("placeholder", ""))
                field.setStyleSheet("""
                    QLineEdit {
                        background-color: #1e1e1e;
                        color: white;
                        border: 2px solid #ffa500;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                    }
                    QLineEdit:hover {
                        border-color: #ffb733;
                    }
                    QLineEdit:focus {
                        border-color: #17a2b8;
                    }
                """)
            
            self.properties_layout.addWidget(field)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1391a5;
            }
            QPushButton:pressed {
                background-color: #0f7a8a;
            }
        """)
        save_btn.clicked.connect(lambda: self.save_activity_properties(activity_widget))
        self.properties_layout.addWidget(save_btn)
    
    def save_activity_properties(self, activity_widget):
        """Save the properties of the selected activity"""
        print(f"Saving properties for: {activity_widget.activity_name}")
        # Here you can collect all the property values and store them
        # This will be used later when generating the Python code