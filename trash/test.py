from PySide2.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PySide2.QtGui import QFont, QColor, QPainter
from PySide2.QtCore import Qt


class InlineCompleterLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completion_text = ""  # Satır içi tamamlayıcı metin
        self.font = QFont("Arial", 12)
        self.setFont(self.font)
        self.textChanged.connect(self.on_text_changed)  # Yazı değiştiğinde çağrılır

    def on_text_changed(self):
        """Girilen metne göre tahmini tamamlama yap"""
        current_text = self.text().lower()
        suggestions = {"hello": "hello world", "python": "python rocks", "example": "example code"}

        # Metnin tamamlanmış halini göster
        self.completion_text = suggestions.get(current_text, "")
        self.update()  # paintEvent'i tetikleyerek güncelle

    def paintEvent(self, event):
        """QLineEdit'i çiz ve ardından inline tamamlama metnini ekle"""
        super().paintEvent(event)

        # Eğer tamamlayıcı metin varsa ve kullanıcının yazdığı metin onun bir kısmıysa
        if self.completion_text and self.text() in self.completion_text:
            painter = QPainter(self)
            painter.setFont(self.font)
            painter.setPen(QColor(150, 150, 150))  # Gri renk

            # Tamamlama metnini yerleştir
            completion = self.completion_text[len(self.text()):]  # Yalnızca eksik kısmı göster
            rect = self.rect().adjusted(5 + self.fontMetrics().width(self.text()), 0, 0, 0)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, completion)


class SimpleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Satır İçi Tamamlama")
        self.setGeometry(100, 100, 400, 100)

        # QLineEdit ve inline tamamlama ayarları
        self.line_edit = InlineCompleterLineEdit(self)
        self.line_edit.setFont(QFont("Arial", 12))

        # Basit bir dikey düzen
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication([])
    window = SimpleApp()
    window.show()
    app.exec_()
