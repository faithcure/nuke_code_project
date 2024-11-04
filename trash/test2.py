from PySide2.QtWidgets import QApplication, QPlainTextEdit, QCompleter
from PySide2.QtCore import QStringListModel, Qt
import sys

class CompleterTextEdit(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        # Tamamlayıcı için öneri listesini tanımla
        suggestions = ["apple","asdasd" ,"banana", "cherry", "date", "elderberry", "fig", "grape"]

        # QCompleter oluştur ve öneri listesini ekle
        self.completer = QCompleter(suggestions, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)  # Büyük-küçük harf duyarsız hale getir
        self.completer.setWidget(self)  # QCompleter'ı bu widget ile ilişkilendir

        # QPlainTextEdit içinde değişiklik olduğunda QCompleter'ı kontrol et
        self.textChanged.connect(self.show_completer)

    def show_completer(self):
        cursor = self.textCursor()
        cursor.select(cursor.WordUnderCursor)  # İmlecin altındaki kelimeyi seç

        # Seçili kelimeyi al ve QCompleter'da göster
        if cursor.selectedText():
            self.completer.setCompletionPrefix(cursor.selectedText())
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0))  # Tamamlama popup genişliği
            self.completer.complete(rect)  # QCompleter'ı uygun pozisyonda göster
        else:
            self.completer.popup().hide()  # Kelime yoksa QCompleter'ı gizle

app = QApplication(sys.argv)
window = CompleterTextEdit()
window.setWindowTitle("QCompleter Example with QPlainTextEdit")
window.resize(400, 300)
window.show()
sys.exit(app.exec_())
