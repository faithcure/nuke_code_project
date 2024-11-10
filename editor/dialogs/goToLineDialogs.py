from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QHBoxLayout
from PySide2.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide2.QtGui import QPainter, QPainterPath, QBrush, QColor, QTextCursor

class GoToLineDialog(QDialog):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setWindowTitle("Go To Line:Column")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 120)

        # Ana Çerçeve
        main_frame = QFrame(self)
        main_frame.setObjectName("main_frame")
        main_frame.setStyleSheet("""
            #main_frame {
                background-color: rgba(48, 48, 48, 230); 
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
            }
        """)
        main_frame.setFixedSize(self.width(), self.height())

        # Ana Layout
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(20, 10, 20, 10)

        # Satır ve Sütun Açıklamaları İçin Layout
        label_layout = QHBoxLayout()

        # Satır ve Sütun Açıklamaları
        line_label = QLabel("Line:", self)
        line_label.setStyleSheet("color: #CCCCCC; font-size: 10px;")
        label_layout.addWidget(line_label, alignment=Qt.AlignCenter)

        column_label = QLabel("Column:", self)
        column_label.setStyleSheet("color: #CCCCCC; font-size: 10px;")
        label_layout.addWidget(column_label, alignment=Qt.AlignCenter)

        # Label Layout'u Ana Layout'a Ekleyin
        layout.addLayout(label_layout)

        # Satır ve Sütun Numarası İçin Girdi Alanları ve OK Butonu
        input_layout = QHBoxLayout()

        # Mevcut Satır ve Sütun Numarasını Al
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1

        # Satır Numarası Girişi
        self.line_input = QLineEdit(self)
        self.line_input.setText(str(line))
        self.line_input.setFixedSize(80, 30)
        self.line_input.setStyleSheet("""
            QLineEdit {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border-radius: 5px;
                padding-left: 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;  /* Hafif yeşil stroke */
            }
        """)
        input_layout.addWidget(self.line_input)

        # İki Nokta Arası Simge
        colon_label = QLabel(":", self)
        colon_label.setStyleSheet("color: #CCCCCC; font-size: 16px;")
        input_layout.addWidget(colon_label, alignment=Qt.AlignCenter)

        # Sütun Numarası Girişi
        self.column_input = QLineEdit(self)
        self.column_input.setText(str(column))
        self.column_input.setFixedSize(80, 30)
        self.column_input.setStyleSheet("""
            QLineEdit {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border-radius: 5px;
                padding-left: 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;  /* Hafif yeşil stroke */
            }
        """)
        input_layout.addWidget(self.column_input)

        # OK Butonu
        ok_button = QPushButton("OK", self)
        ok_button.setFixedSize(60, 30)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #5A5A5A;
                color: #FFFFFF;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6A6A6A;
            }
        """)
        ok_button.clicked.connect(self.on_ok_button_clicked)
        input_layout.addWidget(ok_button)

        # Girdi Alanlarını ve OK Butonunu Layout'a Ekleyin
        layout.addLayout(input_layout)

        # Açılma Animasyonu
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_animation.start()

    def on_ok_button_clicked(self):
        """Girilen satır ve sütun numarasına gitme işlemini başlatır."""
        line_text = self.line_input.text()
        column_text = self.column_input.text()
        if line_text.isdigit() and column_text.isdigit():
            line_number = int(line_text)
            column_number = int(column_text)
            self.go_to_line_column(line_number, column_number)
            self.accept()  # Diyaloğu kapatır

    def go_to_line_column(self, line_number, column_number):
        """İmleci belirtilen satır ve sütuna taşır."""
        editor = self.editor
        if editor:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)
            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, column_number - 1)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()

    def paintEvent(self, event):
        """Arka plan ve kenar çizimi."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QBrush(QColor(48, 48, 48, 230)))
