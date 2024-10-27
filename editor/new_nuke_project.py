import os
import re
import zipfile
import importlib

from PySide2.QtGui import QFont, QColor, QPainter, QTextFormat
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QHBoxLayout, QFileDialog, QCheckBox, QPlainTextEdit, QTextEdit
from PySide2.QtCore import Qt, QSize, QRect, QRegExp
from PySide2.QtWidgets import QGraphicsDropShadowEffect
from PySide2.QtGui import QSyntaxHighlighter, QTextCharFormat
import editor.core
importlib.reload(editor.core)

class LineNumberedTextEdit(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        max_number = max(1, self.blockCount())
        while max_number >= 10:
            max_number //= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(75, 75, 74, 150)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

class LineNumberArea(QFrame):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # Renk ve stil kuralları
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#ff79c6"))  # pembe
        keywordFormat.setFontWeight(QFont.Bold)

        nukeFormat = QTextCharFormat()
        nukeFormat.setForeground(QColor("#ffb86c"))  # turuncu

        menuFormat = QTextCharFormat()
        menuFormat.setForeground(QColor("#ffb86c"))  # turuncu

        commandFormat = QTextCharFormat()
        commandFormat.setForeground(QColor("#bbbbbb"))  # gri bold
        commandFormat.setFontWeight(QFont.Bold)

        # Keywords for highlighting
        keywords = ["import", "nuke", "command", "menu", "addCommand"]

        for word in keywords:
            if word == "nuke":
                pattern = QRegExp(r'\bnuke\b')
                self.highlightingRules.append((pattern, nukeFormat))
            elif word == "menu":
                pattern = QRegExp(r'\bmenu\b')
                self.highlightingRules.append((pattern, menuFormat))
            elif word in ["addCommand", "command"]:
                pattern = QRegExp(r'\b' + word + r'\b')
                self.highlightingRules.append((pattern, commandFormat))
            else:
                pattern = QRegExp(r'\b' + word + r'\b')
                self.highlightingRules.append((pattern, keywordFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class NewNukeProjectDialog(QDialog):
    def __init__(self, parent=None, jet_fonts=None):
        super().__init__(parent)
        self.allowed_pattern = r'^[a-zA-Z0-9_ ]+$'
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        dialog_size = QSize(500, 500)
        self.resize(dialog_size)

        # Gölge efekti
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(40)
        shadow_effect.setOffset(0, 12)
        shadow_effect.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow_effect)

        # Ana layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Arka plan çerçevesi
        background_frame = QFrame(self)
        background_frame.setStyleSheet("""QFrame {background-color: rgb(50, 50, 50);border: 1px solid rgba(255, 255, 255, 0.1);border-radius: 9px;}""")
        self.inner_layout = QVBoxLayout(background_frame)
        self.inner_layout.setContentsMargins(30, 30, 30, 20)
        self.main_layout.addWidget(background_frame)

        # Başlık
        title_label = QLabel("Create New Nuke Project", background_frame)
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setStyleSheet("""color: #CFCFCF; font-size: 18px; font-weight: bold; font-family: 'Myriad';border: none;background-color: transparent;""")
        self.inner_layout.addWidget(title_label)

        # Separator çizgisi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        self.inner_layout.addWidget(line)

        # Proje ismi giriş alanı
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter Project Name")
        self.project_name_input.setMaxLength(20)
        self.project_name_input.setStyleSheet("""QLineEdit {background-color: rgba(255, 255, 255, 0.08); color: #E0E0E0; padding: 10px; padding-right: 40px; border: 1px solid #5A5A5A; border-radius: 8px;}""")
        self.inner_layout.addWidget(self.project_name_input)

        # Proje dizini giriş alanı ve "Browse" butonu
        self.project_dir_input = QLineEdit()
        self.project_dir_input.setPlaceholderText("Select Project Directory")
        self.project_dir_input.setText(self.get_default_nuke_directory())
        self.project_dir_input.setStyleSheet("""QLineEdit {background-color: rgba(255, 255, 255, 0.08); color: #E0E0E0; padding: 10px; border: 1px solid #5A5A5A; border-radius: 8px;}""")
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.project_dir_input)
        browse_button = QPushButton("Browse")
        browse_button.setFixedHeight(37)
        browse_button.setStyleSheet("""QPushButton {background-color: #4E4E4E; color: #FFFFFF; border-radius: 8px; padding: 6px 12px; font-size: 12px;} QPushButton:hover {background-color: #6E6E6E;}""")
        browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_button)
        self.inner_layout.addLayout(dir_layout)

        # Çizgi separatorları
        def add_separator():
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
            self.inner_layout.addWidget(line)

        # 1. Create Menu.py
        self.create_menu_py_checkbox = QCheckBox("Create Menu.py")
        self.create_menu_py_checkbox.setStyleSheet("color: #CFCFCF;")
        self.create_menu_py_checkbox.stateChanged.connect(self.toggle_menu_py_textbox)
        self.inner_layout.addWidget(self.create_menu_py_checkbox)

        self.menu_py_textbox = LineNumberedTextEdit()
        self.menu_py_textbox.setStyleSheet(f"""background-color: rgba(255, 255, 255, 0.08);color: #CFCFCF;font-size: 12px;""")
        self.menu_py_textbox.setFont(QFont("Consolas"))
        self.inner_layout.addWidget(self.menu_py_textbox)
        self.menu_py_textbox.hide()  # Initially hidden
        # Add syntax highlighting to menu.py
        self.highlighter_menu = SyntaxHighlighter(self.menu_py_textbox.document())  # Syntax highlighting added

        # 2. Create init.py
        self.create_init_py_checkbox = QCheckBox("Create init.py")
        self.create_init_py_checkbox.setStyleSheet("color: #CFCFCF;")
        self.create_init_py_checkbox.stateChanged.connect(self.toggle_init_py_textbox)
        self.inner_layout.addWidget(self.create_init_py_checkbox)

        self.init_py_textbox = LineNumberedTextEdit()
        self.init_py_textbox.setFont(QFont("Consolas"))
        self.init_py_textbox.setStyleSheet(f"""background-color: rgba(255, 255, 255, 0.08);color: #CFCFCF;font-size: 12px;""")
        self.inner_layout.addWidget(self.init_py_textbox)
        self.init_py_textbox.hide()  # Initially hidden
        # Add syntax highlighting to init.py
        self.highlighter_init = SyntaxHighlighter(self.init_py_textbox.document())  # Syntax highlighting added

        # Çizgi separatoru
        add_separator()

        # 4. Make backup .nuke folder (be safe)
        self.create_backup_folder_checkbox = QCheckBox("Make backup .nuke folder (be safe)")
        self.create_backup_folder_checkbox.setStyleSheet("color: #CFCFCF;")
        self.create_backup_folder_checkbox.stateChanged.connect(self.toggle_backup_location)
        self.inner_layout.addWidget(self.create_backup_folder_checkbox)

        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setPlaceholderText("Select Backup Location")
        self.backup_dir_input.setStyleSheet("""QLineEdit {background-color: rgba(255, 255, 255, 0.08);color: #E0E0E0;padding: 10px;border: 1px solid #5A5A5A;border-radius: 8px;}""")

        # Browse button for .nuke backup location
        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_input)
        self.browse_backup_button = QPushButton("Backup Location")
        self.browse_backup_button.setFixedHeight(37)
        self.browse_backup_button.setFixedWidth(150)  # Daha dar genişlik
        self.browse_backup_button.setStyleSheet("""QPushButton {background-color: #4E4E4E;color: #FFFFFF;border-radius: 8px;padding: 6px 12px;font-size: 12px;} QPushButton:hover {background-color: #6E6E6E;}""")
        self.browse_backup_button.clicked.connect(self.browse_backup_directory)
        backup_dir_layout.addWidget(self.browse_backup_button)
        self.inner_layout.addLayout(backup_dir_layout)

        # Backup ile ilgili açıklama
        self.backup_explanation = QLabel("If you have an existing .nuke environment, backing it up \nwill make your work easier.")
        self.backup_explanation.setStyleSheet("color: #CFCFCF; font-size: 12px; stroke: none; border: none;")
        self.inner_layout.addWidget(self.backup_explanation)
        self.backup_explanation.hide()

        self.backup_dir_input.hide()
        self.browse_backup_button.hide()

        # OK ve Cancel butonları
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.setStyleSheet("""QPushButton {background-color: #808080;color: #FFFFFF;border-radius: 10px;font-size: 14px;padding: 5px;} QPushButton:hover {background-color: #A9A9A9;}""")
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(80, 30)
        cancel_button.setStyleSheet("""QPushButton {background-color: #808080;color: #FFFFFF;border-radius: 10px;font-size: 14px;padding: 5px;} QPushButton:hover {background-color: #A9A9A9;}""")
        button_layout.addWidget(cancel_button)

        self.inner_layout.addSpacing(20)
        self.inner_layout.addLayout(button_layout)

        ok_button.clicked.connect(self.create_project)
        cancel_button.clicked.connect(self.reject)

    def toggle_menu_py_textbox(self, state):
        if state == Qt.Checked:
            self.menu_py_textbox.show()
            self.menu_py_textbox.setPlainText("import nuke\ntoolbar = nuke.menu(\'Nodes\')\ni = toolbar.addMenu('Studio')")
        else:
            self.menu_py_textbox.hide()
            self.menu_py_textbox.clear()

    def toggle_init_py_textbox(self, state):
        if state == Qt.Checked:
            self.init_py_textbox.show()
            self.init_py_textbox.setPlainText("import nuke\nimport os\nnuke.pluginAddPath('your_plugin_path')")
        else:
            self.init_py_textbox.hide()
            self.init_py_textbox.clear()

    def toggle_backup_location(self, state):
        if state == Qt.Checked:
            self.backup_dir_input.show()
            self.browse_backup_button.show()
            self.backup_explanation.show()  # Backup açıklamasını göster
            self.backup_dir_input.setText("")
        else:
            self.backup_dir_input.hide()
            self.browse_backup_button.hide()
            self.backup_explanation.hide()  # Backup açıklamasını gizle

    def get_default_nuke_directory(self):
        """İşletim sistemine göre .nuke dizinini döndürür."""
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".nuke")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if directory:
            self.project_dir_input.setText(directory)

    def browse_backup_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if directory:
            self.backup_dir_input.setText(directory)

    def create_project(self):
        project_name = self.project_name_input.text()
        project_dir = self.project_dir_input.text()

        if not project_name or not project_dir:
            return  # Proje adı ve dizini doğrulama eklenebilir

        if self.create_backup_folder_checkbox.isChecked():
            backup_dir = self.backup_dir_input.text()
            if backup_dir:
                nuke_dir = self.get_default_nuke_directory()
                backup_zip = os.path.join(backup_dir, "nuke_backup.zip")
                with zipfile.ZipFile(backup_zip, 'w') as zf:
                    for root, dirs, files in os.walk(nuke_dir):
                        for file in files:
                            zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), nuke_dir))

        if self.create_menu_py_checkbox.isChecked():
            menu_py_content = self.menu_py_textbox.toPlainText()
            with open(os.path.join(project_dir, "menu.py"), 'w') as f:
                f.write(menu_py_content)

        if self.create_init_py_checkbox.isChecked():
            init_py_content = self.init_py_textbox.toPlainText()
            with open(os.path.join(project_dir, "init.py"), 'w') as f:
                f.write(init_py_content)

        os.makedirs(project_dir, exist_ok=True)
        self.accept()