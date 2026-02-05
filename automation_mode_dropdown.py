import sys
import os
from PyQt5.QtWidgets import QComboBox, QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class AutomationModeDropdown(QWidget):
    """Custom dropdown widget for automation mode selection"""
    
    # Signal emitted when automation mode changes
    mode_changed = pyqtSignal(str)  # Emits: "web", "desktop", "native", "citrix"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = "web"  # Default mode
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dropdown UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Create the dropdown
        self.dropdown = QComboBox()
        self.dropdown.setMinimumWidth(180)
        self.dropdown.setMaximumHeight(32)
        
        # Add automation mode options
        self.add_dropdown_items()
        
        # Style the dropdown
        self.style_dropdown()
        
        # Connect signal
        self.dropdown.currentTextChanged.connect(self.on_mode_changed)
        
        layout.addWidget(self.dropdown)
        
    def add_dropdown_items(self):
        """Add items to dropdown with icons and text"""
        
        # Define automation modes with their icons
        modes = [
            ("Web", "web", resource_path("styles/Icon/web.png")),
            ("Desktop", "desktop", resource_path("styles/Icon/desktop.png")),
            ("Native", "native", resource_path("styles/Icon/native.png")),
            ("Citrix", "citrix", resource_path("styles/Icon/citrix.png"))
        ]
        
        for display_text, mode_key, icon_path in modes:
            # Create icon
            icon = QIcon()
            if os.path.exists(icon_path):
                # Load and process icon to ensure transparency
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    # Ensure transparent background
                    transparent_pixmap = QPixmap(pixmap.size())
                    transparent_pixmap.fill(Qt.transparent)
                    
                    painter = QPainter(transparent_pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    painter.drawPixmap(0, 0, pixmap)
                    painter.end()
                    
                    icon.addPixmap(transparent_pixmap)
                else:
                    # Fallback to default icon if file doesn't exist
                    icon = self.create_default_icon()
            else:
                # Create default icon if file doesn't exist
                icon = self.create_default_icon()
            
            # Add item with icon and text
            self.dropdown.addItem(icon, display_text)
            self.dropdown.setItemData(self.dropdown.count() - 1, mode_key)
    
    def create_default_icon(self):
        """Create a default icon when image file is not found"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.setBrush(Qt.transparent)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        return QIcon(pixmap)
    
    def style_dropdown(self):
        """Apply modern styling to the dropdown"""
        self.dropdown.setStyleSheet("""
            QComboBox {
                background-color: #1b1b1b;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                min-height: 20px;
            }
            
            QComboBox:hover {
                border: 1px solid #17a2b8;
                background-color: #2a2a2a;
            }
            
            QComboBox:focus {
                border: 1px solid #17a2b8;
                outline: none;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background: transparent;
            }
            
            QComboBox::down-arrow {
                image: url(""" + resource_path("styles/Icon/switch.png").replace("\\", "/") + """);
                width: 12px;
                height: 12px;
            }
            
            QComboBox::down-arrow:hover {
                image: url(""" + resource_path("styles/Icon/switch.png").replace("\\", "/") + """);
            }
            
            QComboBox QAbstractItemView {
                background-color: #1b1b1b;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 4px;
                outline: none;
                selection-background-color: #17a2b8;
                selection-color: #ffffff;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                margin: 1px;
                min-height: 20px;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #17a2b8;
                color: #ffffff;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #17a2b8;
                color: #ffffff;
            }
        """)
    
    def on_mode_changed(self, text):
        """Handle mode change"""
        # Get the mode key from item data
        current_index = self.dropdown.currentIndex()
        if current_index >= 0:
            mode_key = self.dropdown.itemData(current_index)
            if mode_key and mode_key != self.current_mode:
                self.current_mode = mode_key
                self.mode_changed.emit(mode_key)
                print(f"Automation mode changed to: {text} ({mode_key})")
    
    def get_current_mode(self):
        """Get the currently selected automation mode"""
        return self.current_mode
    
    def set_mode(self, mode_key):
        """Set the automation mode programmatically"""
        for i in range(self.dropdown.count()):
            if self.dropdown.itemData(i) == mode_key:
                self.dropdown.setCurrentIndex(i)
                break
    
    def get_mode_display_text(self):
        """Get the display text of current mode"""
        return self.dropdown.currentText()


class SwitchModeButton(QWidget):
    """Switch Mode button widget that shows current mode and opens dropdown"""
    
    # Signal emitted when mode changes
    mode_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = "web"
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the switch mode button UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Switch icon
        self.switch_icon = QLabel()
        self.switch_icon.setFixedSize(16, 16)
        self.switch_icon.setScaledContents(True)
        switch_pixmap = QPixmap(resource_path("styles/Icon/switchhh.png"))
        if not switch_pixmap.isNull():
            self.switch_icon.setPixmap(switch_pixmap)
        
        # Switch Mode text
        self.switch_text = QLabel("Switch Mode")
        self.switch_text.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
            font-weight: 500;
            padding: 2px;
        """)
        
        # Dropdown
        self.dropdown = AutomationModeDropdown()
        self.dropdown.mode_changed.connect(self.on_mode_changed)
        
        layout.addWidget(self.switch_icon)
        layout.addWidget(self.switch_text)
        layout.addWidget(self.dropdown)
        
    def on_mode_changed(self, mode_key):
        """Handle mode change from dropdown"""
        self.current_mode = mode_key
        self.mode_changed.emit(mode_key)
        
    def get_current_mode(self):
        """Get current automation mode"""
        return self.current_mode
        
    def set_mode(self, mode_key):
        """Set automation mode"""
        self.dropdown.set_mode(mode_key)
