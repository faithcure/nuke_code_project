import inspect
from PySide2.QtGui import QColor, QPainter, QTextCursor, QFont
from PySide2.QtWidgets import QPlainTextEdit, QListWidget, QListWidgetItem
from PySide2.QtCore import Qt, QPoint
import importlib
import editor.core
import os

try:
    import nuke
except ImportError:
    nuke = None

importlib.reload(editor.core)
from editor.core import CodeEditorSettings, PathFromOS


class InlineGhosting(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.suggestions = self.load_suggestions_from_modules()
        self.usage_count = {key: 0 for key in self.suggestions}  # Komut kullanım sayısını takip eder
        self.ghost_text = ""
        self.accepting_suggestion = False
        self.textChanged.connect(self.update_ghost_text)

        self.node_list_popup = QListWidget(self)
        self.node_list_popup.hide()
        self.node_list_popup.itemClicked.connect(self.insert_selected_node)

    def load_suggestions_from_modules(self):
        suggestions = {}

        if nuke:
            for attr in dir(nuke):
                if not attr.startswith("_"):
                    suggestions[attr] = self.get_completion_text(nuke, attr)

        try:
            import nukescripts
            for attr in dir(nukescripts):
                if not attr.startswith("_"):
                    suggestions[attr] = self.get_completion_text(nukescripts, attr)
        except ImportError:
            pass

        return suggestions

    def get_completion_text(self, module, attr):
        item = getattr(module, attr)
        if inspect.isfunction(item) or inspect.ismethod(item):
            try:
                params = inspect.signature(item).parameters
                param_list = ", ".join(param.name for param in params.values())
                return f"{attr}({param_list})"
            except (ValueError, TypeError):  # Bu hata, bazı modüller için signature alınamazsa çıkar
                # Eğer signature alınamazsa, __doc__ üzerinden bir tahmin yapmaya çalış
                docstring = getattr(item, "__doc__", "")
                if docstring:
                    first_line = docstring.splitlines()[0]
                    return f"{attr}({first_line})"
                else:
                    return f"{attr}()"
        elif isinstance(item, str):
            return f"{attr}('')"
        elif isinstance(item, (int, float)):
            return f"{attr}"
        else:
            return f"{attr}()"

    def update_ghost_text(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        current_word = cursor.selectedText()

        # Öneri listesini kullanım sayısına göre sıralar
        sorted_suggestions = dict(sorted(self.suggestions.items(), key=lambda item: -self.usage_count[item[0]]))

        if current_word and any(current_word.startswith(suggestion) for suggestion in sorted_suggestions):
            self.ghost_text = self.find_suggestion(current_word, sorted_suggestions)
        else:
            self.ghost_text = ""

        self.viewport().update()

    def find_suggestion(self, word, sorted_suggestions):
        """Find a relevant suggestion based on the typed word, including partial matches."""
        for suggestion, completion_text in sorted_suggestions.items():
            if word in suggestion and suggestion != word:
                # Kullanım sayısını arttır
                self.usage_count[suggestion] += 1
                return completion_text[len(word):]
        return ""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.AltModifier and self.ghost_text:
            self.accepting_suggestion = True
            cursor = self.textCursor()
            cursor.insertText(self.ghost_text)
            self.ghost_text = ""
            self.accepting_suggestion = False
            self.viewport().update()
            return

        elif event.key() == Qt.Key_ParenRight:
            cursor = self.textCursor()
            cursor.select(QTextCursor.WordUnderCursor)
            word = cursor.selectedText()

            if word in self.suggestions and callable(getattr(nuke, word, None)):
                cursor.movePosition(QTextCursor.EndOfWord)
                cursor.insertText("()")
                cursor.movePosition(QTextCursor.Left)
                self.setTextCursor(cursor)

                if word == "createNode":
                    self.show_node_list_popup(cursor)
                return

        super().keyPressEvent(event)

    def show_node_list_popup(self, cursor):
        if nuke:
            self.node_list_popup.clear()
            node_classes = [attr for attr in dir(nuke) if "Node" in attr]
            for node in node_classes:
                QListWidgetItem(node, self.node_list_popup)

            cursor_rect = self.cursorRect(cursor)
            popup_position = self.mapToGlobal(cursor_rect.bottomRight())
            self.node_list_popup.move(popup_position + QPoint(0, 2))
            self.node_list_popup.show()

    def insert_selected_node(self, item):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor, 1)
        cursor.insertText(item.text())
        self.node_list_popup.hide()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.ghost_text:
            painter = QPainter(self.viewport())
            painter.setPen(CodeEditorSettings().GHOSTING_COLOR)

            cursor_rect = self.cursorRect(self.textCursor())
            x_offset, y_offset = cursor_rect.x(), cursor_rect.y() + self.fontMetrics().ascent()
            painter.drawText(x_offset, y_offset, self.ghost_text)
            painter.end()
