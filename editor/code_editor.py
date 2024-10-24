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
from editor.core import CodeEditorSettings
from editor.core import PathFromOS
importlib.reload(editor.completer)
from editor.completer import Completer
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor

class CodeEditor(QPlainTextEdit):
    def __init__(self, *args):
        super(CodeEditor, self).__init__(*args)
        self.setup_fonts()
        self.set_background_color()
        self.completer = Completer(self)  # Completer sınıfını başlatıyoruz
        self.setWordWrapMode(QTextOption.NoWrap)
        self.set_line_spacing(CodeEditorSettings().line_spacing_size)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.highlight_current_word)
        self.cursorPositionChanged.connect(self.update_cursor_position)  # Cursor pozisyonu güncelleme
        self.blockCountChanged.connect(self.update_line_and_character_count)  # Satır sayısı güncellenince
        self.textChanged.connect(self.update_line_and_character_count)  # Karakter değişikliklerinde
        self.cursorPositionChanged.connect(self.update_line_and_character_count)  # İmleç pozisyonu değişince
        self.textChanged.connect(self.handle_text_change)  # Her yazımda tetiklenecek
        self.update_line_number_area_width(0)

    def handle_text_change(self):
        """Yazarken tamamlayıcıyı her harf değişiminde tetikleme"""
        self.completer.update_completions()

    def set_background_color(self):
        """Kod panelinin arkaplan rengini ayarlar"""
        # QPalette oluştur
        palette = self.palette()
        # QPalette ile arka plan rengini QPalette.Base kısmına uygula
        palette.setColor(QPalette.Base, CodeEditorSettings().code_background_color)
        # Arka plan rengini uygula
        self.setPalette(palette)

    def setup_fonts(self):
        # core.py'deki font yollarını almak için PathFromOS kullanıyoruz
        jetbrains_mono_path = os.path.join(PathFromOS().jet_fonts, "JetBrainsMono-Regular.ttf")

        # JetBrains Mono fontunu yükleyelim
        font_id = QFontDatabase.addApplicationFont(jetbrains_mono_path)

        if font_id == -1:
            print("JetBrains Mono fontu yüklenemedi!")
        else:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                # print(f"Yüklenen font ailesi: {font_families[0]}")
                self.setFont(QFont(font_families[0], CodeEditorSettings().main_font_size))  # JetBrains Mono'yu 12 boyutunda ayarla
            else:
                print("Font ailesi bulunamadı!")

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
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
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

        # Ctrl+Enter kombinasyonu ile kod çalıştırma
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            main_window = self.get_main_window()
            if main_window:
                selected_text = cursor.selectedText()  # Seçili metni al
                if selected_text:
                    main_window.run_selected_code(selected_text)  # Eğer seçili metin varsa sadece onu çalıştır
                else:
                    pass
                    #main_window.run_code()  # Seçili metin yoksa tüm kodu çalıştır
            return  # Varsayılan davranışı engellemek için return ekliyoruz

        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            main_window = self.get_main_window()
            if main_window:
                main_window.show_search_dialog()
            return

        # Eğer Ctrl+H kombinasyonuna basıldıysa replace diyalogunu aç
        if event.key() == Qt.Key_H and event.modifiers() == Qt.ControlModifier:
            main_window = self.get_main_window()
            if main_window:
                main_window.trigger_replace_in_active_editor()
            return

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
        replace_action = QAction("Replace All", self)
        replace_action.setShortcut("Ctrl+H")  # Kısa yol atama
        replace_action.triggered.connect(self.replace_selected_word)  # Replace All fonksiyonunu bağla
        menu.addAction(replace_action)

        # Menüyü göster
        menu.exec_(event.globalPos())

    def replace_selected_word(self):
        selected_text = self.textCursor().selectedText()

        if not selected_text:
            self.get_main_window().status_bar.showMessage("Lütfen değiştirmek istediğiniz kelimeyi seçin.", 5000)
            return

        # Yeni kelimeyi almak için diyalog kutusu açıyoruz
        new_word, ok = QInputDialog.getText(self, "Replace All", f"{selected_text} kelimesini değiştirin:")

        if ok and new_word:  # Kullanıcı "Tamam" demişse ve yeni kelime varsa
            document = self.document()
            cursor = QTextCursor(document)
            cursor.beginEditBlock()  # Toplu işlem başlat

            # Belge metnini alıyoruz
            text = self.toPlainText()

            # Seçili kelimeyi tüm belgede değiştiriyoruz
            new_text = text.replace(selected_text, new_word)

            # Tüm belgeyi seçip yeni metni yerleştiriyoruz
            cursor.select(QTextCursor.Document)
            cursor.insertText(new_text)

            cursor.endEditBlock()  # Toplu işlem sonlandır

            # Başarı mesajı
            self.get_main_window().status_bar.showMessage(
                f"Tüm '{selected_text}' kelimeleri '{new_word}' ile değiştirildi.", 5000
            )

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

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        self.load_syntax_colors()

    def load_syntax_colors(self):
        # JSON dosyasını yükle
        with open(os.path.join(PathFromOS().json_path, "syntax_color.json"), 'r') as file:
            syntax_data = json.load(file)
        colors = syntax_data["colors"]

        # Anahtar kelimeler için renklendirme kuralı
        self.add_highlighting_rule(syntax_data["keywords"], colors["keywords"])

        # Diğer kategoriler için kurallar
        self.add_highlighting_rule(syntax_data["built_in_functions"], colors["built_in_functions"])
        self.add_highlighting_rule(syntax_data["built_in_constants"], colors["built_in_constants"])
        self.add_highlighting_rule(syntax_data["built_in_types"], colors["built_in_types"])
        self.add_highlighting_rule(syntax_data["special_methods"], colors["special_methods"], special_method=True)
        self.add_highlighting_rule(syntax_data["decorators_gold"], colors["decorators_gold"])
        self.add_highlighting_rule(syntax_data["exceptions"], colors["exceptions"])
        self.add_highlighting_rule(syntax_data["modules"], colors["modules"])
        self.add_highlighting_rule(syntax_data["nukescripts"], colors["nukescripts"])
        self.add_highlighting_rule(syntax_data["coroutines"], colors["coroutines"])
        self.add_highlighting_rule(syntax_data["context_managers"], colors["context_managers"])
        self.add_highlighting_rule(syntax_data["type_hints"], colors["type_hints"])

        # Fonksiyon isimleri için renklendirme kuralı
        self.add_function_name_rule(colors["function_names"])  # Fonksiyon adı için renk

        # Yorumlar, docstringler, stringler ve sayılar için kurallar
        self.add_regex_rule(QRegExp("#[^\n]*"), colors["comments"])  # Yorumlar
        self.add_regex_rule(QRegExp("\"\"\".*\"\"\"", Qt.CaseInsensitive), colors["docstrings"])  # Docstring
        self.add_regex_rule(QRegExp("\'\'\'.*\'\'\'", Qt.CaseInsensitive), colors["docstrings"])  # Docstring
        self.add_regex_rule(QRegExp("\".*\""), colors["strings"])  # Stringler
        self.add_regex_rule(QRegExp("\'.*\'"), colors["strings"])  # Stringler
        self.add_regex_rule(QRegExp("\\b[0-9]+\\b"), colors["numbers"])  # Sayılar

        # `@` ile başlayan dekoratörler için renklendirme kuralı (altın sarısı)
        self.add_regex_rule(QRegExp(r"@\w+"), colors["decorators_gold"])  # Altın sarısı dekoratörler

    def add_highlighting_rule(self, items, color, special_method=False):
        """Her kategori için renklendirme kuralını ekler"""
        format = QTextCharFormat()
        format.setForeground(QColor(color))

        for item in items:
            pattern = QRegExp(f"\\b{item}\\b")
            self.highlighting_rules.append((pattern, format))

    def add_regex_rule(self, pattern, color):
        """Regex tabanlı renklendirme kuralı ekler"""
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        self.highlighting_rules.append((pattern, format))

    def add_function_name_rule(self, color):
        """Fonksiyon adları için renklendirme kuralı ekler"""
        format = QTextCharFormat()
        format.setForeground(QColor(color))

        # Fonksiyon adını yakalamak için regex deseni: `def`'den sonra gelen ismi yakalar
        self.function_name_format = QTextCharFormat()
        self.function_name_format.setForeground(QColor(color))

    def highlightBlock(self, text):
        """Her bir metin bloğunu renklendiren fonksiyon"""
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        # `def` anahtar kelimesinden sonra gelen fonksiyon ismini renklendirme
        function_pattern = QRegExp(r'\bdef\s+(\w+)')
        function_index = function_pattern.indexIn(text)
        if function_index >= 0:
            function_name = function_pattern.cap(1)  # Fonksiyon ismini yakala
            function_name_start = function_pattern.pos(1)  # Fonksiyon isminin başladığı pozisyonu al
            self.setFormat(function_name_start, len(function_name), self.function_name_format)  # Fonksiyon ismini renklendir
