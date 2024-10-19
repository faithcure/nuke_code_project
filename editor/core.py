import os
from PySide2.QtGui import QColor
class OutputCatcher:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, message):
        self.output_widget.append(message)  # Mesajı Output penceresine ekle

    def flush(self):
        pass  # Gerekirse bir flush metodu eklenebilir, fakat burada gerek yok

class PathFromOS:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_path = os.path.join(self.project_root, 'ui', 'icons')
        self.json_path = os.path.join(self.project_root, 'assets')
        self.nuke_ref_path = os.path.join(self.project_root, 'assets', 'nuke.py')
        self.nukescripts_ref_path = os.path.join(self.project_root, 'assets', 'nukescripts.py')
        self.assets_path = os.path.join(self.project_root, 'assets')

        # Getting dynamic fonts from JetBrains Mono
        self.jet_fonts = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')
        self.jet_fonts_var = os.path.join(self.project_root, 'assets', 'jetBrains','ttf',"variable")

class CodeEditorSettings:
    def __init__(self):
        """Kod yazım ayarları burada döner"""
        # GENEL KODLAMA AYARLARI
        self.main_font_size = 11

        # BACKGROUND COLOR SETTIGS
        self.code_background_color = QColor(45, 45, 45)


        # SOL LINE NUMBER AREA AYARLARI
        self.line_spacing_size = 1.2
        self.line_number_weight = False
        self.line_number_color = QColor(100, 100, 100)
        self.line_number_draw_line = QColor(100, 100, 100)
        self.line_number_background_color = QColor(45, 45, 45)

        # CODE PythonHighlighter SETTINGS
        self.selfColor = QColor(255, 255, 255)