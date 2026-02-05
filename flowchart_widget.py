import sys
import re
import uuid
import ast
import json
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QTextEdit, QLabel, QComboBox, QPushButton, QScrollArea,
                             QFrame, QDialog, QLineEdit, QDialogButtonBox, QMessageBox, QFileDialog,
                             QGroupBox, QFormLayout, QMenuBar, QAction) 
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal, QThread, QSize
from PyQt5.QtGui import (QPainter, QPen, QBrush, QColor, QFont, QPixmap, QPainterPath,
                         QPolygon, QPainterPathStroker)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog 
import os
import google.generativeai as genai


# --- Configuration ---
GEMINI_API_KEY = "AIzaSyDUu2MGTHD_-T6OEVzJ1d2QlpBOdB_77jU"
SAMPLE_CODE = None


# --- Constants ---
BOX_WIDTH, BOX_HEIGHT, OVAL_HEIGHT = 220, 100, 50
Y_SPACING, X_CENTER, Y_START = 80, 550, 50
TASK_BOX_WIDTH, TASK_BOX_HEIGHT = 280, 120
TASK_HEADER_HEIGHT = 35
INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT = 220, 60
INPUT_BOX_X_OFFSET = 270

SHAPE_COLORS = {
    'terminator': '#3b82f6', 'process': "#529df2", 'decision': '#1d4ed8',
    'io': "#4e9df9", 'subroutine': '#3b82f6', 'end': '#3b82f6', 'loop': "#3180db",
    'task_box': '#ffffff'
}
SHAPE_BORDER_COLORS = {
    'terminator': '#1d4ed8', 'process': "#1758c1", 'decision': "#2648a6",
    'io': '#3b82f6', 'subroutine': '#1d4ed8', 'end': '#1d4ed8', 'loop': '#3b82f6',
    'task_box': '#4b5563'
}

TEXT_FONT_SIZE, TEXT_PADDING = 9, 15
LINE_COLOR = "#232529"
ARROW_WIDTH = 2
ARROW_HEAD_SIZE = 10

# Button Style - Professional gradient
BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                stop:0 #005B7F, stop:1 #008AB3);
        border-radius: 10px;
        color: #FFFFFF;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.05em;
        padding: 10px 20px;
        border: none;
        min-height: 40px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                stop:0 #006B8F, stop:1 #009AC3);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                stop:0 #004B6F, stop:1 #007A93);
    }
    QPushButton:disabled {
        background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                stop:0 #888888, stop:1 #999999);
        color: #CCCCCC;
    }
