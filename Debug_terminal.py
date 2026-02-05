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

class EnhancedPythonSyntaxHighlighter(QSyntaxHighlighter):
    """Enhanced Python syntax highlighter with current line tracking"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_line = -1
        self.setup_highlighting_rules()
    
    def clear_highlights(self):
        self.current_line = -1
        self.breakpoint_line = -1
        self.rehighlight()
        
    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules"""
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            'import', 'from', 'def', 'class', 'if', 'else', 'elif', 'for', 'while',
            'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'break',
            'continue', 'pass', 'lambda', 'and', 'or', 'not', 'in', 'is', 'None',
            'True', 'False', 'global', 'nonlocal', 'assert', 'del', 'raise'
        ]
        
        for keyword in keywords:
            pattern = f"\\b{keyword}\\b"
            self.highlighting_rules.append((pattern, keyword_format))
            
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        
        # Single quotes
        self.highlighting_rules.append((r"'[^']*'", string_format))
        # Double quotes
        self.highlighting_rules.append((r'"[^"]*"', string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)
        
        # Single-line comments
        self.highlighting_rules.append((r"#[^\n]*", comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append((r"\b\d+\.?\d*\b", number_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append((r"\b[a-zA-Z_][a-zA-Z0-9_]*(?=\()", function_format))
        
    def highlightBlock(self, text):
        """Apply highlighting to a text block"""
        block_number = self.currentBlock().blockNumber()
        
        # Apply syntax highlighting rules
        for pattern, format in self.highlighting_rules:
            import re
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)
                
        # Highlight current execution line
        if block_number == self.current_line:
            current_line_format = QTextCharFormat()
            current_line_format.setBackground(QColor("#2d4a5a"))
            current_line_format.setProperty(QTextCharFormat.FullWidthSelection, True)
            self.setFormat(0, len(text), current_line_format)
            
        # Highlight current line indicator (▶️)
        if "▶️" in text:
            arrow_format = QTextCharFormat()
            arrow_format.setForeground(QColor("#ffff00"))
            arrow_format.setFontWeight(QFont.Bold)
            arrow_index = text.find("▶️")
            if arrow_index >= 0:
                self.setFormat(arrow_index, 2, arrow_format)
                
    def set_current_line(self, line_number):
        """Set the current line to highlight"""
        self.current_line = line_number
        self.rehighlight()
        
    def clear_current_line(self):
        """Clear current line highlighting"""
        self.current_line = -1
        self.rehighlight()

class DebugTerminalWidget(QTextEdit):
    """Enhanced terminal widget with VS Code-style debugging UI"""
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 12))
        
        # Apply centralized styling
        self.setProperty('class', 'DebugTerminalWidget')
        style_loader.apply_stylesheet(self)
        
        # Enhanced syntax highlighter with line tracking
        self.highlighter = EnhancedPythonSyntaxHighlighter(self.document())
        
        # Debug controls container
        self.debug_controls_container = QWidget(self)
        self.setup_enhanced_debug_controls()
        self.debug_controls_container.setGeometry(10, 10, 450, 55)
        self.debug_controls_container.show()
        
        # Track debugging state
        self.is_pdb_active = False
        self.current_code_lines = []
        self.current_line_index = 0
        self.line_number_area = None
        
        # Setup line number area
        self.setup_line_number_area()

    def disable_debug_controls(self):
        """Disable debug control buttons"""
        self.step_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.debug_indicator.setText(" DEBUG MODE")
        self.debug_indicator.setProperty('class', 'DebugIndicatorInactive')
        style_loader.apply_stylesheet(self.debug_indicator)
        
    def setup_line_number_area(self):
        """Setup line number area like VS Code"""
        self.line_number_area = QWidget(self)
        self.line_number_area.setProperty('class', 'DebugLineNumberArea')
        style_loader.apply_stylesheet(self.line_number_area)
        self.line_number_area.setFixedWidth(60)
    
    def enable_debug_controls(self):
        """Enable debug control buttons"""
        self.step_btn.setEnabled(True)
        self.continue_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.debug_indicator.setText(" DEBUG ACTIVE")
        self.debug_indicator.setProperty('class', 'DebugIndicatorActive')
        style_loader.apply_stylesheet(self.debug_indicator)
    def clear_highlights(self):
        """Clear all line highlights"""
        self.highlighter.clear_highlights()
        
    def setup_enhanced_debug_controls(self):
        """Setup VS Code-style debug controls"""
        layout = QHBoxLayout(self.debug_controls_container)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Debug status with better styling
        self.debug_indicator = QLabel(" DEBUG MODE")
        self.debug_indicator.setProperty('class', 'DebugIndicator')
        style_loader.apply_stylesheet(self.debug_indicator)
        
        # Enhanced step button
        self.step_btn = QPushButton("⏩ Step Into")
        self.step_btn.setProperty('class', 'DebugStepButton')
        style_loader.apply_stylesheet(self.step_btn)
        self.step_btn.setEnabled(False)
        
        # Enhanced continue button
        self.continue_btn = QPushButton("▶️ Continue")
        self.continue_btn.setProperty('class', 'DebugContinueButton')
        style_loader.apply_stylesheet(self.continue_btn)
        self.continue_btn.setEnabled(False)
        
        # Enhanced stop button
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setProperty('class', 'DebugStopButton')
        style_loader.apply_stylesheet(self.stop_btn)
        self.stop_btn.setEnabled(False)
        
        # Current line indicator
        self.line_indicator = QLabel("Line: 0")
        self.line_indicator.setProperty('class', 'DebugLineIndicator')
        style_loader.apply_stylesheet(self.line_indicator)
        
        # Add widgets to layout
        layout.addWidget(self.debug_indicator)
        layout.addWidget(self.step_btn)
        layout.addWidget(self.continue_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.line_indicator)
        layout.addStretch()
        
    def display_code_with_highlighting(self, code_str, current_line=0):
        """Display code with VS Code-style line highlighting"""
        self.clear()
        self.current_code_lines = code_str.strip().split('\n')
        self.current_line_index = current_line
        
        # Enhanced header
        header = " DEBUG SESSION - Code Execution\n"
        header += "=" * 60 + "\n\n"
        
        # Build code with line numbers and highlighting
        code_with_numbers = ""
        for i, line in enumerate(self.current_code_lines):
            line_num = str(i + 1).rjust(3)
            if i == current_line:
                # Current line with highlighting
                code_with_numbers += f"▶️ {line_num} │ {line}\n"
            else:
                # Regular line
                code_with_numbers += f"   {line_num} │ {line}\n"
        
        # Status footer
        footer = f"\n{'─' * 60}\n"
        footer += f"🎯 Current Line: {current_line + 1} / {len(self.current_code_lines)}\n"
        footer += f"⏳ Waiting for debug action..."
        
        full_content = header + code_with_numbers + footer
        self.setPlainText(full_content)
        
        # Update highlighter
        self.highlighter.set_current_line(current_line + 3)  # +3 for header offset
        self.line_indicator.setText(f"Line: {current_line + 1}")
        
        # Auto-scroll to current line
        self.scroll_to_current_line(current_line)
        
        print(f" DEBUG: Code displayed with {len(self.current_code_lines)} lines")
  
    def scroll_to_current_line(self, line_index):
        """Scroll to show the current line"""
        cursor = self.textCursor()
        # Calculate approximate position (header + line_index)
        target_line = line_index + 2  # Account for header
        cursor.movePosition(QTextCursor.Start)
        for _ in range(target_line):
            cursor.movePosition(QTextCursor.Down)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        
    def step_to_next_line(self):
        """Advance to next line with highlighting"""
        if self.current_line_index < len(self.current_code_lines) - 1:
            self.current_line_index += 1
            self.update_line_highlight()
            
    def update_line_highlight(self):
        """Update the line highlighting"""
        if self.current_code_lines:
            self.display_code_with_highlighting(
                '\n'.join(self.current_code_lines), 
                self.current_line_index
            )
            
    def enable_debug_mode(self):
        """Enable debug mode with enhanced UI"""
        self.is_pdb_active = True
        self.step_btn.setEnabled(True)
        self.continue_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        self.debug_indicator.setText("🐛 DEBUGGING")
        self.debug_indicator.setProperty('class', 'DebuggingIndicator')
        style_loader.apply_stylesheet(self.debug_indicator)
        
    def disable_debug_mode(self):
        """Disable debug mode"""
        self.is_pdb_active = False
        self.step_btn.setEnabled(False)
        self.continue_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        self.debug_indicator.setText(" DEBUG MODE")
        self.debug_indicator.setProperty('class', 'DebugModeIndicator')
        style_loader.apply_stylesheet(self.debug_indicator)
        
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if self.line_number_area:
            self.line_number_area.setGeometry(
                0, 70, 60, self.height() - 70
            )
        # Reposition debug controls
        self.debug_controls_container.setGeometry(
            10, 10, min(450, self.width() - 20), 55
        )

class CodeDebugger:
    """True PDB-based code debugger"""
    
    def __init__(self, debug_state, debug_signals):
        self.debug_state = debug_state
        self.debug_signals = debug_signals
        self.local_vars = {}
        self.global_vars = {'driver': None}
        self.pdb_instance = None
        self.original_stdout = None
        self.original_stderr = None
        
    def execute_with_debugging(self, code_str, driver_ref):
        """Execute code with TRUE PDB integration"""
        print(" DEBUG: Starting execute_with_debugging")
        
        self.global_vars['driver'] = driver_ref["driver"]
        
        # Convert code to include pdb.set_trace()
        from debug_code_convert import code_convert
        final_code = code_convert(code_str)
        
        print(f" DEBUG: Final code with PDB:\n{final_code}")
        
        # Display clean code on terminal
        clean_code = code_str.strip("`").replace("python", "", 1).strip()
        print(f" DEBUG: Emitting code_display_requested signal")
        self.debug_signals.code_display_requested.emit(clean_code)
        
        # Setup custom PDB
        self.setup_gui_pdb()
        
        try:
            print(" DEBUG: About to execute code with PDB")
            exec(final_code, self.global_vars,driver_ref)
            print(" DEBUG: Code execution completed")
            
            self.debug_signals.debug_completed.emit()
            return "No_Issue", code_str
        except StaleElementReferenceException:
            return "No_Issue", code_str
        except Exception as e:
            print(f" DEBUG: Exception during execution: {str(e)}")
            self.debug_signals.execution_error.emit(0, final_code, str(e))
            return f"Debug execution error: {str(e)}", code_str
        finally:
            self.cleanup_pdb()

    def setup_gui_pdb(self):
        """Setup PDB to work with GUI buttons - SIMPLIFIED VERSION"""
        
        class GUIPdb(pdb.Pdb):
            def __init__(self, debug_state, debug_signals):
                super().__init__()
                self.debug_state = debug_state
                self.debug_signals = debug_signals

            def set_trace(self, frame=None):
                """Override set_trace - THIS IS THE MISSING ENTRY POINT"""
                print(" PDB: set_trace called - entering GUI PDB mode")
                if frame is None:
                    frame = sys._getframe().f_back
                self.reset()
                self.interaction(frame, None)

            def interaction(self, frame, traceback):
                """Override interaction - THIS CALLS cmdloop"""
                print(" PDB: interaction called - will call cmdloop")
                
                # Setup frame
                self.curframe = frame
                self.curframe_locals = frame.f_locals
                self.curframe_globals = frame.f_globals
                
                # THIS IS THE MISSING CALL TO cmdloop
                self.cmdloop()
                
            def user_line(self, frame):
                """Called automatically by PDB when stepping to a new line"""
                print(f" PDB: user_line AUTOMATICALLY called at line {frame.f_lineno}")
                
                # Update current frame
                self.curframe = frame
                self.curframe_locals = frame.f_locals
                self.curframe_globals = frame.f_globals
                
                # Get line info
                lineno = frame.f_lineno
                filename = frame.f_code.co_filename
                
                import linecache
                line_content = linecache.getline(filename, lineno).strip()
                if line_content:
                    print(f" PDB: Stepped to line {lineno}: {line_content}")
                    self.debug_signals.pdb_line_changed.emit(lineno, line_content)
                
                # Show cmdloop for next user action
                self.cmdloop()
            
            def cmdloop(self, intro=None):
                """Custom command loop with proper PDB step handling"""
                print(" PDB: cmdloop started with proper step handling")
                
                try:
                    while True:
                        # Get and display current line info
                        if self.curframe:
                            lineno = self.curframe.f_lineno
                            filename = self.curframe.f_code.co_filename
                            
                            import linecache
                            line_content = linecache.getline(filename, lineno).strip()
                            if line_content:
                                print(f" PDB: Current line {lineno}: {line_content}")
                                self.debug_signals.pdb_line_changed.emit(lineno, line_content)

                        # Signal that PDB is waiting for input
                        self.debug_state.execution_paused = True
                        self.debug_signals.pdb_waiting_for_input.emit()

                        # Wait for GUI button click
                        self.debug_state.mutex.lock()
                        while self.debug_state.execution_paused and not self.debug_state.stop_requested:
                            self.debug_state.wait_condition.wait(self.debug_state.mutex)
                        self.debug_state.mutex.unlock()

                        print(f" PDB: Received action: {self.debug_state.debug_action}")

                        # Handle button clicks
                        if self.debug_state.stop_requested:
                            print(" PDB: QUIT - stopping execution")
                            self.onecmd("q")
                            break
                            
                        elif self.debug_state.debug_action == "stepinto":
                            print(" PDB: STEP - executing one line")
                            self.debug_signals.pdb_step_executed.emit()
                            
                            # Execute step and let PDB handle line advancement
                            result = self.onecmd("s")
                            print(f" PDB: Step result: {result}")
                            
                            # CRITICAL: Don't break here - continue loop for next step
                            print(" PDB: Step completed - ready for next action")
                            
                        elif self.debug_state.debug_action == "continue":
                            print(" PDB: CONTINUE - running to completion")
                            self.debug_signals.pdb_continue_executed.emit()
                            self.onecmd("c")
                            break

                        # Reset action for next iteration
                        self.debug_state.debug_action = None

                except Exception as e:
                    print(f" PDB: cmdloop error: {e}")


        # Create and set up the PDB instance
        self.pdb_instance = GUIPdb(self.debug_state, self.debug_signals)
        
        # Store original and override global pdb
        self.original_set_trace = pdb.set_trace
        pdb.set_trace = self.pdb_instance.set_trace
        
        print("✅ Simplified PDB setup complete")


    def cleanup_pdb(self):
        """Restore original pdb functionality"""
        if hasattr(self, 'original_set_trace'):
            pdb.set_trace = self.original_set_trace

class DebugSignals(QThread):
    """Signals for debugging events"""
    debug_started = pyqtSignal(list)
    line_executing = pyqtSignal(int, str)
    line_executed = pyqtSignal(int, str)
    breakpoint_hit = pyqtSignal(int, str)
    step_paused = pyqtSignal(int, str)
    execution_error = pyqtSignal(int, str, str)
    debug_stopped = pyqtSignal()
    debug_completed = pyqtSignal()
    task_debug_completed = pyqtSignal()
    code_display_requested = pyqtSignal(str)
    pdb_waiting_for_input = pyqtSignal()
    pdb_output_received = pyqtSignal(str)
    pdb_step_executed = pyqtSignal()
    pdb_continue_executed = pyqtSignal()
    pdb_quit_executed = pyqtSignal()
    pdb_line_changed = pyqtSignal(int, str)  # line_number, line_conten
