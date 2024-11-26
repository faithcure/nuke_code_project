import os
from PySide2.QtCore import QSize
from PySide2.QtGui import QColor, Qt
import json
from init_ide import settings_path

def load_nuke_function_descriptions(json_path):
    """Nuke işlev açıklamalarını JSON'dan yükler."""
    with open(json_path, "r") as file:
        data = json.load(file)
    return {func["name"]: func["doc"] for func in data}

class PathFromOS:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_path = os.path.join(self.project_root, 'ui', 'icons')
        self.json_path = os.path.join(self.project_root, 'assets')
        self.json_dynamic_path = os.path.join(self.project_root, 'assets', 'dynamic_data')
        self.nuke_ref_path = os.path.join(self.project_root, 'assets', 'nuke.py')
        self.nukescripts_ref_path = os.path.join(self.project_root, 'assets', 'nukescripts.py')
        self.assets_path = os.path.join(self.project_root, 'assets')

        # Gettings dynamic path settings
        self.settings_db = os.path.join(self.project_root, 'editor', 'settings')

        # Getting dynamic fonts from JetBrains Mono
        self.jet_fonts = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')
        self.jet_fonts_var = os.path.join(self.project_root, 'assets', 'jetBrains','ttf',"variable")
        self.jet_fonts_italic = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')

class CodeEditorSettings:
    def __init__(self):
        """Kod yazım ayarları burada döner"""

        # TEMP CODES
        self.temp_codes = ("# -*- coding: utf-8 -*-\n"
                           "#import love")

        # GENEL KODLAMA AYARLARI
        self.main_font_size = 11 # Default font size
        self.ctrlWheel = True # Ctrl Whell Zoom Settings Default!

        # BACKGROUND COLOR SETTIGS
        self.code_background_color = QColor(45, 45, 45)

        # SOL LINE NUMBER AREA AYARLARI
        self.line_spacing_size = 1.2
        self.line_number_weight = False
        self.line_number_color = QColor(100, 100, 100)
        self.line_number_draw_line = QColor(100, 100, 100)
        self.line_number_background_color = QColor(45, 45, 45)

        # Intender Color
        inteder_line_onOff = 250
        self.intender_color = QColor(62, 62, 62, inteder_line_onOff)
        self.intender_width = 1.5

        # Satır renklendirme ayarları
        line_opacity = 50
        self.clicked_line_color = QColor(75, 75, 75, line_opacity)

        # TOOLBAR settings
        self.setToolbar_area = Qt.TopToolBarArea
        tb_icon_sizeX= 20
        tb_icon_sizeY= 20
        self.toolbar_icon_size = QSize(tb_icon_sizeX,tb_icon_sizeY)

        # COMPLETER SETTINGS
        self.ENABLE_FUZZY_COMPLETION = True # Fuzzy filter ON/OFF
        self.ENABLE_COMPLETER = True  # Completer varsayılan olarak açık
        self.ENABLE_INLINE_GHOSTING = True # Inline suggestion ON/OFF
        self.GHOSTING_OPACITY = 100
        self.GHOSTING_COLOR = QColor(175, 175, 175, self.GHOSTING_OPACITY) # Inline Color settings.
        self.CREATE_NODE_COMPLETER = True # Sadece createNode ile çalışır.

        # TEMP UI SETTINGS DONT TOUCH
        self.OUTLINER_DOCK_POS = Qt.LeftDockWidgetArea
        self.HEADER_DOCK_POS = Qt.LeftDockWidgetArea
        self.WORKPLACE_DOCK_POS = Qt.RightDockWidgetArea
        self.OUTPUT_DOCK_POS = Qt.BottomDockWidgetArea
        self.CONSOLE_DOCK_POS = Qt.BottomDockWidgetArea
        self.NUKEAI_DOCK_POS = Qt.BottomDockWidgetArea

        self.OUTLINER_VISIBLE = True
        self.HEADER_VISIBLE = True
        self.WORKPLACE_VISIBLE = True
        self.OUTPUT_VISIBLE = True
        self.CONSOLE_VISIBLE = True
        self.NUKEAI_VISIBLE = True

        def set_focus_mode():
            self.OUTLINER_VISIBLE = False
            self.HEADER_VISIBLE = False
            self.WORKPLACE_VISIBLE = False
            self.OUTPUT_VISIBLE = False
            self.CONSOLE_VISIBLE = False
            self.NUKEAI_VISIBLE = False

        def set_default_mode():
            self.OUTLINER_VISIBLE = True
            self.HEADER_VISIBLE = True
            self.WORKPLACE_VISIBLE = True
            self.OUTPUT_VISIBLE = True
            self.CONSOLE_VISIBLE = True
            self.NUKEAI_VISIBLE = True


        # JSON dosyasını oku
        with open(settings_path) as file:
            data = json.load(file)

        interface_mode = data.get("General", {}).get("default_interface_mode", "")

        if interface_mode == "Mumen Rider (Professional)":
            set_default_mode()

        elif interface_mode == "Saitama (immersive)":
            set_focus_mode()


