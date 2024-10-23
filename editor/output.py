from PySide2.QtWidgets import QTextEdit

class OutputWidget(QTextEdit):
    def __init__(self, parent=None):
        super(OutputWidget, self).__init__(parent)
        self.setReadOnly(True)  # Sadece okuma modunda olacak

    def append_output(self, text):
        """Nuke Python çıktısını eklemek için kullanılan fonksiyon."""
        self.append(text)