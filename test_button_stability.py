#!/usr/bin/env python3
"""
Test script to verify button stability in Generated Steps tab.
This creates a minimal UI to test the EditableTaskListWidget.
"""

import sys
import os

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from generated_tasks import EditableTaskListWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Button Stability Test - Generated Steps")
        self.setGeometry(100, 100, 1200, 600)
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Create the task list widget
        self.task_list = EditableTaskListWidget()
        
        # Add some test tasks
        test_tasks = [
            "Open application and log in with credentials",
            "Navigate to the main dashboard",
            "Click on the reports section",
            "Filter data by date range",
            "Export results to CSV file"
        ]
        
        # Set the tasks
        self.task_list.set_tasks_data(test_tasks)
        
        layout.addWidget(self.task_list)
        self.setCentralWidget(main_widget)
        
        # Print instructions
        self.print_test_instructions()
    
    def print_test_instructions(self):
        print("\n" + "="*70)
        print("BUTTON STABILITY TEST INSTRUCTIONS")
        print("="*70)
        print("\nThis test validates that Edit, Insert, and Delete buttons remain")
        print("responsive after multiple operations and list rebuilds.\n")
        print("TEST PROCEDURE:")
        print("1. Click 'Edit' button on any step - editor should appear")
        print("2. Click tick button to finish editing")
        print("3. Click 'Insert Step After' button - new step should appear")
        print("4. Click 'Delete' button on any step - confirmation dialog should appear")
        print("5. Click 'Add Step' button at bottom - new step should be added")
        print("\nREPEAT Steps 1-5 multiple times (at least 5-10 times)")
        print("\nOBSERVATION:")
        print("✓ PASS: All buttons remain responsive and work consistently")
        print("✗ FAIL: Buttons become unresponsive or non-functional")
        print("\nCONSOLE LOGS:")
        print("- If 'is_rebuilding' flag is working, you'll see debug messages")
        print("- Look for '⚠️  Cannot...' messages if clicking during rebuild")
        print("="*70 + "\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
