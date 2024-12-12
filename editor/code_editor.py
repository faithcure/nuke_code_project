import importlib
import json
import os
from PySide2.QtCore import QRect
from PySide2.QtCore import QRegExp
from PySide2.QtCore import QSize
from PySide2.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter, QPen
from PySide2.QtGui import QFont, QPalette, QTextOption
from PySide2.QtGui import QPainter, QTextFormat, QFontDatabase, QTextBlockFormat
from PySide2.QtWidgets import *
import editor.completer
import editor.inline_ghosting
import nodes.crtNode
import editor.dialogs.replaceDialogs
from editor.core import CodeEditorSettings
import settings.settings_ui
from editor.completer import Completer
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor
from editor.inline_ghosting import InlineGhosting
from init_ide import settings_path
from nodes.crtNode import createNodeCompleter

importlib.reload(editor.completer)
importlib.reload(editor.inline_ghosting)
importlib.reload(nodes.crtNode)
importlib.reload(editor.dialogs.replaceDialogs)
importlib.reload(settings.settings_ui)

from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Number, Operator, Text, Generic, Literal, Punctuation
from editor.dialogs.replaceDialogs import ReplaceDialogs
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

class CodeEditor(InlineGhosting):
    def __init__(self, editor_window=None, *args):
        super().__init__(*args)
        self.editor_window = editor_window  # Store a reference to the EditorApp instance
        self.font_size = CodeEditorSettings().main_font_size  # Default font size
        self.ctrl_wheel_enabled = CodeEditorSettings().ctrlWheel  # Control + Wheel feature check
        self.setup_fonts()
        self.set_background_color()
        self.completer = Completer(self)  # Initialize Completer
        self.setWordWrapMode(QTextOption.NoWrap)
        self.set_line_spacing(CodeEditorSettings().line_spacing_size)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.highlight_current_word)
        self.cursorPositionChanged.connect(self.update_cursor_position)
        self.blockCountChanged.connect(self.update_line_and_character_count)
        self.textChanged.connect(self.update_line_and_character_count)
        self.cursorPositionChanged.connect(self.update_line_and_character_count)
        self.textChanged.connect(self.handle_text_change)
        self.update_line_number_area_width(0)
        self.highlighter = PygmentsHighlighter(self.document())  # Highlighter'ı bağla
        # `createNodeCompleter` nesnesini oluştur
        self.createNodeCompleter = createNodeCompleter(self)

        # `textChanged` sinyalini `createNodeCompleter` ile bağla
        self.textChanged.connect(self.createNodeCompleter.check_for_create_node)

    def handle_text_change(self):
        """Yazarken tamamlayıcıyı her harf değişiminde tetikleme"""
        self.completer.update_completions()

        # Inline ghosting ayarını kontrol et
        if CodeEditorSettings().ENABLE_INLINE_GHOSTING:
            self.update_ghost_text()  # inline ghost text özelliğini tetikle
        else:
            self.ghost_text = ""  # Ghost text özelliği kapalıysa boş bırak
            self.viewport().update()  # Görüntüyü güncelle

    def set_background_color(self):
        """Kod panelinin arkaplan rengini ayarlar"""
        # QPalette oluştur
        palette = self.palette()
        # QPalette ile arka plan rengini QPalette.Base kısmına uygula
        palette.setColor(QPalette.Base, CodeEditorSettings().code_background_color)
        # Arka plan rengini uygula
        self.setPalette(palette)

    def setup_fonts(self):
        # JSON'dan font bilgilerini yükle

        default_font = CodeEditorSettings().main_default_font  # Ayar dosyasındaki font ismi
        default_font_size = CodeEditorSettings().main_font_size  # Ayar dosyasındaki font boyutu

        self.setFont(QFont(default_font, default_font_size))  # Fontu ayarla
        print (default_font, default_font_size, "font info")


    def wheelEvent(self, event):
        """Adjust font size with CTRL + Wheel"""
        if self.ctrl_wheel_enabled and event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.font_size += 1
            elif event.angleDelta().y() < 0 and self.font_size > 1:
                self.font_size -= 1

            # Update font size in the editor
            font = self.font()
            font.setPointSize(self.font_size)
            self.setFont(font)

            # Update the font size display in EditorApp's status bar
            if self.editor_window:
                self.editor_window.font_size_label.setText(f"Font Size: {self.font_size} | ")

            event.accept()
        else:
            # Call the default wheel event if CTRL + Wheel is not enabled
            super().wheelEvent(event)

    def set_line_spacing(self, line_spacing_factor):
        # TextCursor ve TextBlockFormat kullanarak satır aralığını ayarlıyoruz
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)  # Tüm belgeyi seçiyoruz
        block_format = QTextBlockFormat()
        block_format.setLineHeight(line_spacing_factor * 100, QTextBlockFormat.ProportionalHeight)
        cursor.mergeBlockFormat(block_format)
        self.setTextCursor(cursor)  # Yeni formatı uyguluyoruz

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        # Eğer tamamlama popup'ı açık ise Enter/Return tuşunu popup ile kullanmak
        if self.completer.completion_popup.popup().isVisible():
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Seçilen öneriyi al
                selected_index = self.completer.completion_popup.popup().currentIndex()
                if selected_index.isValid():
                    selected_completion = self.completer.completion_popup.popup().model().data(selected_index)
                    if selected_completion:
                        self.completer.insert_completion(selected_completion)
                        self.completer.completion_popup.popup().hide()  # Tamamlama yapıldıktan sonra popup'ı gizle
                return  # Tamamlama işlemi tamamlandığında varsayılan işlevi atla

            elif event.key() in (Qt.Key_Up, Qt.Key_Down):
                # Eğer yukarı/aşağı ok tuşuna basılmışsa popup'ta gezinme işlemini yap
                self.completer.completion_popup.popup().keyPressEvent(event)
                return  # Varsayılan davranışı atla

        # Otomatik kapanan karakterler için kontrol
        if event.key() in (Qt.Key_ParenLeft, Qt.Key_BraceLeft, Qt.Key_BracketLeft,
                           Qt.Key_QuoteDbl, Qt.Key_Apostrophe):
            pairs = {
                Qt.Key_ParenLeft: ('(', ')'),
                Qt.Key_BraceLeft: ('{', '}'),
                Qt.Key_BracketLeft: ('[', ']'),
                Qt.Key_QuoteDbl: ('"', '"'),
                Qt.Key_Apostrophe: ("'", "'"),
            }
            opening, closing = pairs[event.key()]
            cursor.insertText(opening + closing)
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)

        # Kapanış karakterleri üzerinde gezinme
        elif event.key() in (Qt.Key_ParenRight, Qt.Key_BraceRight, Qt.Key_BracketRight,
                             Qt.Key_QuoteDbl, Qt.Key_Apostrophe):
            current_char = self.document().characterAt(cursor.position())
            closing_chars = {
                Qt.Key_ParenRight: ')',
                Qt.Key_BraceRight: '}',
                Qt.Key_BracketRight: ']',
                Qt.Key_QuoteDbl: '"',
                Qt.Key_Apostrophe: "'",
            }
            if current_char == closing_chars[event.key()]:
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
            else:
                super().keyPressEvent(event)

        # Shift+Tab ile girintiyi azalt
        elif event.key() == Qt.Key_Backtab:
            cursor.beginEditBlock()

            block = cursor.block()
            text = block.text()
            indentation_level = len(text) - len(text.lstrip())

            if indentation_level >= 4:
                cursor.movePosition(QTextCursor.StartOfBlock)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                cursor.removeSelectedText()

            cursor.endEditBlock()

        elif event.key() == Qt.Key_Tab:
            cursor.insertText(' ' * 4)

        elif event.key() == Qt.Key_Return:
            block = cursor.block()
            text = block.text()
            indentation = text[:len(text) - len(text.lstrip())]

            if text.strip().endswith(':'):
                indentation += ' ' * 4
            super().keyPressEvent(event)
            cursor.insertText(indentation)

        else:
            super().keyPressEvent(event)

    def update_line_and_character_count(self):
        """Update the total number of characters in the status bar, along with cursor position."""
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        total_characters = len(self.toPlainText())

        main_window = self.get_main_window()
        if main_window:
            main_window.status_bar.showMessage(f"{line}:{column} | Characters: {total_characters}")

    def get_main_window(self):
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        return parent

    def contextMenuEvent(self, event):
        # Varsayılan bağlam menüsünü oluştur
        menu = self.createStandardContextMenu()

        # Search seçeneği oluştur
        search_action = QAction("Search", self)
        search_action.setShortcut("Ctrl+F")  # Kısa yol atama

        # Ana pencereyi al ve arama diyalogunu bağla
        main_window = self.get_main_window()
        if main_window:
            search_action.triggered.connect(
                main_window.show_search_dialog)  # Ana pencereye ait arama diyalogunu açmak için bağla
        menu.addAction(search_action)  # Menüye ekle

        # Replace All seçeneği
        replace_action = QAction("Replace", self)
        replace_action.triggered.connect(
            lambda: ReplaceDialogs(self).show()
            if self.textCursor().selectedText().strip()
            else self.get_main_window().status_bar.showMessage("Please select the text you want to replace.", 5000)
        )

        menu.addAction(replace_action)
        # Menüyü göster
        menu.exec_(event.globalPos())

    def get_main_window(self):
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        return parent

    def highlight_current_word(self):
        extra_selections = []
        selected_text = self.textCursor().selectedText()

        if selected_text and len(selected_text) >= 2:
            document = self.document()
            cursor = QTextCursor(document)
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(125, 81, 0))

            while not cursor.isNull() and not cursor.atEnd():
                cursor = document.find(selected_text, cursor)
                if not cursor.isNull():
                    selection = QTextEdit.ExtraSelection()
                    selection.cursor = cursor
                    selection.format = highlight_format
                    extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def update_cursor_position(self):
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1

        main_window = self.get_main_window()
        if main_window:
            main_window.status_bar.showMessage(f"{line}:{column}")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())

        pen = QPen(QColor(CodeEditorSettings().intender_color))
        pen.setWidth(CodeEditorSettings().intender_width)  # Çizgi kalınlığını buradan ayarlayabilirsiniz (örnek: 2 piksel)
        painter.setPen(pen)

        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                text = block.text()
                indentation_level = len(text) - len(text.lstrip())
                font_metrics = self.fontMetrics()
                char_width = font_metrics.horizontalAdvance(' ')

                for i in range(1, (indentation_level // 4) + 1):
                    x = i * 4 * char_width
                    painter.drawLine(x, top, x, bottom)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

        painter.end()

    def line_number_area_width(self):
        digits = len(str(self.blockCount()))
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits +10
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(77, 77, 77)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), CodeEditorSettings().line_number_background_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        font = painter.font()
        font.setBold(CodeEditorSettings().line_number_weight)
        font.setPointSize(CodeEditorSettings().main_font_size)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                text = block.text().strip()

                # Satırın "def" veya "class" ile başlayıp başlamadığını kontrol ediyoruz
                if text.startswith('def ') or text.startswith('class '):
                    painter.setPen(CodeEditorSettings().line_number_color)
                    # Satır numarasının sağ tarafına ">" sembolü ekliyoruz
                    painter.drawText(5, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                     Qt.AlignLeft, number + u" \u2192")
                else:
                    # Diğer satırlara sadece numara yaz
                    painter.setPen(CodeEditorSettings().line_number_color)
                    painter.drawText(5, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                     Qt.AlignLeft, number)

            # Bir sonraki bloğa geçerken block_number'ı arttır
            block_number += 1
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(CodeEditorSettings().line_number_draw_line)
        painter.drawLine(self.line_number_area.width() - 1, event.rect().top(), self.line_number_area.width() - 1,
                         event.rect().bottom())

    def mousePressEvent(self, event):
        """Satır numarası alanına tıklama kontrolü ve satır renklendirme"""
        super().mousePressEvent(event)  # Önce varsayılan işlemi çağır

        # Tıklanan satırın rengini değiştir
        self.highlight_clicked_line()

    def highlight_clicked_line(self):
        """Tıklanan satırı transparan arka plan rengiyle vurgula"""
        cursor = self.textCursor()  # İmleç pozisyonunu al
        selection = QTextEdit.ExtraSelection()

        # Transparan arka plan rengi ayarlama
        line_color = CodeEditorSettings().clicked_line_color
        selection.format.setBackground(line_color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)

        selection.cursor = cursor
        selection.cursor.clearSelection()

        # Mevcut renklendirmeleri temizle
        extraSelections = self.extraSelections()

        # Diğer renklendirmeleri kontrol et ve temizle
        extraSelections = [sel for sel in extraSelections if sel.format.background() != line_color]

        # Yeni renklendirme ekle
        extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class PyCharmDarkStyle(Style):
    """
    PyCharm Dark theme adapted for Pygments.
    """
    default_style = ""
    background_color = "#1e1f22"  # Background
    highlight_color = "#26282e"  # Caret row color

    styles = {
        # Genel Yapılar
        Text: '#bcbec4',  # Plain text
        Text.Whitespace: '#6f737a',  # Whitespace
        Text.Highlight: 'bg:#26282e',  # Highlighted text
        Error: 'bold bg:#ff5640',  # Errors (bold red background)

        # Yorumlar
        Comment: 'italic #7a7e85',  # Comments
        Comment.Multiline: 'italic #7a7e85',  # Multiline comments
        Comment.Preproc: 'italic #7a7e85',  # Preprocessor comments
        Comment.Special: 'italic bold #6f737a',  # Special comments like TODO or FIXME

        # Anahtar Kelimeler
        Keyword: 'bold #cf8e6d',  # Keywords
        Keyword.Constant: 'bold #cf8e6d',  # Constant keywords (e.g., True, False, None)
        Keyword.Declaration: 'bold #cf8e6d',  # Declaration keywords (e.g., class, def)
        Keyword.Namespace: 'bold #cf8e6d',  # Namespace keywords (e.g., import, from)
        Keyword.Pseudo: 'italic #cf8e6d',  # Pseudo keywords (e.g., self, cls)

        # İsimler ve Fonksiyonlar
        Name: '#bcbec4',  # General names
        Name.Builtin: '#c77dbb',  # Built-in names (e.g., print, len)
        Name.Function: '#57aaf7',  # Function names
        Name.Class: 'bold #bcbec4',  # Class names
        Name.Decorator: '#fa7db1',  # Decorators (e.g., @staticmethod)
        Name.Exception: 'bold #ff5640',  # Exception names (e.g., ValueError)
        Name.Variable: '#bcbec4',  # General variables
        Name.Variable.Global: 'italic #bcbec4',  # Global variables
        Name.Variable.Instance: 'italic #bcbec4',  # Instance variables
        Name.Attribute: '#A9B7C6',  # Attributes (e.g., object.property)
        Name.Tag: 'bold #d5b778',  # Tags (e.g., HTML/XML tags)

        # Stringler
        String: '#A9B7C6',  # Strings
        String.Interpol: '#A9B7C6',  # Interpolated strings (e.g., f-strings)
        String.Escape: '#c77dbb',  # String escape sequences
        String.Doc: 'italic #6A8759',  # Docstring

        # Sayılar ve Operatörler
        Number: '#2aacb8',  # Numbers
        Operator: '#bcbec4',  # Operators
        Operator.Word: 'bold #cf8e6d',  # Operators as words (e.g., and, or, not)
        Punctuation: '#bcbec4',  # Punctuation (e.g., commas, colons)

        # Generic Yapılar
        Generic.Deleted: 'bg:#402929',  # Deleted text
        Generic.Inserted: 'bg:#3d7a49',  # Inserted text
        Generic.Heading: 'bold #bcbec4',  # Headings
        Generic.Subheading: 'bold #bcbec4',  # Subheadings
        Generic.Error: 'bg:#fa6675 #FFFFFF',  # Errors
        Generic.Emph: 'italic',  # Emphasis
        Generic.Strong: 'bold',  # Strong emphasis
        Generic.Prompt: '#bcbec4',  # Prompts
        Generic.Output: '#bcbec4',  # Output text
        Generic.Traceback: '#f75464',  # Tracebacks

        # HTML, XML ve JSON için Ek Renkler
        Name.Tag: 'bold #d5b778',  # Tags
        Name.Attribute: '#A9B7C6',  # Attributes
        String.Double: '#A9B7C6',  # Double-quoted strings
        String.Single: '#A9B7C6',  # Single-quoted strings
        String.Symbol: '#A9B7C6',  # Symbols within strings

        # CSS ve JavaScript Renkleri
        Name.Property: '#fa7db1',  # CSS properties
        Name.Label: '#d5b778',  # Labels in code
        Name.Constant: '#c77dbb',  # Constants
        String.Regex: '#57aaf7',  # Regular expressions
        Keyword.Type: 'italic #c77dbb',  # Type-related keywords (e.g., int, str)
    }


class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        # Settings dosyasını yükle
        style = "monokai"  # Varsayılan stil
        # Settings.json'dan style'ı oku
        try:
            with open(settings_path, "r") as settings_file:
                settings = json.load(settings_file)
                style = settings.get("General", {}).get("syntax_style_dropdown", style)
                print("Code Style: ",style)
        except FileNotFoundError:
            print(f"Settings file not found at {settings_path}. Using default style: {style}.")
        except json.JSONDecodeError:
            print(f"Settings file is not a valid JSON. Using default style: {style}.")
        super().__init__(document)

        # Formatter ve lexer ayarla
        self.formatter = HtmlFormatter(style=style)
        self.lexer = PythonLexer()
        self.token_styles = self._generate_token_styles()

    def _generate_token_styles(self):
        """Pygments token stillerini PyQt formatına çevir."""
        token_styles = {}
        for token, style in self.formatter.style:
            text_format = QTextCharFormat()

            if style['color']:
                text_format.setForeground(QColor(f"#{style['color']}"))
            if style['bold']:
                text_format.setFontWeight(QFont.Bold)
            if style['italic']:
                text_format.setFontItalic(True)

            token_styles[token] = text_format
        return token_styles

    def highlightBlock(self, text):
        """Metni token'lara böl ve stilleri uygula."""
        tokens = self.lexer.get_tokens(text)
        for token_type, token_value in tokens:
            if token_type in self.token_styles:
                start_index = text.find(token_value)
                while start_index != -1:
                    length = len(token_value)
                    self.setFormat(start_index, length, self.token_styles[token_type])
                    start_index = text.find(token_value, start_index + length)