"""


class FlowchartCanvas(QWidget):
    item_edited = pyqtSignal(object)
    item_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1200, 800)
        self.flowchart_steps = []
        self.item_positions = []
        self.loading_message = None
        self.setMouseTracking(True)

    def set_flowchart_data(self, steps):
        self.loading_message = None
        self.flowchart_steps = steps
        self.update_canvas_size()
        self.update()

    def show_loading(self, message):
        self.loading_message = message
        self.flowchart_steps = []
        self.update()

    def _calculate_flowchart_height(self):
        if not self.flowchart_steps:
            return 800
        num_items = len(self.flowchart_steps)
        total_height = Y_START + (num_items * (TASK_BOX_HEIGHT + Y_SPACING)) + OVAL_HEIGHT + Y_SPACING + 100
        return max(800, total_height)

    def update_canvas_size(self):
        calculated_height = self._calculate_flowchart_height()
        if self.height() != calculated_height:
            self.setMinimumSize(self.width(), calculated_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f8fafc"))

        if self.loading_message:
            painter.setFont(QFont("Arial", 16))
            painter.setPen(QColor("#6b7280"))
            painter.drawText(self.rect(), Qt.AlignCenter, self.loading_message)
            return

        self.draw_flowchart(painter)

    def draw_flowchart(self, painter):

        self.item_positions.clear()

        if not self.flowchart_steps:

            painter.setFont(QFont("Arial", 16))

            painter.setPen(QColor("#6b7280"))

            painter.drawText(self.rect(), Qt.AlignCenter, "Generate a flowchart from the code.")




            return



        # Center the flowchart

        center_x = 550



        self.draw_shape(painter, center_x, Y_START, "Start", "terminator", None)

        last_y, last_x = Y_START + OVAL_HEIGHT, center_x



        for i, step in enumerate(self.flowchart_steps):

            x_pos = center_x

            y_pos = last_y + Y_SPACING



            self.draw_thin_arrow(painter, last_x, last_y, x_pos, y_pos)

            bottom_of_item = self.draw_task_box(painter, x_pos, y_pos, step, i)

            last_y, last_x = bottom_of_item, x_pos



        y_pos = last_y + Y_SPACING

        self.draw_thin_arrow(painter, last_x, last_y, center_x, y_pos)

        self.draw_shape(painter, center_x, y_pos, "End", "end", None)

    def draw_task_box(self, painter, x, y, step_data, item_index):
        w, h = TASK_BOX_WIDTH, TASK_BOX_HEIGHT
        rect = QRect(x - w//2, y, w, h)
        self.item_positions.append({'rect': rect, 'index': item_index})

        header_rect = QRect(rect.left(), rect.top(), w, TASK_HEADER_HEIGHT)
        body_rect = QRect(rect.left(), rect.top() + TASK_HEADER_HEIGHT, w, h - TASK_HEADER_HEIGHT)

        painter.setBrush(QColor(SHAPE_COLORS['task_box']))
        painter.setPen(QPen(QColor(SHAPE_BORDER_COLORS['task_box']), 2))
        painter.drawRect(body_rect)

        painter.setBrush(QColor(SHAPE_BORDER_COLORS['task_box']))
        painter.drawRect(header_rect)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(header_rect, Qt.AlignCenter, step_data.get('action', 'Unknown Action'))

        painter.setPen(QColor("#374151"))
        painter.setFont(QFont("Arial", TEXT_FONT_SIZE))
        desc_text_rect = body_rect.adjusted(TEXT_PADDING, TEXT_PADDING, -TEXT_PADDING, -TEXT_PADDING)
        painter.drawText(desc_text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, step_data.get('description', ''))

        inputs = step_data.get('inputs', [])
        num_inputs = len(inputs)
        if num_inputs > 0:
            total_input_height = (num_inputs * INPUT_BOX_HEIGHT) + ((num_inputs - 1) * 10)
            start_y = y + (h // 2) - (total_input_height // 2)
            input_x = x - w//2 - INPUT_BOX_X_OFFSET

            for i, input_item in enumerate(inputs):
                input_y = start_y + i * (INPUT_BOX_HEIGHT + 10)
                input_rect = QRect(input_x, input_y, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)

                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor("#9ca3af"), 1))
                painter.drawRect(input_rect)

                input_text = f"{input_item.get('name', '')} = {input_item.get('value', '')}".strip("= ")
                painter.setPen(QColor("#1f2937"))
                painter.setFont(QFont("Arial", TEXT_FONT_SIZE))
                painter.drawText(input_rect, Qt.AlignCenter | Qt.TextWordWrap, input_text)

                arrow_start_x = input_rect.right()
                arrow_start_y = input_rect.center().y()
                arrow_end_x = rect.left()
                self.draw_thin_arrow(painter, arrow_start_x, arrow_start_y, arrow_end_x, arrow_start_y, is_input_arrow=True)

        return y + h

    def draw_shape(self, painter, x, y, text, shape, item_index):
        w, h = BOX_WIDTH, OVAL_HEIGHT
        fill_color = QColor(SHAPE_COLORS.get(shape, '#3b82f6'))
        border_color = QColor(SHAPE_BORDER_COLORS.get(shape, '#1d4ed8'))
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(border_color, 3))
        rect = QRect(x - w//2, y, w, h)
        painter.drawRoundedRect(rect, h//2, h//2)

        painter.setPen(QPen(QColor("white")))
        font = QFont("Arial", TEXT_FONT_SIZE, QFont.Bold)
        painter.setFont(font)
        text_rect = QRect(x - w//2, y, w, h)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
        return y + h

    def draw_thin_arrow(self, painter, x1, y1, x2, y2, is_input_arrow=False):
        pen = QPen(QColor(LINE_COLOR), ARROW_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(LINE_COLOR)))

        painter.drawLine(x1, y1, x2, y2)
        if is_input_arrow:
            arrow_poly = QPolygon([
                QPoint(x2, y2),
                QPoint(x2 + ARROW_HEAD_SIZE, y2 - ARROW_HEAD_SIZE//2),
                QPoint(x2 + ARROW_HEAD_SIZE, y2 + ARROW_HEAD_SIZE//2)
            ])
        else:
            arrow_poly = QPolygon([
                QPoint(x2, y2),
                QPoint(x2 - ARROW_HEAD_SIZE//2, y2 - ARROW_HEAD_SIZE),
                QPoint(x2 + ARROW_HEAD_SIZE//2, y2 - ARROW_HEAD_SIZE)
            ])
        painter.drawPolygon(arrow_poly)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.get_item_at_position(event.pos())
            if item:
                self.item_selected.emit(item['index'])
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.item_selected.emit(None)

    def mouseMoveEvent(self, event):
        item = self.get_item_at_position(event.pos())
        self.setCursor(Qt.PointingHandCursor if item else Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        item = self.get_item_at_position(event.pos())
        if item:
            self.item_edited.emit(item['index'])

    def get_item_at_position(self, pos):
        for item_pos in reversed(self.item_positions):
            if item_pos['rect'].contains(pos):
                return item_pos
        return None

    def export_to_pdf(self, filename):
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        printer.setPaperSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Portrait)
        
        painter = QPainter()
        if painter.begin(printer):
            widget_rect = self.rect()
            page_rect = printer.pageRect()
            
            scale_x = page_rect.width() / widget_rect.width()
            scale_y = page_rect.height() / widget_rect.height()
            scale = min(scale_x, scale_y, 1.0)
            
            painter.scale(scale, scale)
            painter.fillRect(widget_rect, QColor("#ffffff"))
            painter.setRenderHint(QPainter.Antialiasing)
            self.draw_flowchart(painter)
            
            painter.end()
            return True
        return False


class PropertyPane(QWidget):
    properties_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item_data = None
        self.current_item_index = None
        self.original_code_block = None
        self._is_updating_ui = False
        self.input_widgets = []
        self.setMinimumWidth(420)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        title_label = QLabel("Property Panel")
        title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #FFFFFF;")
        main_layout.addWidget(title_label)

        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setSpacing(12)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.form_container)

        self.placeholder_label = QLabel("Click on a flowchart element to see its properties.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #9CA3AF; font-style: italic; padding: 20px;")
        main_layout.addWidget(self.placeholder_label)

        main_layout.addStretch()
        self.clear_pane()

    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout:
                    self._clear_layout(sub_layout)

    def load_item(self, item_data, item_index):
        self._is_updating_ui = True
        self._clear_layout(self.form_layout)

        self.current_item_data = item_data
        self.current_item_index = item_index
        self.original_code_block = item_data.get('code_block', '')
        self.input_widgets = []

        # --- Action & Description ---
        top_form_layout = QFormLayout()
        top_form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop)
        top_form_layout.setFormAlignment(Qt.AlignTop)
        top_form_layout.setHorizontalSpacing(12)
        top_form_layout.setVerticalSpacing(10)
        top_form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.action_edit = QLineEdit(item_data.get('action', ''))
        self.action_edit.setMinimumHeight(35)
        self.action_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px;")
        
        action_label = QLabel("Action:")
        action_label.setStyleSheet("font-weight: 600; color: #FFFFFF;")
        top_form_layout.addRow(action_label, self.action_edit)
        
        self.desc_edit = QTextEdit(item_data.get('description', ''))
        self.desc_edit.setMinimumHeight(70)
        self.desc_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px;")
        
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: 600; color:#FFFFFF; vertical-align: top;")
        desc_label.setAlignment(Qt.AlignTop)
        top_form_layout.addRow(desc_label, self.desc_edit)
        
        self.form_layout.addLayout(top_form_layout)

        # --- Inputs ---
        if item_data.get('inputs'):
            self.inputs_group = QGroupBox("Inputs")
            self.inputs_group.setStyleSheet("""
                QGroupBox {
                    font-weight: 600;
                    color: #FFFFFF;
                    padding: 10px;
                    border: 1px solid #E5E7EB;
                    border-radius: 4px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
            """)
            self.inputs_layout = QFormLayout(self.inputs_group)
            self.inputs_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.inputs_layout.setFormAlignment(Qt.AlignTop)
            self.inputs_layout.setHorizontalSpacing(12)
            self.inputs_layout.setVerticalSpacing(8)
            self.form_layout.addWidget(self.inputs_group)
            self._build_inputs_ui(item_data.get('inputs', []))

        # --- Code Block ---
        self.form_layout.addSpacing(8)
        code_label = QLabel("Code Block:")
        code_label.setStyleSheet("font-weight: 600; color:#FFFFFF;")
        self.form_layout.addWidget(code_label)
        
        self.code_edit = QTextEdit(item_data.get('code_block', ''))
        self.code_edit.setFont(QFont("Consolas", 10))
        self.code_edit.setMinimumHeight(85)
        self.code_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #000000; color: #FFFFFF;")
        self.form_layout.addWidget(self.code_edit)

        # --- Apply Button ---
        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.setFixedSize(235, 40)
        self.apply_button.setCursor(Qt.PointingHandCursor)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                text-align: center;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #004B6F, stop:1 #007A93);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #888888, stop:1 #999999);
                color: #CCCCCC;
            }
        """)
        self.form_layout.addWidget(self.apply_button)
        self.form_layout.addStretch()

        # Connect signals
        self.action_edit.textChanged.connect(self._update_code_from_fields)
        self.code_edit.textChanged.connect(self._update_fields_from_code)
        self.apply_button.clicked.connect(self._apply_changes)

        self.form_container.show()
        self.placeholder_label.hide()
        self._is_updating_ui = False

    def _build_inputs_ui(self, inputs_data):
        for an_input in inputs_data:
            name = an_input.get('name', 'arg')
            value = str(an_input.get('value', ''))
            editor = QLineEdit(value)
            editor.setMinimumHeight(35)
            editor.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px;")
            
            label = QLabel(f"{name}:")
            label.setStyleSheet("color: #FFFFFF;")
            self.inputs_layout.addRow(label, editor)
            self.input_widgets.append({'name': name, 'editor': editor})
            editor.textChanged.connect(self._update_code_from_fields)

    def _update_code_from_fields(self):
        if self._is_updating_ui: return
        self._is_updating_ui = True
        
        action = self.action_edit.text()
        args = []
        for widget_info in self.input_widgets:
            name = widget_info['name']
            value_text = widget_info['editor'].text()
            try:
                value = repr(ast.literal_eval(value_text))
            except (ValueError, SyntaxError):
                value = repr(value_text)
            args.append(f"{name}={value}")
        
        args_str = ", ".join(args)
        new_code = f"{action}({args_str})" if args else f"{action}()"
        self.code_edit.setText(new_code)
        # self.code_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #F9FAFB;")
        self.code_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #000000; color: #FFFFFF;")
        self._is_updating_ui = False

    def _update_fields_from_code(self):
        if self._is_updating_ui: return
        self._is_updating_ui = True
        
        code_block = self.code_edit.toPlainText().strip()
        try:
            if not code_block: raise SyntaxError("Code is empty")

            tree = ast.parse(code_block)
            if not tree.body or not isinstance(tree.body[0], ast.Expr) or not isinstance(tree.body[0].value, ast.Call):
                raise SyntaxError("Not a valid function call.")
            
            call_node = tree.body[0].value
           
            if isinstance(call_node.func, ast.Name):
                action_name = call_node.func.id
            elif isinstance(call_node.func, ast.Attribute):
                action_name = call_node.func.attr
            else:
                action_name = "Unknown"

            self.action_edit.setText(action_name)

            parsed_inputs = []
            for kw in call_node.keywords:
                try:
                    value = ast.literal_eval(kw.value)
                except ValueError:
                    value = ast.unparse(kw.value) if hasattr(ast, 'unparse') else '...'
                parsed_inputs.append({'name': kw.arg, 'value': value})
            
            self._clear_layout(self.inputs_layout)
            self.input_widgets = []
            self._build_inputs_ui(parsed_inputs)

            self.code_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #000000; color: #FFFFFF;")
            
        except (SyntaxError, ValueError, TypeError):
            self.code_edit.setStyleSheet("padding: 5px; border: 2px solid #DC2626; border-radius: 4px; background-color: #1a0000; color: #FFFFFF;")
        
        self._is_updating_ui = False

    def _apply_changes(self):
        if "DC2626" in self.code_edit.styleSheet():
            QMessageBox.warning(self, "Invalid Code", "Cannot apply changes because the code block has invalid syntax.")
            return

        self.current_item_data['action'] = self.action_edit.text()
        self.current_item_data['description'] = self.desc_edit.toPlainText()
        self.current_item_data['code_block'] = self.code_edit.toPlainText().strip()
        
        new_inputs = []
        for widget_info in self.input_widgets:
            value_text = widget_info['editor'].text()
            try:
                value = ast.literal_eval(value_text)
            except (ValueError, SyntaxError):
                value = value_text
            new_inputs.append({'name': widget_info['name'], 'value': value})
        self.current_item_data['inputs'] = new_inputs
        
        self.properties_changed.emit()
        self.code_edit.setStyleSheet("padding: 5px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #000000; color: #FFFFFF;")

    def clear_pane(self):
        self._clear_layout(self.form_layout)
        self.current_item_data = None
        self.current_item_index = None
        self.original_code_block = None
        self.form_container.hide()
        self.placeholder_label.show()


class AITaskAutomationWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, gemini_model, code_to_analyze):
        super().__init__()
        self.gemini_model = gemini_model
        self.code = code_to_analyze

    def run(self):

        # Check for XPath mapping file
        xpath_file_path = os.path.join("json_info", "json_xpath.json")
        xpath_data = {}

        if os.path.exists(xpath_file_path):
            try:
                with open(xpath_file_path, "r", encoding="utf-8") as f:
                    xpath_data = json.load(f)
            except Exception as e:
                xpath_data = {"error": f"Failed to load xpath file: {str(e)}"}
        else:
            xpath_data = {"info": "json_xpath.json not found, defaulting to Not_assigned"}

        # Prepare AI prompt
        prompt = f"""
        Analyze the following Python code to identify function calls that represent distinct automation tasks. 
        Ignore comments, imports, and simple print statements. For each task, generate a JSON object.

        **Instructions:**
        1. Focus only on function calls such as `open_browser(...)`, `click_into(...)`, `find_element_and_type(...)`, `find_element_and_click(...)`, etc.
        2. Extract the function name as the 'action'.
        3. Write a short, clear 'description' (1–7 words) explaining what the action does.
        4. For 'inputs':
        - Include up to two main arguments of the function.
        - Each argument should be a dictionary with:
            - 'name': argument name (if available, otherwise use "Value")
            - 'value': actual value used in the code block.(if not available, refer from json_xpath.json)
        - If the variable used in the function matches any key in the provided XPath mapping below, 
            replace it with the corresponding XPath value.
        - If the variable was assigned a value earlier in the code, use that value.
        - If no assignment or XPath mapping exists, use "Not_assigned".
        5. The 'code_block' field must contain the **exact original line of Python code**.
        6. The 'shape' must always be "task_box".
        7. Output MUST be a valid JSON list only — no explanation or extra text outside the JSON.

        **Note: All the fields are mandatory, include all the inputs even if they are "Not_assigned" and how many times generated keep the order same as in code.**
        **XPath mapping for Variables in the Python code:**
        ```json
        {json.dumps(xpath_data, indent=4)}
        ```

        **Python code to analyze:**
        ```python
        {self.code}
        ```
        """

        try:
            response = self.gemini_model.generate_content(prompt, request_options={'timeout': 60})
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            flowchart_data = json.loads(cleaned_response)
            for step in flowchart_data:
                step['id'] = str(uuid.uuid4())
            self.finished.emit(flowchart_data)

        except Exception as e:
            response_text = "No response"
            if 'response' in locals() and hasattr(response, 'text'):
                response_text = response.text
            error_message = f"Failed to generate AI Task Flow.\n\nError: {str(e)}\n\nResponse from AI:\n{response_text}"
            self.error.emit(error_message)


class ComprehensiveFlowchartIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Task Automation IDE")
        self.setGeometry(100, 100, 1900, 1000)

        self.flowchart_steps = []
        self.preamble_code = ""
        self.sync_enabled = True
        self.gemini_model = None

        self.initialize_gemini()
        self.setup_ui()
        self.create_menu_bar()

        self.code_input.setPlainText(SAMPLE_CODE)
        QTimer.singleShot(100, self.generate_flowchart)

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        export_pdf_action = QAction('Export to PDF', self)
        export_pdf_action.setShortcut('Ctrl+E')
        export_pdf_action.setStatusTip('Export flowchart to PDF')
        export_pdf_action.triggered.connect(self.export_to_pdf)
        file_menu.addAction(export_pdf_action)

    def export_to_pdf(self):
        if not self.flowchart_steps:
            QMessageBox.warning(self, "No Flowchart", "Please generate a flowchart first before exporting to PDF.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export Flowchart to PDF", "flowchart.pdf", "PDF Files (*.pdf)")
        
        if filename:
            try:
                success = self.canvas.export_to_pdf(filename)
                if success:
                    QMessageBox.information(self, "Export Successful", f"Flowchart exported to:\n{filename}")
                else:
                    QMessageBox.critical(self, "Export Failed", "Failed to export flowchart to PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"An error occurred while exporting:\n{str(e)}")

    def initialize_gemini(self):
        if not GEMINI_API_KEY or "YOUR_GEMINI_API_KEY" in GEMINI_API_KEY:
            QMessageBox.warning(self, "API Key Missing", "Gemini API key is not configured. AI features will be unavailable.")
            return
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        except Exception as e:
            self.gemini_model = None
            QMessageBox.critical(self, "API Error", f"Failed to initialize Gemini API: {e}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # --- LEFT PANEL: Code Input (HIDDEN) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        self.code_input = QTextEdit()
        self.code_input.setFont(QFont("Consolas", 11))
        self.code_input.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 4px;")
        left_layout.addWidget(self.code_input, 1)
        left_widget.hide()  # Hide the entire left panel


        # --- MIDDLE PANEL: Flowchart ---
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        flowchart_label = QLabel("Interactive Flowchart")
        flowchart_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #FFFFFF;")
        header_layout.addWidget(flowchart_label)
        header_layout.addStretch()

        # Generate Button with fixed size
        self.generate_button = QPushButton("🔄 Generate/Refresh Flowchart")
        self.generate_button.setFixedSize(280, 40)
        self.generate_button.setCursor(Qt.PointingHandCursor)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                text-align: center;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #004B6F, stop:1 #007A93);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #888888, stop:1 #999999);
                color: #CCCCCC;
            }
        """)
        header_layout.addWidget(self.generate_button)

        # Download PDF Button with fixed size
        self.export_pdf_button = QPushButton("📄 Download PDF")
        self.export_pdf_button.setFixedSize(235, 40)
        self.export_pdf_button.setCursor(Qt.PointingHandCursor)
        self.export_pdf_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #005B7F, stop:1 #008AB3);
                border-radius: 10px;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.05em;
                text-align: center;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #006B8F, stop:1 #009AC3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #004B6F, stop:1 #007A93);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                                            stop:0 #888888, stop:1 #999999);
                color: #CCCCCC;
            }
        """)
        header_layout.addWidget(self.export_pdf_button)

        middle_layout.addLayout(header_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #D1D5DB; border-radius: 4px; }")
        self.canvas = FlowchartCanvas()
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.scroll_area, 1)

        # --- RIGHT PANEL: Property Pane ---
        self.property_pane = PropertyPane()

        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(middle_widget)
        main_splitter.addWidget(self.property_pane)
        main_splitter.setSizes([500, 1000, 450])
        main_splitter.setCollapsible(0, False)
        main_splitter.setCollapsible(1, False)
        main_splitter.setCollapsible(2, False)

        # Connect signals
        self.generate_button.clicked.connect(self.generate_flowchart)
        self.canvas.item_selected.connect(self.show_properties_for_item)
        self.property_pane.properties_changed.connect(self.update_from_properties)
        self.export_pdf_button.clicked.connect(self.on_export_pdf_clicked)
        
        # Initially disable export button
        self.export_pdf_button.setEnabled(False)
        
    def off_download_button(self):
        self.export_pdf_button.setEnabled(False)

    def on_export_pdf_clicked(self):
        threading.Thread(target=self.export_to_pdf, daemon=True).start()

    def generate_flowchart(self):
        if not self.gemini_model:
            QMessageBox.critical(self, "AI Not Available", "The Gemini AI model is not initialized.")
            return

        code = self.code_input.toPlainText()
        if not code.strip():
            self.flowchart_steps = []
            self.canvas.set_flowchart_data([])
            self.property_pane.clear_pane()
            self.export_pdf_button.setEnabled(False)
            return

        lines = code.splitlines()
        self.preamble_code = ""
        task_code_lines = []
        in_preamble = True
        
        for line in lines:
            stripped = line.strip()
            is_preamble_line = not stripped or \
                               stripped.startswith('#') or \
                               stripped.startswith('import ') or \
                               stripped.startswith('from ') or \
                               stripped.startswith('def ') or \
                               stripped.startswith('class ')

            if in_preamble and is_preamble_line:
                self.preamble_code += line + '\n'
            else:
                in_preamble = False
                if stripped and not stripped.startswith('#'):
                    task_code_lines.append(line)

        task_code_to_analyze = "\n".join(task_code_lines)

        self.generate_button.setEnabled(False)
        self.generate_button.setText("⏳ Generating...")
        self.canvas.show_loading("Generating Flowchart...")

        self.ai_worker = AITaskAutomationWorker(self.gemini_model, task_code_to_analyze)
        self.ai_worker.finished.connect(self.on_ai_flowchart_ready)
        self.ai_worker.error.connect(self.on_ai_flowchart_error)
        self.ai_worker.start()

    def on_ai_flowchart_ready(self, steps):
        self.flowchart_steps = steps
        self.canvas.set_flowchart_data(self.flowchart_steps)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🔄 Generate/Refresh Flowchart")
        self.property_pane.clear_pane()
        self.export_pdf_button.setEnabled(len(self.flowchart_steps) > 0)

    def on_ai_flowchart_error(self, error_message):
        QMessageBox.critical(self, "AI Generation Failed", error_message)
        self.canvas.set_flowchart_data([])
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🔄 Generate/Refresh Flowchart")
        self.export_pdf_button.setEnabled(False)

    def show_properties_for_item(self, item_index):
        if item_index is None:
            self.property_pane.clear_pane()
            return
        if isinstance(item_index, int) and 0 <= item_index < len(self.flowchart_steps):
            item_data = self.flowchart_steps[item_index]
            self.property_pane.load_item(item_data, item_index)

    def update_from_properties(self):
        self.surgically_update_code()
        self.canvas.set_flowchart_data(self.flowchart_steps)

    def surgically_update_code(self):
        if not self.sync_enabled or self.property_pane.current_item_index is None:
            return

        edited_item_index = self.property_pane.current_item_index
        new_code_line = self.flowchart_steps[edited_item_index].get('code_block', '').strip()
        original_code_line = self.property_pane.original_code_block.strip()
        current_full_code = self.code_input.toPlainText()

        if original_code_line and new_code_line != original_code_line:
            updated_full_code = current_full_code.replace(original_code_line, new_code_line, 1)
            self.sync_enabled = False
            self.code_input.setPlainText(updated_full_code)
            QTimer.singleShot(100, lambda: setattr(self, 'sync_enabled', True))
            self.property_pane.original_code_block = new_code_line


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ComprehensiveFlowchartIDE()
    window.show()
    sys.exit(app.exec_())