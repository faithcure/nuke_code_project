import jedi
from PySide2.QtWidgets import *
from PySide2.QtGui import QIcon, QFont, QBrush, QColor, QSyntaxHighlighter, QTextCharFormat, QPainter, QTextFormat, QTextCursor, QGuiApplication
from PySide2.QtCore import Qt, QEvent, QRegExp, QStringListModel, QSize, QRect
from core import LineNumberArea


class CodeEditor(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.cursorPositionChanged.connect(self.highlight_current_word)
        self.cursorPositionChanged.connect(self.update_cursor_position)  # Cursor pozisyonu güncelleme
        self.blockCountChanged.connect(self.update_line_and_character_count)  # Satır sayısı güncellenince
        self.textChanged.connect(self.update_line_and_character_count)  # Karakter değişikliklerinde
        self.cursorPositionChanged.connect(self.update_line_and_character_count)  # İmleç pozisyonu değişince
        self.update_line_number_area_width(0)

        # QCompleter oluştur
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setWidget(self)

        # Dinamik olarak güncellenecek model
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.completer.popup().installEventFilter(self)  # Event filter ekleme

        # İmleç pozisyonuna göre tamamlama popup'ını göster
        self.textChanged.connect(self.show_completer)

        # Completer'den bir öneri seçildiğinde, insert_completion fonksiyonunu çağır.
        self.completer.activated.connect(self.insert_completion)

    def eventFilter(self, obj, event):
        if obj == self.completer.popup():
            if event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self.insert_completion(self.completer.currentCompletion())
                    self.completer.popup().hide()
                    return True
                elif event.key() == Qt.Key_Escape:
                    self.completer.popup().hide()
                    return True
                else:
                    self.setFocus()
                    self.keyPressEvent(event)
                    return True
            return False
        return super().eventFilter(obj, event)

    def show_completer(self):
        """Tamamlama popup'ını göster"""
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        current_code = self.toPlainText()
        line, col = cursor.blockNumber() + 1, cursor.columnNumber()

        if len(cursor.selectedText()) > 0:
            script = jedi.Script(current_code)
            try:
                completions = script.complete(line, col)
            except Exception:
                completions = []

            if completions:
                completion_list = [comp.name for comp in completions]
                self.model.setStringList(completion_list)

                rect = self.cursorRect()
                rect.setX(rect.x() + 35)
                rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 100)

                opacity_effect = QGraphicsOpacityEffect(self.completer.popup())
                opacity_effect.setOpacity(0.9)
                self.completer.popup().setGraphicsEffect(opacity_effect)

                self.completer.complete(rect)
                self.setFocus()  # Odağı editöre geri ver
            else:
                self.completer.popup().hide()
        else:
            self.completer.popup().hide()

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        # Ctrl+Enter kombinasyonu ile kod çalıştırma
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            main_window = self.get_main_window()
            if main_window:
                selected_text = cursor.selectedText()  # Seçili metni al
                if selected_text:
                    main_window.run_selected_code(selected_text)  # Eğer seçili metin varsa sadece onu çalıştır
                else:
                    main_window.run_code()  # Seçili metin yoksa tüm kodu çalıştır
            return  # Varsayılan davranışı engellemek için return ekliyoruz

        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            main_window = self.get_main_window()
            if main_window:
                main_window.show_search_dialog()
            return

            # Diğer tuş işlemleri için varsayılan davranış


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
            self.show_completer()  # Her tuş basımında tamamlayıcıyı güncelle

    def insert_completion(self, completion_text):
        """Seçilen öğeyi imleç pozisyonuna ekle"""
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(completion_text + ' ')
        self.setTextCursor(cursor)
        self.completer.popup().hide()

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
        pen = painter.pen()
        pen.setColor(QColor("#C0C0C0"))
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
        space = 20 + self.fontMetrics().horizontalAdvance('9') * digits
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
        painter.fillRect(event.rect(), QColor(77, 77, 77))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width(), self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1