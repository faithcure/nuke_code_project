from PySide2.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QLabel, QFrame, QPushButton, QTextEdit
from PySide2.QtGui import QColor, QPixmap, QTextCursor, QTextCharFormat, QPainter, QPainterPath, QBrush, QIcon
from PySide2.QtCore import Qt, QEasingCurve, QPropertyAnimation, QTimer
import os
from editor.core import PathFromOS


class SearchDialog(QDialog):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.matches = []
        self.current_match_index = -1

        # Çerçevesiz ve başlıksız yapmak için dialog ayarları
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 60)

        # Ana çerçeve, dialog etrafında daha hafif beyaz bir stroke olacak
        main_frame = QFrame(self)
        main_frame.setObjectName("main_frame")
        main_frame.setStyleSheet("""
            #main_frame {
                background-color: rgba(48, 48, 48, 230); 
                border: 1px solid rgba(255, 255, 255, 0.3); /* Hafif beyaz stroke */
                border-radius: 15px; /* Daha oval kenarlar */
            }
        """)
        main_frame.setFixedSize(self.width(), self.height())

        # İçerik layout'u
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(10, 0, 10, 0)

        # Sağ üst köşede kapatma butonu
        close_button = QPushButton("X", self)
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                color: rgba(204, 204, 204, 0.8); /* Saydam gri */
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #FF6666;
            }
        """)
        close_button.clicked.connect(self.reject)  # Kapatma işlemi
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        # Arama ikonu
        search_icon = QLabel(self)
        search_icon.setPixmap(
            QPixmap(os.path.join(PathFromOS().icons_path, "find.svg")).scaled(20, 20, Qt.KeepAspectRatio))
        search_icon.setStyleSheet("opacity: 0.7;")  # İkon saydamlığı
        layout.addWidget(search_icon)

        # Arama kutusu
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFrame(False)
        self.search_input.setFixedHeight(25)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #FFFFFF;
                padding-left: 10px;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)

        # Sonuç sayısını gösteren etiket
        self.result_count_label = QLabel("0 Matches")
        self.result_count_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        layout.addWidget(self.result_count_label)

        # Yukarı ve aşağı butonları yan yana yerleştirme
        nav_layout = QHBoxLayout()
        self.up_button = QPushButton(self)
        self.down_button = QPushButton(self)
        self.up_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, "scroll_top_icon.svg")))
        self.down_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, "scroll_down_icon.svg")))

        for btn in (self.up_button, self.down_button):
            btn.setFlat(True)
            btn.setFixedSize(30, 30)
            btn.clicked.connect(self.navigate_matches)
            btn.setStyleSheet("opacity: 0.7;")  # İkon saydamlığı
            nav_layout.addWidget(btn)

        layout.addLayout(nav_layout)

        # Açılma animasyonu
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(400)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_animation.start()

        # Dialog konumunu ayarla
        self.move_below_cursor()

    def move_below_cursor(self):
        """Arama dialogunu düzenleyicideki kod satırının hemen altında gösterir."""
        current_editor = self.main_window.tab_widget.currentWidget()
        if current_editor:
            cursor_rect = current_editor.cursorRect()
            editor_global_pos = current_editor.mapToGlobal(cursor_rect.bottomLeft())
            self.move(editor_global_pos.x(), editor_global_pos.y())

    def on_search_text_changed(self):
        """Arama kutusuna yazı girildikçe eşleşme sayısını günceller."""
        search_term = self.search_input.text().strip()
        match_count = self.find_and_highlight(search_term) if search_term else 0
        self.result_count_label.setText(f"{match_count} Matches")

    def on_search_clicked(self):
        """Arama işlemini başlatır."""
        search_term = self.search_input.text().strip()
        match_count = self.find_and_highlight(search_term) if search_term else 0
        self.result_count_label.setText(f"{match_count} Matches")
        self.accept()

    def find_and_highlight(self, search_term):
        """Kod düzenleyicide arama terimiyle eşleşen kelimeleri vurgular ve eşleşme sayısını döner."""
        current_editor = self.main_window.tab_widget.currentWidget()
        if current_editor is None:
            return 0

        cursor = current_editor.textCursor()
        document = current_editor.document()
        current_editor.setExtraSelections([])

        self.matches.clear()
        extra_selections = []
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)

        match_count = 0
        while not cursor.isNull() and not cursor.atEnd():
            cursor = document.find(search_term, cursor)
            if not cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = self.get_transparent_highlight()
                extra_selections.append(selection)
                self.matches.append(cursor.blockNumber() + 1)  # Satır numarasını kaydet
                match_count += 1

        cursor.endEditBlock()
        current_editor.setExtraSelections(extra_selections)
        return match_count

    def get_transparent_highlight(self):
        """Saydam, pastel turuncu vurgulama formatı."""
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 180, 100, 80))  # Çok saydam pastel turuncu
        return highlight_format

    def navigate_matches(self):
        """Bulunan sonuçlar arasında yukarı ve aşağı geçiş yapar ve gidilen satırı parlak şekilde gösterir."""
        sender = self.sender()
        if sender == self.up_button:
            self.current_match_index = (self.current_match_index - 1) % len(self.matches)
        elif sender == self.down_button:
            self.current_match_index = (self.current_match_index + 1) % len(self.matches)

        # İlgili satıra git ve parlak göster
        if self.current_match_index != -1 and self.matches:
            editor = self.main_window.tab_widget.currentWidget()
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, self.matches[self.current_match_index] - 1)
            editor.setTextCursor(cursor)
            self.flash_current_line(editor)

    def flash_current_line(self, editor):
        """Gidilen satırı parlak bir renkle geçici olarak gösterir."""
        extra_selection = QTextEdit.ExtraSelection()
        extra_selection.format.setBackground(QColor(255, 230, 100, 150))  # Parlak renk
        extra_selection.cursor = editor.textCursor()
        editor.setExtraSelections([extra_selection])

        # Parlaklığı azaltan animasyon
        QTimer.singleShot(300, lambda: self.dim_highlight(extra_selection, editor))

    def dim_highlight(self, selection, editor):
        """Seçimin parlaklığını düşürür."""
        selection.format.setBackground(QColor(255, 180, 100, 80))
        editor.setExtraSelections([selection])

    def paintEvent(self, event):
        """Dialog arka plan ve kenar için özel çerçeve tasarımı."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)  # Kenarları daha oval
        painter.fillPath(path, QBrush(QColor(51, 51, 51, 230)))
