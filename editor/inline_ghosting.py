from PySide2.QtGui import QColor, QPainter, QTextCursor, QFont
from PySide2.QtWidgets import QPlainTextEdit
from PySide2.QtCore import Qt
import importlib
import editor.core

try:
    import nuke  # Attempt to import the nuke module
except ImportError:
    nuke = None  # If not found, set nuke to None

importlib.reload(editor.core)
from editor.core import CodeEditorSettings, PathFromOS

class InlineGhosting(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suggestions = self.load_suggestions_from_modules()  # Suggestions from `nuke` and `nukescripts` only
        self.ghost_text = ""
        self.textChanged.connect(self.update_ghost_text)

    def load_suggestions_from_modules(self):
        """Load class and function names from `nuke` and `nukescripts` modules."""
        suggestions = []

        # Add all items from the `nuke` module if available
        if nuke:
            suggestions.extend([attr for attr in dir(nuke) if not attr.startswith("_")])

        # If nukescripts is available, add its items similarly
        try:
            import nukescripts
            suggestions.extend([attr for attr in dir(nukescripts) if not attr.startswith("_")])
        except ImportError:
            pass

        return suggestions

    def set_suggestions(self, new_suggestions):
        """Dynamically update the suggestion list."""
        self.suggestions = new_suggestions

    def update_ghost_text(self):
        """Update inline ghost suggestion based on the current word."""
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        current_word = cursor.selectedText()

        # Suggestion based only on keywords from `nuke` or `nukescripts`
        if current_word and any(current_word.startswith(suggestion) for suggestion in self.suggestions):
            self.ghost_text = self.find_suggestion(current_word)
        else:
            self.ghost_text = ""

        self.viewport().update()  # Trigger a repaint for ghost text

    def find_suggestion(self, word):
        """Find a relevant suggestion based on the typed word."""
        for suggestion in self.suggestions:
            if suggestion.startswith(word) and suggestion != word:
                return suggestion[len(word):]  # Return the missing part of the suggestion
        return ""

    def keyPressEvent(self, event):
        """Accept suggestion with Alt + Enter."""
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.AltModifier and self.ghost_text:
            # Insert the ghost text suggestion at the cursor
            cursor = self.textCursor()
            cursor.insertText(self.ghost_text)
            self.ghost_text = ""
            self.viewport().update()  # Refresh to clear ghost text
            return  # Stop event propagation for Alt + Enter
        else:
            super().keyPressEvent(event)  # Default behavior for other keys

    def paintEvent(self, event):
        """Custom paintEvent to display ghost text."""
        super().paintEvent(event)
        if self.ghost_text:
            painter = QPainter(self.viewport())
            painter.setPen(CodeEditorSettings().GHOSTING_COLOR)  # Color for ghost text

            cursor_rect = self.cursorRect(self.textCursor())
            x_offset, y_offset = cursor_rect.x(), cursor_rect.y() + self.fontMetrics().ascent()
            painter.drawText(x_offset, y_offset, self.ghost_text)
            painter.end()
