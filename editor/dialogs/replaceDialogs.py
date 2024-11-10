# editor/dialogs/replaceDialogs.py
from PySide2.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox, QFrame
from PySide2.QtGui import QTextCursor, QColor, QPainter, QPainterPath, QBrush
from PySide2.QtCore import Qt, QPropertyAnimation, QEasingCurve

class ReplaceDialogs(QDialog):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setWindowTitle("Replace Word")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 80)  # Dikey olarak daraltıldı
        self.is_dragging = False  # Taşıma durumu

        # Seçili kelimeyi kontrol et; yoksa pencereyi kapat
        self.selected_text = editor.textCursor().selectedText()
        if not self.selected_text:
            editor.get_main_window().status_bar.showMessage("Please select a code first", 5000)
            self.reject()  # Seçim yoksa pencereyi kapat
            return

        # Ana çerçeve
        main_frame = QFrame(self)
        main_frame.setObjectName("main_frame")
        main_frame.setStyleSheet("""
            #main_frame {
                background-color: rgba(48, 48, 48, 230); 
                border: 1px solid rgba(255, 255, 255, 0.3); 
                border-radius: 15px;
            }
        """)
        main_frame.setFixedSize(self.width(), self.height())

        # Layout
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(10, 0, 10, 0)

        # Yeni kelime giriş kutusu en üstte
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Enter replacement")
        self.replace_input.setFixedWidth(220)
        self.replace_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #FFFFFF;
                padding-left: 10px;
                border: none;
                font-size: 13px;
            }
        """)
        self.replace_input.textChanged.connect(self.update_button_state)  # Giriş değiştikçe buton durumunu güncelle
        layout.addWidget(self.replace_input)

        # Alt layout: Seçenekler ve butonlar
        bottom_layout = QHBoxLayout()
        layout.addLayout(bottom_layout)

        # Değiştirilecek kelime bilgisi
        label = QLabel(f"Replace: '{self.selected_text}'", self)
        label.setStyleSheet("color: #FFFFFF; font-size: 13px;")
        bottom_layout.addWidget(label)

        # Sadece seçili alan seçeneği, varsayılan olarak aktif
        self.selection_only_checkbox = QCheckBox("Only in selection", self)
        self.selection_only_checkbox.setChecked(True)
        self.selection_only_checkbox.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        bottom_layout.addWidget(self.selection_only_checkbox)

        # Replace butonu (başlangıçta devre dışı)
        self.replace_button = QPushButton("Replace", self)
        self.replace_button.setEnabled(False)  # Başlangıçta devre dışı
        self.replace_button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #808080;
                padding: 5px;
                font-size: 13px;
                border-radius: 8px;
            }
            QPushButton:disabled {
                background-color: #555555;  # Devre dışıyken daha koyu bir renk
            }
            QPushButton:hover:enabled {
                background-color: #6e6e6e;
            }
        """)
        self.replace_button.clicked.connect(self.perform_replace)
        bottom_layout.addWidget(self.replace_button)

        # Sağ üst köşede kapatma butonu
        close_button = QPushButton("X", self)
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                color: rgba(204, 204, 204, 0.8);
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #FF6666;
            }
        """)
        close_button.clicked.connect(self.reject)
        bottom_layout.addWidget(close_button, alignment=Qt.AlignRight)

        # Animasyonlu açılma
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(400)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_animation.start()

        # Diyalog konumunu ayarla
        self.move_below_cursor()

    def update_button_state(self):
        """Replace butonunu etkinleştir veya devre dışı bırak"""
        self.replace_button.setEnabled(bool(self.replace_input.text().strip()))

    def move_below_cursor(self):
        """Diyaloğu düzenleyicideki imleç pozisyonunun altında gösterir."""
        current_editor = self.editor
        if current_editor:
            cursor_rect = current_editor.cursorRect()
            editor_global_pos = current_editor.mapToGlobal(cursor_rect.bottomLeft())
            self.move(editor_global_pos.x(), editor_global_pos.y() + 10)

    def perform_replace(self):
        """Kelimeyi tüm belgede veya seçili alanda değiştirir."""
        new_word = self.replace_input.text()
        if not new_word:
            QMessageBox.warning(self, "Warning", "Please enter the new word.")
            return

        document = self.editor.document()
        cursor = QTextCursor(document)
        cursor.beginEditBlock()

        if self.selection_only_checkbox.isChecked():
            selected_text = self.editor.textCursor().selectedText()
            new_text = selected_text.replace(self.selected_text, new_word)
            self.editor.textCursor().insertText(new_text)
        else:
            text = self.editor.toPlainText()
            new_text = text.replace(self.selected_text, new_word)
            cursor.select(QTextCursor.Document)
            cursor.insertText(new_text)

        cursor.endEditBlock()
        self.accept()  # İşlem tamamlandıktan sonra pencereyi kapat

    def mousePressEvent(self, event):
        """Diyaloğun taşınabilmesi için mouse event'leri."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.mouse_offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.mouse_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def paintEvent(self, event):
        """Arka plan ve kenar çizimi."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)
        painter.fillPath(path, QBrush(QColor(51, 51, 51, 230)))
