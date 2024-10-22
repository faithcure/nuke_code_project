# -*- coding: utf-8 -*-
import sys
from PySide2.QtWidgets import QTextEdit


class OutputCatcher:
    def __init__(self, output_text_edit: QTextEdit):
        self.output_text_edit = output_text_edit

    def write(self, message):
        self.output_text_edit.append(message)

    def flush(self):
        pass  # `flush` methodu sys.stdout için gerekli olduğundan boş bırakıyoruz.


class OutputManager:
    def __init__(self, output_text_edit: QTextEdit):
        self.output_text_edit = output_text_edit
        self.output_text_edit.setReadOnly(True)

    def clear_output(self):
        """Output penceresini temizlemek için kullanılır."""
        self.output_text_edit.clear()

    def capture_output(self):
        """Output penceresinde standart ve hata çıktısını yakalamak için kullanılır."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = OutputCatcher(self.output_text_edit)
        sys.stderr = OutputCatcher(self.output_text_edit)
        return old_stdout, old_stderr

    def restore_output(self, old_stdout, old_stderr):
        """Çıktıyı eski stdout ve stderr'e geri döndürür."""
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def append_output(self, message):
        """Output penceresine manuel mesaj eklemek için kullanılır."""
        self.output_text_edit.append(message)
