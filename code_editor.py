from PyQt5.QtWidgets import QWidget, QTextEdit, QPlainTextEdit
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QTextFormat, QFont


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    # Signal emitted when undo/redo state changes
    undo_redo_state_changed = pyqtSignal(bool, bool)  # (can_undo, can_redo)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lineNumberArea = LineNumberArea(self)
        self.setReadOnly(False) 
        
        # Initialize custom undo/redo stack
        self.undo_stack = []  # Stack of code states
        self.redo_stack = []  # Stack of undone states
        self.current_state = ""  # Track current state
        self.is_updating_from_chat = False  # Flag to prevent recording chat updates as user edits
        
        # Connect signals
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.textChanged.connect(self.on_text_changed)
        
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        
        # Set styling similar to VS Code
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                selection-background-color: #264f78;
            }
        """)
        
        # Set font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # Set tab width (4 spaces)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

    def lineNumberAreaWidth(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), 
                                               self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(30, 30, 30))
        
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        font = QFont("Consolas", 9)
        painter.setFont(font)
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(133, 133, 133))
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, 
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(44, 44, 44)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        
        self.setExtraSelections(extraSelections)
    
    def on_text_changed(self):
        """Called when text changes - tracks changes for undo/redo"""
        if not self.is_updating_from_chat:
            current_text = self.toPlainText()
            # Only add to history if text actually changed
            if current_text != self.current_state:
                self.undo_stack.append(self.current_state)
                self.current_state = current_text
                self.redo_stack.clear()  # Clear redo stack when new changes made
                self.emit_undo_redo_state()
    
    def initialize_state(self, text):
        """Initialize the editor state without adding to undo history"""
        self.current_state = text
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.is_updating_from_chat = True
        self.setPlainText(text)
        self.is_updating_from_chat = False
        self.emit_undo_redo_state()
    
    def push_state(self, new_text):
        """Push a new state to the undo stack when code is updated from chat"""
        self.undo_stack.append(self.current_state)
        self.current_state = new_text
        self.redo_stack.clear()
        self.emit_undo_redo_state()
    
    def can_undo(self):
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def undo(self):
        """Undo the last change"""
        if self.can_undo():
            self.redo_stack.append(self.current_state)
            self.current_state = self.undo_stack.pop()
            self.is_updating_from_chat = True
            self.setPlainText(self.current_state)
            self.is_updating_from_chat = False
            self.emit_undo_redo_state()
            return True
        return False
    
    def redo(self):
        """Redo the last undone change"""
        if self.can_redo():
            self.undo_stack.append(self.current_state)
            self.current_state = self.redo_stack.pop()
            self.is_updating_from_chat = True
            self.setPlainText(self.current_state)
            self.is_updating_from_chat = False
            self.emit_undo_redo_state()
            return True
        return False
    
    def emit_undo_redo_state(self):
        """Emit signal about current undo/redo state"""
        self.undo_redo_state_changed.emit(self.can_undo(), self.can_redo())