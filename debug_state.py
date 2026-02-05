import sys
import pdb
# import subprocess_cmd
from styles.Icon import *
import threading
import selenium.webdriver.support.ui
import pandas,openpyxl,pyautogui,numpy,google.generativeai
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import StaleElementReferenceException


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import ast
import re
import win32gui
# import Desktop_Process

class DebugState:
    """Manages the debugging state and execution control"""
    def __init__(self):
        self.is_debugging = False
        self.current_line = 0
        self.total_lines = 0
        self.code_lines = []
        self.breakpoints = set()
        self.radio_selections = set()  # Track radio button selections
        self.task_applications = {}  # Store selected applications for radio tasks
        self.execution_paused = False
        self.step_mode = False
        self.stop_requested = False
        self.continue_requested = False
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.current_task_index = -1
        self.debug_action = None  # 'stepinto', 'continue', 'stop'
        
    def reset(self):
        self.current_line = 0
        self.total_lines = 0
        self.code_lines = []
        self.breakpoints.clear()
        self.radio_selections.clear()
        self.task_applications.clear()
        self.execution_paused = False
        self.step_mode = False
        self.stop_requested = False
        self.continue_requested = False
        self.current_task_index = -1
        self.debug_action = None
