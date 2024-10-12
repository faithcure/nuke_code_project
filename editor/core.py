from PySide2.QtCore import Qt, QRegExp, QSize
from PySide2.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PySide2.QtWidgets import *


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Monokai Renk Paleti
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#F92672"))  # Pembe/Kırmızı (keywords)
        keyword_format.setFontWeight(QFont.Bold)

        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#66D9EF"))  # Açık Mavi (sınıf isimleri)

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#A6E22E"))  # Açık Yeşil (fonksiyon isimleri)

        special_method_format = QTextCharFormat()
        special_method_format.setForeground(QColor("#AE81FF"))  # Mor (özel metodlar)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#E6DB74"))  # Sarı (stringler)

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#75715E"))  # Gri (yorumlar)

        docstring_format = QTextCharFormat()
        docstring_format.setForeground(QColor("#A6E22E"))  # Yeşil (docstringler)

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#AE81FF"))  # Mor (sayısal değerler)

        # Anahtar kelimeler
        keywords = [
            "class", "def", "if", "else", "elif", "while", "for", "in", "try", "except", "finally",
            "return", "yield", "break", "continue", "pass", "import", "from", "as", "with", "raise",
            "assert", "async", "await"
        ]
        for word in keywords:
            pattern = QRegExp(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # Sınıf isimleri
        class_name_pattern = QRegExp(r'\bclass\s+(\w+)')
        self.highlighting_rules.append((class_name_pattern, class_format))

        # Fonksiyon isimleri
        function_name_pattern = QRegExp(r'\bdef\s+(\w+)')
        self.highlighting_rules.append((function_name_pattern, function_format))

        # Özel metodlar
        special_methods = [
            "__init__", "__str__", "__repr__", "__call__", "__len__", "__getitem__", "__setitem__", "__delitem__"
        ]
        for method in special_methods:
            pattern = QRegExp(f"\\b{method}\\b")
            self.highlighting_rules.append((pattern, special_method_format))

        # Stringler
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("\'.*\''"), string_format))

        # Yorumlar
        self.highlighting_rules.append((QRegExp("#[^\n]*"), comment_format))

        # Docstring
        self.highlighting_rules.append((QRegExp("\"\"\".*\"\"\"", Qt.CaseInsensitive), docstring_format))
        self.highlighting_rules.append((QRegExp("\'\'\'.*\'\'\'", Qt.CaseInsensitive), docstring_format))

        # Sayısal değerler
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))

    def highlightBlock(self, text):
        """Her bir metin bloğunu renklendiren fonksiyon."""
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class OutputCatcher:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, message):
        self.output_widget.append(message)  # Mesajı Output penceresine ekle

    def flush(self):
        pass  # Gerekirse bir flush metodu eklenebilir, fakat burada gerek yok
