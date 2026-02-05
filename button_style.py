import sys
import pdb
# import subprocess_cmd
from styles.Icon import *
import threading
import selenium.webdriver.support.ui
import pandas,openpyxl,pyautogui,numpy,google.generativeai
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import StaleElementReferenceException
import style_loader

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import ast
import re
import win32gui
# import Desktop_Process

class ModernButton(QPushButton):
    """Custom button with hover effects and modern styling"""
    def __init__(self, text, color="#2196F3", hover_color="#1976D2"):
        super().__init__(text)
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        self.scale_factor = round(min(screen_width / 1920, screen_height / 1080), 2)
        self.color = color
        self.hover_color = hover_color
        
        # Set appropriate CSS class based on color
        if color == "#9C27B0":
            self.setProperty('class', 'BrowseButton')
        elif color == "#4CAF50":
            self.setProperty('class', 'ProcessButton')
        elif color == "#FF9800":
            self.setProperty('class', 'GenerateCodeButton')
        elif color == "#f44336":
            self.setProperty('class', 'ClearAllButton')
        elif color == "#17a2b8":
            self.setProperty('class', 'Refresh Steps Button')
        elif color == "#dc3545":
            self.setProperty('class', 'ClearBreakpointsButton')
        elif color == "#6f42c1":
            self.setProperty('class', 'CopyCodeButton')
        elif color == "#28a745":
            self.setProperty('class', 'SaveCodeButton')
        else:
            self.setProperty('class', 'ModernButton')
        
        style_loader.apply_stylesheet(self)
        
    def get_custom_button_style(self):
        """Only used when custom colors are specified"""
        return f"""
        QPushButton {{
            background-color: {self.color};
            color: white;
            border: none;
            padding: {int(12 * self.scale_factor)}px {int(24 * self.scale_factor)}px;
            border-radius: {int(8 * self.scale_factor)}px;
            font-weight: 600;
            font-size: {int(14 * self.scale_factor)}px;
            min-height: {int(20 * self.scale_factor)}px;
        }}
        QPushButton:hover {{
            background-color: {self.hover_color};
            transform: translateY(-{int(2 * self.scale_factor)}px);
        }}
        QPushButton:pressed {{
            background-color: {self.hover_color};
            transform: translateY(0px);
        }}
        QPushButton:disabled {{
            background-color: #CCCCCC;
            color: #666666;
        }}
        """

# Function to apply stylesheet to application
def apply_modern_button_styles(app):
    """Apply the centralized stylesheet to the application"""
    style_loader.apply_stylesheet(app)

