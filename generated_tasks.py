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
import style_loader

def resource_path(relative_path):
    # When run from PyInstaller .exe, _MEIPASS is temp path to bundled files
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class EditableTaskListWidget(QListWidget):
    """Enhanced editable task list widget with full CRUD operations and drag-drop support"""
    
    # Signals for task updates
    tasks_updated = pyqtSignal(list)  # Emit when tasks are modified
    
    def __init__(self):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        self.scale_factor = round(min(screen_width / 1920, screen_height / 1080), 2)
        self.breakpoints = set()
        self.task_status = {}  # Track task status: 'pending', 'processing', 'completed'
        self.task_widgets = {}  # Store references to task widgets
        self.tasks_data = []  # Store actual task data
        self.app_info = []  # Store app info data for each task
        self.editing_item = None  # Track currently editing item
        self.is_rebuilding = False  # Flag to block interactions during rebuild
        
        # Enable drag and drop
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Enable multiple selection
        self.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Apply external stylesheet
        style_loader.apply_stylesheet(self)
        
        # Ensure proper sizing
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Setup context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect key press events
        self.keyPressEvent = self.handle_key_press
        
        # Add the initial "Add Step" button
        self.add_bottom_add_step_button()
    def clear(self):
        """Override clear to add button back after clearing"""
        super().clear()
        self.task_widgets.clear()
        # Only add the button if we're not about to call set_tasks_data or rebuild_task_list
        # The button will be added by rebuild_task_list() or add_bottom_add_step_button() when needed
    
    def add_task_with_breakpoint(self, task_text, task_index,task_len, app_info_text=None):
        """Add task item with simplified layout - no container wrapper"""
        # ------------------------------------------------------------------
        # Store task data
        # ------------------------------------------------------------------
        # try:
        #     if task_len < len(self.tasks_data):
        #         del self.tasks_data[task_len - 1:]
        # except:
        #     pass
        if task_index >= len(self.tasks_data):
            self.tasks_data.append(task_text)
        else:
            self.tasks_data[task_index] = task_text

        # Store app info data
        if task_index >= len(self.app_info):
            self.app_info.append(app_info_text or "")
        else:
            self.app_info[task_index] = app_info_text or ""

        # ------------------------------------------------------------------
        # QListWidgetItem + QWidget
        # ------------------------------------------------------------------
        item = QListWidgetItem()
        widget = QWidget()
        widget.setProperty('class', 'TaskWidget')

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # ------------------------------------------------------------------
        # 1. Checkbox
        # ------------------------------------------------------------------
        checkbox = QCheckBox()
        checkbox.setFixedSize(20, 20)
        layout.addWidget(checkbox)

        # ------------------------------------------------------------------
        # 2. Breakpoint button
        # ------------------------------------------------------------------
        breakpoint_btn = QPushButton()
        breakpoint_btn.setFixedSize(20, 20)
        breakpoint_btn.setIcon(QIcon(resource_path("styles/Icon/breakpoint_icon.png")))
        breakpoint_btn.setIconSize(QSize(16, 16))
        breakpoint_btn.setProperty('class', 'BreakpointButton')
        breakpoint_btn.setCheckable(True)
        style_loader.apply_stylesheet(breakpoint_btn)
        layout.addWidget(breakpoint_btn)

        # ------------------------------------------------------------------
        # 3. Conditional button (if any)
        # ------------------------------------------------------------------
        conditional_btn = None
        task_conditions = self.get_conditional_type_for_task(task_index)
        if task_conditions:
            conditional_btn = QPushButton()
            conditional_btn.setFixedSize(24, 16)
            conditional_btn.setProperty('class', 'ConditionalButton')
            condition_count = len(task_conditions)
            conditional_btn.setText(f"C{condition_count}")
            conditional_btn.setToolTip(f"{condition_count} conditional statement(s) - Click for details")
            conditional_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b35;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 1px 2px;
                }
                QPushButton:hover { background-color: #e55a2b; }
                QPushButton:pressed { background-color: #cc4e24; }
            """)
            conditional_btn.clicked.connect(lambda: self.show_conditional_popup(task_index))
            layout.addWidget(conditional_btn)

        # ------------------------------------------------------------------
        # 4. TASK LABEL – TRUNCATED WITH ELLIPSIS
        # ------------------------------------------------------------------
        task_label = QLabel()
        task_label.setWordWrap(True)                     # allow multi-line
        task_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        task_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ---- Font first (so stylesheet can’t override) ----
        label_font = QFont()
        label_font.setPointSize(10)
        task_label.setFont(label_font)

        # ---- Ellipsis stylesheet (Qt >= 5.15) ----
        task_label.setStyleSheet("""
            QLabel {
                font-size: 10pt !important;
                color: #ffffff;               /* match your dark theme */
                qproperty-textElideMode: ElideRight;   /* <-- ELLIPSIS */
            }
        """)

        # Set the (potentially very long) text
        task_label.setText(f"Step {task_index + 1}: {task_text}")

        # Optional: full text on hover
        task_label.setToolTip(task_text)

        layout.addWidget(task_label, 1)   # stretch to fill available space

        # ------------------------------------------------------------------
        # 5. Task editor (hidden until edit mode)
        # ------------------------------------------------------------------
        task_editor = QTextEdit()
        task_editor.setPlainText(task_text)
        task_editor.setProperty('class', 'TaskEditor')
        task_editor.setVisible(False)
        task_editor.setMinimumHeight(40)
        task_editor.setMaximumHeight(150)

        editor_font = QFont()
        editor_font.setPointSize(10)
        task_editor.setFont(editor_font)
        task_editor.setStyleSheet("""
            QTextEdit {
                font-size: 10pt !important;
                font-family: inherit;
            }
        """)
        layout.addWidget(task_editor, 1)

        # ------------------------------------------------------------------
        # 6. Action buttons (always visible)
        # ------------------------------------------------------------------
        edit_btn = QPushButton()
        edit_btn.setFixedSize(28, 28)
        edit_btn.setIcon(QIcon(resource_path("styles/Icon/edit.png")))
        edit_btn.setProperty('class', 'EditButton')
        layout.addWidget(edit_btn)

        tick_btn = QPushButton()
        tick_btn.setFixedSize(28, 28)
        tick_btn.setIcon(QIcon(resource_path("styles/Icon/tick.png")))
        tick_btn.setProperty('class', 'TickButton')
        tick_btn.setVisible(False)
        layout.addWidget(tick_btn)

        insert_btn = QPushButton()
        insert_btn.setIcon(QIcon(resource_path("styles/Icon/add_step.png")))
        insert_btn.setFixedSize(28, 28)
        insert_btn.setProperty('class', 'InsertButton')
        insert_btn.setToolTip("Insert new step after this")
        layout.addWidget(insert_btn)

        delete_btn = QPushButton()
        delete_btn.setIcon(QIcon(resource_path("styles/Icon/delete.png")))
        delete_btn.setFixedSize(28, 28)
        delete_btn.setProperty('class', 'DeleteButton')
        layout.addWidget(delete_btn)

        continue_btn = QPushButton("Continue")
        continue_btn.setFixedSize(80, 25)
        continue_btn.setProperty('class', 'ContinueButton')
        continue_btn.setVisible(False)
        layout.addWidget(continue_btn)

        # ------------------------------------------------------------------
        # 7. Widget styling (background)
        # ------------------------------------------------------------------
        widget.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

        # ------------------------------------------------------------------
        # 8. Store references on the widget
        # ------------------------------------------------------------------
        widget.task_index       = task_index
        widget.task_label       = task_label
        widget.task_editor      = task_editor
        widget.edit_btn         = edit_btn
        widget.tick_btn         = tick_btn
        widget.insert_btn       = insert_btn
        widget.delete_btn       = delete_btn
        widget.continue_btn     = continue_btn
        widget.breakpoint_btn   = breakpoint_btn
        widget.conditional_btn  = conditional_btn

        # ------------------------------------------------------------------
        # 9. Signal connections (use closures to capture current values)
        # ------------------------------------------------------------------
        # Create a helper to safely get widget by task index
        def create_edit_handler(idx):
            return lambda: self._safe_start_editing(idx)
        
        def create_tick_handler(idx):
            return lambda: self._safe_finish_editing(idx)
        
        def create_insert_handler(idx):
            return lambda: self.insert_task_after(idx)
        
        def create_delete_handler(idx):
            return lambda: self.delete_task(idx)
        
        def create_breakpoint_handler(idx):
            return lambda: self._safe_toggle_breakpoint(idx)
        
        def create_continue_handler(idx):
            return lambda: self.trigger_continue_debug(idx)
        
        # Connect with factory functions to ensure correct closure
        edit_btn.clicked.connect(create_edit_handler(task_index))
        tick_btn.clicked.connect(create_tick_handler(task_index))
        insert_btn.clicked.connect(create_insert_handler(task_index))
        delete_btn.clicked.connect(create_delete_handler(task_index))
        breakpoint_btn.clicked.connect(create_breakpoint_handler(task_index))
        continue_btn.clicked.connect(create_continue_handler(task_index))

        # ------------------------------------------------------------------
        # 10. Store widget dict for later access
        # ------------------------------------------------------------------
        self.task_widgets[task_index] = {
            'button'        : breakpoint_btn,
            'label'         : task_label,
            'widget'        : widget,
            'continue_btn'  : continue_btn,
            'edit_btn'      : edit_btn,
            'tick_btn'      : tick_btn,
            'insert_btn'    : insert_btn,
            'delete_btn'    : delete_btn,
            'editor'        : task_editor,
            'conditional_btn': conditional_btn
        }

        # ------------------------------------------------------------------
        # 11. Initialise status
        # ------------------------------------------------------------------
        self.task_status[task_index] = 'pending'

        # ------------------------------------------------------------------
        # 12. Dynamic height calculation (keeps multi-line text correct)
        # ------------------------------------------------------------------
        list_width = self.viewport().width() if self.viewport().width() > 0 else 800
        # Buttons + margins ≈ 308 px (checkbox 20 + bp 20 + cond 24 + edit 28 + insert 28 + delete 28 + continue 80 + spacing)
        available_width = max(list_width - 308, 500)

        task_label.setMaximumWidth(available_width)
        widget.adjustSize()
        label_height = task_label.sizeHint().height()
        task_label.setMaximumWidth(16777215)               # reset to unlimited

        item_height = max(label_height + 16, 36)           # 16 px padding, min 36 px
        item.setSizeHint(QSize(list_width, item_height))

        # ------------------------------------------------------------------
        # 13. Add to list
        # ------------------------------------------------------------------
        self.addItem(item)
        self.setItemWidget(item, widget)
    def start_editing(self, task_index, widget):
        """Start editing a task"""
        # Prevent action if list is rebuilding
        if self.is_rebuilding:
            print(f"⚠️  Cannot start editing while rebuilding list")
            return
            
        if self.editing_item is not None:
            return  # Already editing another item
            
        self.editing_item = task_index
        self.store_label_properties(task_index, widget)
        
        # Hide label, show editor
        widget.task_label.setVisible(False)
        widget.task_editor.setVisible(True)
        widget.task_editor.setFocus()
        
        # Set the editor font to match the label's font
        editor_font = widget.task_label.font()
        widget.task_editor.setFont(editor_font)
        
        # Hide edit button and action buttons (insert, delete), show only tick button
        widget.edit_btn.setVisible(False)
        widget.insert_btn.setVisible(False)
        widget.delete_btn.setVisible(False)
        widget.tick_btn.setVisible(True)
        
        # Disable other edit buttons
        for idx, w_refs in self.task_widgets.items():
            if idx != task_index:
                w_refs['edit_btn'].setEnabled(False)
                w_refs['insert_btn'].setEnabled(False)
                w_refs['delete_btn'].setEnabled(False)
    
    def finish_editing(self, task_index, widget):
        """Finish editing a task"""
        if self.editing_item != task_index:
            return
            
        # Get new text
        new_text = widget.task_editor.toPlainText().strip()
        
        # Check if this was a newly inserted task with placeholder
        is_new_task = (self.tasks_data[task_index] == "Enter new step description here...")
        
        if not new_text:
            if is_new_task:
                # If it's a new task and user left it empty, remove it
                self.cancel_insert_task(task_index)
                return
            else:
                # Existing task cannot be empty
                QMessageBox.warning(self, "Warning", "Task cannot be empty!")
                return
            
        # Update task data
        self.tasks_data[task_index] = new_text
        
        # Update label
        widget.task_label.setText(f"Step {task_index + 1}: {new_text}")
        self.restore_label_properties(task_index, widget)
        # Show label, hide editor
        widget.task_label.setVisible(True)
        widget.task_editor.setVisible(False)
        
        # Show all action buttons again, hide tick button
        widget.edit_btn.setVisible(True)
        widget.insert_btn.setVisible(True)
        widget.delete_btn.setVisible(True)
        widget.tick_btn.setVisible(False)
        
        # Re-enable other edit buttons and action buttons
        for idx, w_refs in self.task_widgets.items():
            w_refs['edit_btn'].setEnabled(True)
            w_refs['insert_btn'].setEnabled(True)
            w_refs['delete_btn'].setEnabled(True)
            
        self.editing_item = None
        
        # Emit signal that tasks were updated
        self.tasks_updated.emit(self.tasks_data.copy())
    
    def _safe_start_editing(self, task_index):
        """Safely start editing by getting current widget reference"""
        if task_index in self.task_widgets:
            widget = self.task_widgets[task_index]['widget']
            self.start_editing(task_index, widget)
        else:
            print(f"⚠️  Widget not found for task {task_index}")
    
    def _safe_finish_editing(self, task_index):
        """Safely finish editing by getting current widget reference"""
        if task_index in self.task_widgets:
            widget = self.task_widgets[task_index]['widget']
            self.finish_editing(task_index, widget)
        else:
            print(f"⚠️  Widget not found for task {task_index}")
    
    def _safe_toggle_breakpoint(self, task_index):
        """Safely toggle breakpoint by getting current widget references"""
        if task_index in self.task_widgets:
            widget_refs = self.task_widgets[task_index]
            breakpoint_btn = widget_refs['button']
            task_label = widget_refs['label']
            self.toggle_breakpoint_simple(task_index, breakpoint_btn, task_label)
        else:
            print(f"⚠️  Widget not found for task {task_index}")
    
    
    def cancel_insert_task(self, task_index):
        """Cancel inserting a new task and remove it"""
        # Store current scroll position BEFORE rebuild
        scroll_position = self.verticalScrollBar().value()
        
        # Remove the placeholder task
        if task_index < len(self.tasks_data):
            self.tasks_data.pop(task_index)
            self.app_info.pop(task_index)
            
        # Update breakpoint indices (shift back up)
        new_breakpoints = set()
        for bp in self.breakpoints:
            if bp > task_index:
                new_breakpoints.add(bp - 1)
            elif bp != task_index:
                new_breakpoints.add(bp)
        self.breakpoints = new_breakpoints
            
        # Update task status indices (shift back up)
        new_task_status = {}
        for idx, status in self.task_status.items():
            if idx > task_index:
                new_task_status[idx - 1] = status
            elif idx != task_index:
                new_task_status[idx] = status
        self.task_status = new_task_status
            
        # Reset editing state
        self.editing_item = None
            
        # Rebuild the list
        self.rebuild_task_list()
        
        # Restore scroll position AFTER rebuild
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(scroll_position))
            
        # Emit signal that tasks were updated
        self.tasks_updated.emit(self.tasks_data.copy())
    
    def store_label_properties(self, task_index, widget):
        """Store original label properties before editing"""
        if task_index not in self.task_widgets:
            return
            
        # Store font and other properties
        label = widget.task_label
        self.task_widgets[task_index]['original_font'] = label.font()
        self.task_widgets[task_index]['original_style'] = label.styleSheet()
        self.task_widgets[task_index]['original_properties'] = {
            'property_class': label.property('class'),
            'breakpoint': label.property('breakpoint')
        }

    def restore_label_properties(self, task_index, widget):
        """Restore original label properties after editing"""
        if task_index not in self.task_widgets:
            return
            
        label = widget.task_label
        stored = self.task_widgets[task_index]
        
        # Restore font FIRST (before any stylesheet)
        if 'original_font' in stored:
            label.setFont(stored['original_font'])
        
        # Restore other properties
        if 'original_properties' in stored:
            props = stored['original_properties']
            if props.get('property_class'):
                label.setProperty('class', props['property_class'])
            if props.get('breakpoint') is not None:
                label.setProperty('breakpoint', props['breakpoint'])
        
        # Force update of stylesheet after property restoration
        style_loader.apply_stylesheet(label)
        
        # Ensure font size is explicitly set again
        font = label.font()
        font.setPointSize(10)  # Match your original size
        label.setFont(font)
    # def delete_task(self, task_index):
    #     """Delete a task"""
    #     reply = QMessageBox.question(self, 'Delete Task', 
    #                                f'Are you sure you want to delete Step {task_index + 1}?',
    #                                QMessageBox.Yes | QMessageBox.No, 
    #                                QMessageBox.No)
        
    #     if reply == QMessageBox.Yes:
    #         self.delete_task_at_index(task_index)


    def delete_task(self, task_index):
        """Delete a task"""
        # Prevent action if list is rebuilding
        if self.is_rebuilding:
            print(f"⚠️  Cannot delete task while rebuilding list")
            return
            
        reply = self.show_delete_confirmation(task_index)
        
        if reply:
            self.delete_task_at_index(task_index)

    def show_delete_confirmation(self, task_index):
        """Show custom confirmation dialog for deleting a task"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setFixedSize(500, 280)
        dialog.setModal(True)
        dialog.setStyleSheet("")
        
        container = QWidget(dialog)
        container.setGeometry(0, 0, 500, 280)
        container.setObjectName("deleteContainer")
        container.setStyleSheet("QWidget#deleteContainer { background-color: #414141 !important; border: none !important; border-radius: 15px !important; }")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 25)
        layout.setSpacing(0)

        # Title bar
        title_container = QWidget()
        title_container.setFixedHeight(60)
        title_container.setStyleSheet("QWidget { background: #333333 !important; border-radius: 20px 20px 0px 0px !important; border: none !important; }")
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        title_label = QLabel("Delete Task")
        title_label.setStyleSheet("QLabel { color: #ffffff !important; font-family: 'Asen Pro' !important; font-weight: bold !important; font-size: 16px !important; background: transparent !important; border: none !important; }")
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: transparent !important; border: none !important; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1) !important; border-radius: 12px !important; }")
        
        def paintEvent(event):
            painter = QPainter(close_btn)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2)
            painter.setPen(pen)
            margin = 6
            painter.drawLine(margin, margin, 18, 18)
            painter.drawLine(18, margin, margin, 18)
        close_btn.paintEvent = paintEvent
        
        dialog.result_value = False
        
        def on_close():
            dialog.result_value = False
            dialog.reject()
        
        close_btn.clicked.connect(on_close)
        title_layout.addWidget(close_btn)
        layout.addWidget(title_container)
        layout.addSpacing(40)
        
        # Message
        msg_label = QLabel(f"Are you sure you want to delete Step {task_index + 1}?")
        msg_label.setStyleSheet("QLabel { color: #FFFFFF !important; font-family: 'Asen Pro' !important; font-weight: 400 !important; font-size: 16px !important; text-align: center !important; background: transparent !important; border: none !important; padding: 10px 40px !important; }")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)
        
        layout.addSpacing(40)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        def on_no():
            dialog.result_value = False
            dialog.reject()
        
        def on_yes():
            dialog.result_value = True
            dialog.accept()
        
        no_btn = QPushButton("❌ No")
        no_btn.setFixedSize(120, 40)
        no_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        no_btn.clicked.connect(on_no)
        
        yes_btn = QPushButton("✅ Yes")
        yes_btn.setFixedSize(120, 40)
        yes_btn.setStyleSheet("QPushButton { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #008AB3, stop: 1 #005B7F) !important; color: #FFFFFF !important; border: none !important; border-radius: 10px !important; font-family: 'Asen Pro' !important; font-weight: 600 !important; font-size: 16px !important; } QPushButton:hover { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #0099CC, stop: 1 #006699) !important; }")
        yes_btn.clicked.connect(on_yes)
        
        button_layout.addStretch()
        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec_()
        return dialog.result_value
    
    def delete_task_at_index(self, task_index):
        """Actually delete the task at given index"""
        if 0 <= task_index < len(self.tasks_data):
            # Store current scroll position BEFORE rebuild
            scroll_position = self.verticalScrollBar().value()
            
            # Remove from data
            self.tasks_data.pop(task_index)
            
            # Remove from app_info if present
            if task_index < len(self.app_info):
                self.app_info.pop(task_index)
            
            # Remove from breakpoints if present
            if task_index in self.breakpoints:
                self.breakpoints.remove(task_index)
            
            # Update breakpoint indices (shift down)
            new_breakpoints = set()
            for bp in self.breakpoints:
                if bp > task_index:
                    new_breakpoints.add(bp - 1)
                else:
                    new_breakpoints.add(bp)
            self.breakpoints = new_breakpoints
            
            # Rebuild the entire list
            self.rebuild_task_list()
            
            # Restore scroll position AFTER rebuild
            QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(scroll_position))
            
            # Emit signal that tasks were updated
            self.tasks_updated.emit(self.tasks_data.copy()) 
    def delete_selected_tasks(self):
        """Delete all selected tasks"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        reply = QMessageBox.question(self, 'Delete Tasks', 
                                   f'Are you sure you want to delete {len(selected_items)} selected task(s)?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Get indices of selected items
            indices_to_delete = []
            for item in selected_items:
                widget = self.itemWidget(item)
                if widget and hasattr(widget, 'task_index'):
                    indices_to_delete.append(widget.task_index)
            
            # Sort in reverse order to delete from end to beginning
            indices_to_delete.sort(reverse=True)
            
            # Delete each task
            for index in indices_to_delete:
                self.delete_task_at_index(index)
    
    def insert_task_after(self, after_index):
        """Insert a new task after the given index with inline editing"""
        # Prevent action if list is rebuilding
        if self.is_rebuilding:
            print(f"⚠️  Cannot insert task while rebuilding list")
            return
            
        if self.editing_item is not None:
            return  # Already editing another item
        
        # Store current scroll position BEFORE rebuild
        scroll_position = self.verticalScrollBar().value()
        
        # Insert placeholder text into data
        placeholder_text = "Enter new step description here..."
        self.tasks_data.insert(after_index + 1, placeholder_text)
        
        # Insert empty app_info for new task
        self.app_info.insert(after_index + 1, "")
        
        # Update breakpoint indices (shift down for items after insertion point)
        new_breakpoints = set()
        for bp in self.breakpoints:
            if bp > after_index:
                new_breakpoints.add(bp + 1)
            else:
                new_breakpoints.add(bp)
        self.breakpoints = new_breakpoints
        
        # Update task status indices (shift down)
        new_task_status = {}
        for idx, status in self.task_status.items():
            if idx > after_index:
                new_task_status[idx + 1] = status
            else:
                new_task_status[idx] = status
        # Add pending status for new task
        new_task_status[after_index + 1] = 'pending'
        self.task_status = new_task_status
        
        # Rebuild the entire list
        self.rebuild_task_list()
        
        # Restore scroll position AFTER rebuild
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(scroll_position))
        
        # Start editing the newly inserted task
        new_task_index = after_index + 1
        if new_task_index in self.task_widgets:
            widget = self.task_widgets[new_task_index]['widget']
            # Clear the placeholder text in editor
            widget.task_editor.setPlainText("")
            # Start editing mode
            self.start_editing(new_task_index, widget)
        
        # Emit signal that tasks were updated
        self.tasks_updated.emit(self.tasks_data.copy())



    def rebuild_task_list(self):
        """Rebuild the entire task list from tasks_data"""
        # Mark that we're rebuilding
        self.is_rebuilding = True
        
        # Store current selections AND task status
        old_breakpoints = self.breakpoints.copy()
        old_task_status = self.task_status.copy()  # Preserve task status!
        
        print(f"🔄 REBUILD: Preserving {len(old_task_status)} steps statuses")
        for idx, status in old_task_status.items():
            print(f"🔄 REBUILD: Step {idx} has status '{status}'")
        
        # Clear current items but NOT task_status
        self.clear()
        self.task_widgets.clear()
        # DO NOT clear task_status - we want to preserve it!
        
        # Ensure app_info has same length as tasks_data
        while len(self.app_info) < len(self.tasks_data):
            self.app_info.append("")
        
        # Recreate all items with app_info
        for i, task_text in enumerate(self.tasks_data):
            app_info_text = self.app_info[i] if i < len(self.app_info) else ""
            self.add_task_with_breakpoint(task_text, i, len(self.tasks_data), app_info_text)
        
        # Restore selections
        self.breakpoints = old_breakpoints
        
        # Update UI to reflect restored selections
        for task_index in self.breakpoints:
            if task_index in self.task_widgets:
                widget_refs = self.task_widgets[task_index]
                button = widget_refs['button']
                label = widget_refs['label']
                button.setProperty('class', 'BreakpointButton')
                label.setProperty('class', 'TaskLabelBreakpoint')
        
        
        # Restore task status colors after rebuilding
        print(f"🔄 REBUILD: Restoring task status colors...")
        for task_idx, status in old_task_status.items():
            if task_idx < len(self.tasks_data):  # Only restore if task still exists
                self.task_status[task_idx] = status
                self.update_task_status(task_idx, status)
                print(f"🔄 REBUILD: Restored Step {task_idx} to status '{status}'")
        
        # Add the "Add Step" button at the bottom
        self.add_bottom_add_step_button()
        
        # Mark rebuild as complete
        self.is_rebuilding = False
    
    def ensure_add_button_at_end(self):
        """Ensure the add button is at the end of the list"""
        # Remove existing add button if present
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and not hasattr(widget, 'task_index'):
                self.takeItem(i)
                break
        
        # Add the button at the end
        self.add_bottom_add_step_button()
    
    def add_bottom_add_step_button(self):
        """Add a horizontal 'Add Step' button at the bottom of the list"""
        item = QListWidgetItem()
        widget = QWidget()
        
        # Create horizontal layout
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)
        
        # Create the add step button
        add_btn = QPushButton()
        add_btn.setIcon(QIcon(resource_path("styles/Icon/add_step.png")))
        add_btn.setIconSize(QSize(40, 40))  # Larger icon size
        add_btn.setFixedHeight(60)
        add_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_btn.setToolTip("Add new step at the end")
        add_btn.setCursor(Qt.PointingHandCursor)
        
        # Style the button with cyan border
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                border: 2px solid #4ECDC4;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Asen Pro';
                font-size: 14px;
                font-weight: bold;
                color: #4ECDC4;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                border: 2px solid #17a2b8;
                color: #17a2b8;
            }
            QPushButton:pressed {
                background-color: #0d0d0d;
                border: 2px solid #138496;
            }
        """)
        
        # Connect to insert function (insert after last task)
        add_btn.clicked.connect(self.add_step_at_end)
        
        layout.addWidget(add_btn)
        
        # Set widget styling
        widget.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # Set item height
        item.setSizeHint(QSize(self.viewport().width(), 76))
        
        self.addItem(item)
        self.setItemWidget(item, widget)
    
    def add_step_at_end(self):
        """Add a new step at the end of the list"""
        # Prevent action if list is rebuilding
        if self.is_rebuilding:
            print(f"⚠️  Cannot add step while rebuilding list")
            return
            
        if self.editing_item is not None:
            return  # Already editing another item
        
        # Get the last task index
        last_index = len(self.tasks_data) - 1
        
        # Use the existing insert_task_after method, but defer to the event loop
        # so the UI stays responsive and avoids momentary blocking when rebuilding.
        QTimer.singleShot(0, lambda: self.insert_task_after(last_index))
    
    def show_context_menu(self, position):
        """Show context menu on right click"""
        item = self.itemAt(position)
        if not item:
            return
            
        widget = self.itemWidget(item)
        if not widget or not hasattr(widget, 'task_index'):
            return
            
        task_index = widget.task_index
        
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        # Edit action
        edit_action = menu.addAction("✏️ Edit Task")
        edit_action.triggered.connect(lambda: self.start_editing(task_index, widget))
        
        # Insert action
        insert_action = menu.addAction("➕ Insert Task After")
        insert_action.triggered.connect(lambda: self.insert_task_after(task_index))
        
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete Task")
        delete_action.triggered.connect(lambda: self.delete_task(task_index))
        
        menu.exec_(self.mapToGlobal(position))
    
    def handle_key_press(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Delete:
            self.delete_selected_tasks()
        elif event.key() == Qt.Key_F2:
            # Edit selected task
            selected_items = self.selectedItems()
            if len(selected_items) == 1:
                widget = self.itemWidget(selected_items[0])
                if widget and hasattr(widget, 'task_index'):
                    self.start_editing(widget.task_index, widget)
        else:
            # Call parent implementation for other keys
            super().keyPressEvent(event)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.tasks_data = []
        self.app_info = []
        self.task_widgets = {}
        self.task_status = {}
        self.breakpoints = set()
        self.parent_window = parent
        self.conditional_info = {}  # Store conditional logic information
        self.editing_item = None  # Track which item is currently being edited

        # Apply black background styling directly
        self.setStyleSheet("""
            QListWidget {
                background-color: #000000;
                font-family: 'Asen Pro'; 
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QListWidget::item {
                background-color: #000000;
                font-family: 'Asen Pro'; 
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)

    def dropEvent(self, event):
        """Handle drop events for drag and drop reordering"""
        super().dropEvent(event)

        # After drop, rebuild tasks_data based on new order
        new_tasks_data = []
        new_breakpoints = set()

        new_app_info = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and hasattr(widget, 'task_index'):
                old_index = widget.task_index
                new_tasks_data.append(self.tasks_data[old_index])

                # Update app_info
                if old_index < len(self.app_info):
                    new_app_info.append(self.app_info[old_index])
                else:
                    new_app_info.append("")

                # Update breakpoints
                if old_index in self.breakpoints:
                    new_breakpoints.add(i)

        # Update data, app_info, and breakpoints
        self.tasks_data = new_tasks_data
        self.app_info = new_app_info
        self.breakpoints = new_breakpoints

        # Rebuild to update indices
        self.rebuild_task_list()

        # Emit signal that tasks were updated
        self.tasks_updated.emit(self.tasks_data.copy())

    def set_tasks_data(self, tasks_data, task_events=None, app_info=None):
        """Set tasks data and rebuild list with optional task events for auto-selection and app_info"""
        self.tasks_data = tasks_data.copy()
        
        # Set app_info data if provided
        if app_info:
            self.app_info = app_info.copy()
        else:
            # Initialize empty app_info for all tasks
            self.app_info = [""] * len(self.tasks_data)
            
        self.rebuild_task_list()
        
        # Auto-select radio buttons for Desktop tasks if task_events provided
        if task_events:
            print(f"🔵 TASK EVENTS: Received {len(task_events)} steps events for auto-selection")
            self.auto_select_desktop_tasks(task_events)
            
    def set_task_events(self, task_events):
        """Set task events data and auto-select Desktop tasks"""
        if task_events and len(task_events) == len(self.tasks_data):
            print(f"🔵 TASK EVENTS: Received {len(task_events)} steps events for auto-selection")
            self.auto_select_desktop_tasks(task_events)
        else:
            print(f"⚠️ TASK EVENTS: Mismatch - {len(task_events) if task_events else 0} events vs {len(self.tasks_data)} steps")

    def set_app_info(self, app_info):
        """Set the app info for all tasks"""
        self.app_info = app_info
        print(f"📱 Task List: Updated app info for {len(app_info)} steps")

    def set_conditional_info(self, conditional_info):
        """Set the conditional logic information for tasks"""
        self.conditional_info = conditional_info
        print(f"🔀 Task List: Updated conditional info: {conditional_info}")

    def get_conditional_type_for_task(self, task_index):
        """Get all conditional types and details for a specific task, sorted by order"""
        task_num = task_index + 1  # Convert to 1-based indexing
        task_conditions = []

        for condition_type, conditions in self.conditional_info.items():
            for condition in conditions:
                task_range = condition.get('task_no', '')
                if self.is_task_in_range(task_num, task_range):
                    order = condition.get('order', 999)  # Default high order if not specified
                    task_conditions.append((order, condition_type, condition))
        
        # Sort by order and return all conditions
        task_conditions.sort(key=lambda x: x[0])
        return task_conditions

    def is_task_in_range(self, task_num, task_range):
        """Check if a task number is within the specified range"""
        if not task_range:
            return False

        try:
            if ' to ' in task_range:
                start, end = task_range.split(' to ')
                return int(start) <= task_num <= int(end)
            else:
                return task_num == int(task_range)
        except (ValueError, AttributeError):
            return False

    def show_conditional_popup(self, task_index):
        """Show conditional information popup for a task"""
        print(f" DEBUG: Button clicked for step {task_index}")
        print(f" DEBUG: Conditional info available: {bool(self.conditional_info)}")
        print(f" DEBUG: Conditional info content: {self.conditional_info}")
        
        try:
            from conditional_info_popup import ConditionalInfoPopup
            
            print(f" DEBUG: Creating popup for step {task_index}")
            # Create and show the popup
            popup = ConditionalInfoPopup(task_index, self.conditional_info, self)
            print(f" DEBUG: Popup created successfully")
            
            # Store reference to prevent garbage collection
            self.current_popup = popup
            
            # Position popup near the main window
            if self.parent():
                main_window = self.parent()
                popup.move(main_window.x() + 100, main_window.y() + 100)
            
            # Force show with multiple methods
            popup.setVisible(True)
            popup.show()
            popup.raise_()
            popup.activateWindow()
            popup.setFocus()
            print(f" DEBUG: Popup should be visible now at position {popup.pos()}")
            
        except Exception as e:
            print(f"❌ ERROR: Error showing conditional popup: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to simple message box
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Conditional Logic")
            msg.setText(f"Error displaying conditional information: {str(e)}")
            msg.exec_()

    def set_app_info_data(self, app_info):
        """Set app info data for each task"""
        if app_info:
            self.app_info = app_info.copy()
            # Ensure app_info has same length as tasks_data
            while len(self.app_info) < len(self.tasks_data):
                self.app_info.append("")

            # Update existing widgets with app info
            for i, app_text in enumerate(self.app_info):
                if i in self.task_widgets:
                    widget_refs = self.task_widgets[i]
                    app_info_label = widget_refs.get('app_info_label')
                    if app_info_label:
                        # Clean app info text - remove 'App :' prefix
                        clean_app_text = app_text.replace('App :', '').strip() if app_text else ""
                        app_info_label.setText(clean_app_text)
                        # Update styling based on app type
                        self.update_app_info_styling(app_info_label, clean_app_text)
            
            print(f"📱 APP INFO: Set app info for {len(self.app_info)} steps")
    
    def update_app_info_styling(self, app_info_label, app_text):
        """Update app info label styling based on app type"""
        if "Chrome" in app_text or "Browser" in app_text or "Web" in app_text:
            # Web task - bright white styling for better visibility
            app_info_label.setProperty('class', 'AppInfoLabelWeb')
        else:
            # Desktop task - bright blue styling for better visibility
            app_info_label.setProperty('class', 'AppInfoLabelDesktop')
        
    def toggle_breakpoint_simple(self, task_index, button, label):
        """Toggle breakpoint with enhanced text styling"""
        if task_index in self.breakpoints:
            # Remove breakpoint - normal styling
            self.breakpoints.discard(task_index)
            button.setChecked(False)
            
            label.setProperty('breakpoint', 'false')
            label.setStyleSheet("color: #ffffff; font-weight: normal;")
            
        else:
            # Add breakpoint - red styling
            self.breakpoints.add(task_index)
            button.setChecked(True)
            
            label.setProperty('breakpoint', 'true')
            label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    def get_breakpoints(self):
        return self.breakpoints
    
    def clear_breakpoints(self):
        self.breakpoints.clear()
    
    def update_task_status(self, task_index, status):
        """Update task status and color based on processing state"""
        try:
            if task_index not in self.task_widgets:
                return
                
            self.task_status[task_index] = status
            widget_refs = self.task_widgets[task_index]
            button = widget_refs['button']
            label = widget_refs['label']
            
            # Check if task has breakpoint for special red coloring
            is_breakpoint = task_index in self.breakpoints
            
            if status == 'processing':
                if is_breakpoint:
                    # Red color for breakpointed tasks during processing
                    color = '#ff4444'
                    button.setProperty('class', 'BreakpointButton')
                else:
                    # Orange color for all processing tasks
                    color = '#ff8c00'
                    button.setProperty('class', 'BreakpointButton')
            elif status == 'completed':
                if is_breakpoint:
                    # Red color for breakpointed tasks even after completion
                    color = '#ff4444'
                    button.setProperty('class', 'BreakpointButton')
                else:
                    # Green color for all completed tasks
                    color = '#00ff00'
                    button.setProperty('class', 'BreakpointButton')
            elif status == 'exception':
                # Red color for tasks with exceptions
                color = '#ff0000'
                button.setProperty('class', 'BreakpointButton')
            else:  # pending or default
                if is_breakpoint:
                    # Red color for breakpointed tasks
                    color = '#ff4444'
                    button.setProperty('class', 'BreakpointButton')
                else:
                    # White color for pending tasks
                    color = '#ffffff'
                    button.setProperty('class', 'BreakpointButton')
            
            # Apply stylesheet to button
            style_loader.apply_stylesheet(button)
            
            # Update label styling
            label.setProperty('class', f'TaskLabel{status.capitalize()}')
            style_loader.apply_stylesheet(label)
        except RuntimeError:
            return
        except Exception as e:
            print(f"Error updating task status for step {task_index}: {e}")
            return
    
    def set_task_processing(self, task_index):
        """Mark task as currently processing (orange or red if breakpointed)"""
        self.update_task_status(task_index, 'processing')
    
    def set_task_completed(self, task_index):
        """Mark task as completed (green or red if breakpointed)"""
        self.update_task_status(task_index, 'completed')
    
    def set_task_pending(self, task_index):
        """Mark task as pending (white or red if breakpointed)"""
        self.update_task_status(task_index, 'pending')
    
    def show_continue_button(self, task_index):
        """Show the inline continue button for a breakpointed task"""
        if task_index in self.task_widgets:
            continue_btn = self.task_widgets[task_index].get('continue_btn')
            if continue_btn:
                continue_btn.setVisible(True)
                print(f"🎮 UI: Showing continue button for step {task_index}")
    
    def hide_continue_button(self, task_index):
        """Hide the inline continue button for a task"""
        if task_index in self.task_widgets:
            continue_btn = self.task_widgets[task_index].get('continue_btn')
            if continue_btn:
                try:
                    continue_btn.setVisible(False)
                except RuntimeError:
                    # Button has been deleted, remove from widgets dict
                    if 'continue_btn' in self.task_widgets[task_index]:
                        del self.task_widgets[task_index]['continue_btn']
                print(f"🎮 UI: Hiding continue button for step {task_index}")
    
    def hide_all_continue_buttons(self):
        """Hide all inline continue buttons"""
        for task_index, widgets in self.task_widgets.items():
            continue_btn = widgets.get('continue_btn')
            if continue_btn:
                try:
                    continue_btn.setVisible(False)
                except RuntimeError:
                    # Button has been deleted, remove from widgets dict
                    if 'continue_btn' in widgets:
                        del widgets['continue_btn']
    
    def trigger_continue_debug(self, task_index):
        """Trigger continue debug functionality from inline button"""
        print(f"🎮 INLINE CONTINUE: step {task_index} continue button clicked")
        # Find the AutomationApp instance and trigger continue
        app_widget = self
        while app_widget and not isinstance(app_widget, QMainWindow):
            app_widget = app_widget.parent()
        
        if app_widget and hasattr(app_widget, 'continue_execution'):
            app_widget.continue_execution()
        # Hide the continue button after clicking
        self.hide_continue_button(task_index)
    
    def clear_all_status(self):
        """Reset all tasks to pending status"""
        for task_index in self.task_widgets.keys():
            self.set_task_pending(task_index)

