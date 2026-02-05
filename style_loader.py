"""
Style Loader Utility for ABA Application
Centralized stylesheet loading and management
"""

import os
import sys
from PyQt5.QtWidgets import QApplication

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_stylesheet():
    """Load the centralized stylesheet from styles.qss file"""
    try:
        style_path = resource_path("styles/styles.qss")
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"Warning: Stylesheet file not found at {style_path}")
            return ""
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""

def apply_stylesheet(app_or_widget):
    """Apply the centralized stylesheet to the application or widget"""
    stylesheet = load_stylesheet()
    if stylesheet:
        app_or_widget.setStyleSheet(stylesheet)
        return True
    return False

def get_class_style(class_name):
    """Get specific class style from the stylesheet"""
    stylesheet = load_stylesheet()
    if not stylesheet:
        return ""
    
    # Extract specific class style (simplified implementation)
    lines = stylesheet.split('\n')
    in_class = False
    class_style = []
    
    for line in lines:
        line = line.strip()
        if line.startswith(f'.{class_name}') and '{' in line:
            in_class = True
            class_style.append(line)
        elif in_class:
            class_style.append(line)
            if '}' in line:
                break
    
    return '\n'.join(class_style)
