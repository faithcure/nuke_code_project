import os
from PySide2.QtCore import QSize
from PySide2.QtGui import QColor, Qt
import json


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

        # Getting dynamic fonts from JetBrains Mono
        self.jet_fonts = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')
        self.jet_fonts_var = os.path.join(self.project_root, 'assets', 'jetBrains','ttf',"variable")
        self.jet_fonts_italic = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')

class CodeEditorSettings:
    def __init__(self):
        """Kod yazım ayarları burada döner"""

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

        # UI / UX SETTINGS
        self.ui_layout = {
            "main_window": {
                "default_width": 1024,
                "default_height": 768,
                "min_width": 800,
                "min_height": 600
            },
            "docks": {
                "workplace_dock": Qt.RightDockWidgetArea,
                "outliner_dock": Qt.LeftDockWidgetArea,
                "header_dock": Qt.LeftDockWidgetArea,
                "console_dock": Qt.BottomDockWidgetArea,
                "nuke_ai_dock": Qt.BottomDockWidgetArea,
                "output_dock": Qt.BottomDockWidgetArea
            },
            "dock_styles": {
                "tabify_docks": True,  # Default olarak dockları sekmeli yap
                "default_tab_order": ["console_dock", "output_dock", "nuke_ai_dock"],  # Sekme sırası
                "tab_highlight_color": QColor(50, 50, 50),
                "tab_text_color": QColor(200, 200, 200),
            },
            "toolbar": {
                "default_position": Qt.TopToolBarArea,
                "movable": True,
                "icon_spacing": 4,
                "icon_size": QSize(25, 25),
            },
            "menus": {
                "file_menu": True,  # File menüsü açık
                "edit_menu": True,  # Edit menüsü açık
                "view_menu": True,  # View menüsü açık
                "custom_menus": [
                    {"name": "Mode Switcher", "items": ["Default Mode", "Compact Mode", "Focus Mode", "Expanded Mode"]}
                ]
            },
        }

        # DOCK POSITION OVERRIDES
        self.override_dock_positions = {
            "compact_mode": {
                "all_tabs_at_bottom": True,  # Compact mode'da tüm paneller aşağıda sekmeli olur
            },
            "expanded_mode": {
                "console_dock": Qt.BottomDockWidgetArea,
                "output_dock": Qt.BottomDockWidgetArea,
                "nuke_ai_dock": Qt.BottomDockWidgetArea,
                "workplace_dock": Qt.RightDockWidgetArea,
                "outliner_dock": Qt.LeftDockWidgetArea,
                "header_dock": Qt.LeftDockWidgetArea,
            },
        }