import sys
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter with VS Code-like theme"""
    
    def __init__(self, parent=None):
        super(PythonSyntaxHighlighter, self).__init__(parent)
        
        # Define highlighting rules
        self.highlighting_rules = []
        
        # VS Code-like color scheme (Dark theme) - Enhanced
        self.colors = {
            'keyword': QColor(86, 156, 214),      # Blue - def, if, else, etc.
            'builtin': QColor(220, 220, 170),     # Light yellow - print, len, etc.
            'string': QColor(206, 145, 120),      # Orange - strings
            'f_string': QColor(206, 145, 120),    # Orange - f-strings
            'comment': QColor(106, 153, 85),      # Green - comments
            'flow_comment': QColor(0, 255, 200),  # Bright teal - Start/End Flow comments
            'number': QColor(181, 206, 168),      # Light green - numbers
            'operator': QColor(212, 212, 212),    # White - operators
            'function': QColor(220, 220, 170),    # Light yellow - function names
            'class': QColor(78, 201, 176),        # Teal - class names
            'decorator': QColor(86, 156, 214),    # Blue - decorators
            'self': QColor(86, 156, 214),         # Blue - self keyword
            'import': QColor(197, 134, 192),      # Purple - import statements
            'type_hint': QColor(78, 201, 176),    # Teal - type hints
            'magic_method': QColor(197, 134, 192), # Purple - __init__, __str__, etc.
            'constant': QColor(79, 193, 255),     # Light blue - CONSTANTS
        }
        
        # Create text formats with enhanced styling
        self.formats = {}
        for name, color in self.colors.items():
            format = QTextCharFormat()
            format.setForeground(color)
            # Bold formatting for specific elements
            if name in ['keyword', 'builtin', 'self', 'import', 'magic_method', 'comment']:
                format.setFontWeight(QFont.Bold)
            # Extra bold formatting for flow comments to make them stand out more
            elif name == 'flow_comment':
                format.setFontWeight(QFont.Black)  # Maximum boldness
                format.setFont(QFont("Consolas", 14, QFont.Black))  # Explicit font with black weight
            
            # Make comments slightly bigger
            if name == 'comment':
                font = QFont("Consolas", 10, QFont.Bold)  # Increased from default size
                format.setFont(font)
            
            # Italic formatting for type hints (removed comment from here since it's now bold)
            if name == 'type_hint':
                format.setFontItalic(True)
            
            self.formats[name] = format
        
        # Python keywords (enhanced with modern Python features)
        keywords = [
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'None', 'True', 'False', 'nonlocal'
        ]
        
        # Built-in functions
        builtins = [
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict',
            'dir', 'divmod', 'enumerate', 'eval', 'filter', 'float',
            'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash',
            'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
            'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
            'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'property',
            'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
            'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
            'vars', 'zip'
        ]
        
        # Add keyword rules
        for keyword in keywords:
            pattern = QRegExp(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.formats['keyword']))
        
        # Add builtin function rules
        for builtin in builtins:
            pattern = QRegExp(r'\b' + builtin + r'\b')
            self.highlighting_rules.append((pattern, self.formats['builtin']))
        
        # Import statements
        import_pattern = QRegExp(r'\b(import|from)\b')
        self.highlighting_rules.append((import_pattern, self.formats['import']))
        
        # Self keyword
        self_pattern = QRegExp(r'\bself\b')
        self.highlighting_rules.append((self_pattern, self.formats['self']))
        
        # Function definitions
        function_pattern = QRegExp(r'\bdef\s+([A-Za-z_][A-Za-z0-9_]*)')
        self.highlighting_rules.append((function_pattern, self.formats['function']))
        
        # Class definitions
        class_pattern = QRegExp(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
        self.highlighting_rules.append((class_pattern, self.formats['class']))
        
        # Decorators
        decorator_pattern = QRegExp(r'@[A-Za-z_][A-Za-z0-9_]*')
        self.highlighting_rules.append((decorator_pattern, self.formats['decorator']))
        
        # Magic methods (dunder methods)
        magic_method_pattern = QRegExp(r'\b__[A-Za-z_][A-Za-z0-9_]*__\b')
        self.highlighting_rules.append((magic_method_pattern, self.formats['magic_method']))
        
        # Constants (ALL_CAPS)
        constant_pattern = QRegExp(r'\b[A-Z][A-Z0-9_]*\b')
        self.highlighting_rules.append((constant_pattern, self.formats['constant']))
        
        # Type hints (basic pattern for common types)
        type_hint_pattern = QRegExp(r':\s*(int|str|float|bool|list|dict|tuple|set|Optional|Union|List|Dict|Tuple|Set)\b')
        self.highlighting_rules.append((type_hint_pattern, self.formats['type_hint']))
        
        # Numbers
        number_pattern = QRegExp(r'\b[+-]?[0-9]+[lL]?\b|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b')
        self.highlighting_rules.append((number_pattern, self.formats['number']))
        
        # Operators
        operator_pattern = QRegExp(r'[+\-*/%=<>!&|^~]|\b(and|or|not|in|is)\b')
        self.highlighting_rules.append((operator_pattern, self.formats['operator']))
        
        # F-strings (formatted string literals)
        f_string_pattern = QRegExp(r"f['\"][^'\"\\]*(\\.[^'\"\\]*)*['\"]")
        self.highlighting_rules.append((f_string_pattern, self.formats['f_string']))
        
        # Raw strings
        raw_string_pattern = QRegExp(r"r['\"][^'\"\\]*(\\.[^'\"\\]*)*['\"]")
        self.highlighting_rules.append((raw_string_pattern, self.formats['string']))
        
        # String patterns (single and double quotes) - improved
        string_format = self.formats['string']
        
        # Single quoted strings (better regex)
        single_quote_pattern = QRegExp(r"'(?:[^'\\\r\n]|\\.)*'")
        self.highlighting_rules.append((single_quote_pattern, string_format))
        
        # Double quoted strings (better regex)
        double_quote_pattern = QRegExp(r'"(?:[^"\\\r\n]|\\.)*"')
        self.highlighting_rules.append((double_quote_pattern, string_format))
        
        # Triple quoted strings (multiline)
        triple_single_pattern = QRegExp(r"'''.*'''")
        triple_single_pattern.setMinimal(True)
        self.highlighting_rules.append((triple_single_pattern, string_format))
        
        triple_double_pattern = QRegExp(r'""".*"""')
        triple_double_pattern.setMinimal(True)
        self.highlighting_rules.append((triple_double_pattern, string_format))
        
        # Special Flow Comments (Start Flow / End Flow) - Bold and Bright Teal
        # Enhanced pattern to catch variations and ensure entire line is highlighted
        flow_comment_pattern = QRegExp(r'#\s*(Start Flow|End Flow).*$')
        self.highlighting_rules.append((flow_comment_pattern, self.formats['flow_comment']))
        
        # Regular Comments (after flow comments to avoid conflicts)
        comment_pattern = QRegExp(r'#[^\r\n]*')
        self.highlighting_rules.append((comment_pattern, self.formats['comment']))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given text block"""
        # Apply all highlighting rules
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        
        # Handle multiline strings
        self.setCurrentBlockState(0)
        
        # Triple quoted strings
        triple_single = QRegExp(r"'''")
        triple_double = QRegExp(r'"""')
        
        # Check for start of multiline string
        if self.previousBlockState() != 1:
            start_index_single = triple_single.indexIn(text)
            start_index_double = triple_double.indexIn(text)
            
            if start_index_single >= 0:
                self.handle_multiline_string(text, triple_single, 1, self.formats['string'])
            elif start_index_double >= 0:
                self.handle_multiline_string(text, triple_double, 2, self.formats['string'])
        else:
            # Continue multiline string from previous block
            if self.previousBlockState() == 1:
                self.handle_multiline_string(text, triple_single, 1, self.formats['string'])
            elif self.previousBlockState() == 2:
                self.handle_multiline_string(text, triple_double, 2, self.formats['string'])
    
    def handle_multiline_string(self, text, delimiter, state, format):
        """Handle multiline string highlighting"""
        if self.previousBlockState() == state:
            start_index = 0
            add = 0
        else:
            start_index = delimiter.indexIn(text)
            add = delimiter.matchedLength()
        
        while start_index >= 0:
            end_index = delimiter.indexIn(text, start_index + add)
            if end_index == -1:
                self.setCurrentBlockState(state)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + delimiter.matchedLength()
            
            self.setFormat(start_index, comment_length, format)
            start_index = delimiter.indexIn(text, start_index + comment_length)
