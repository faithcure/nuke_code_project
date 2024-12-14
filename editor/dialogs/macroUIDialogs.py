import nuke
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import os

class MacroPanelBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.icon_path = os.path.join(os.path.dirname(__file__), "icons")
        self.setWindowTitle("Nuke Panel Builder")
        self.resize(1400, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.create_tool_bar()
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.create_left_panel()
        self.create_right_panel()
        self.main_layout.addWidget(self.content_splitter)
        self.create_status_bar()

    def create_tool_bar(self):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Generate Code ikonu
        generate_icon_path = os.path.join(self.icon_path, "run-icon.svg")
        generate_action = toolbar.addAction(QIcon(generate_icon_path), "Generate Python Code")
        generate_action.triggered.connect(self.generate_code)

        # Clear Codes ikonu
        clear_icon_path = os.path.join(self.icon_path, "clear-codes-icon.svg")
        clear_action = toolbar.addAction(QIcon(clear_icon_path), "Clear Codes")
        clear_action.triggered.connect(self.clear_codes)

    def create_left_panel(self):
        left_dock = QDockWidget("Widget Box", self)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Knobs Tree
        self.knobs_tree = QTreeWidget()
        self.knobs_tree.setHeaderHidden(True)
        self.knobs_tree.setIconSize(QSize(16, 16))
        self.populate_knobs_tree(self.knobs_tree)
        left_layout.addWidget(self.knobs_tree)

        # Filtre paneli
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)

        filter_top_layout = QHBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by name...")
        filter_top_layout.addWidget(self.filter_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All Types", "Input", "Color", "Transform", "File", "Container", "Custom"])
        filter_top_layout.addWidget(self.type_combo)
        filter_layout.addLayout(filter_top_layout)

        # Knob Preview Paneli
        self.knob_preview_group = QGroupBox()
        self.knob_preview_layout = QVBoxLayout()

        self.knob_preview_label = QLabel()
        self.knob_preview_label.setAlignment(Qt.AlignCenter)
        self.knob_preview_layout.addWidget(self.knob_preview_label)

        self.knob_preview_name_label = QLabel()
        self.knob_preview_name_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self.knob_preview_layout.addWidget(self.knob_preview_name_label)

        self.knob_preview_type_label = QLabel()
        self.knob_preview_layout.addWidget(self.knob_preview_type_label)

        self.knob_preview_group.setLayout(self.knob_preview_layout)
        filter_layout.addWidget(self.knob_preview_group)

        # Filtre bağlantıları
        self.filter_edit.textChanged.connect(self.apply_filters)
        self.type_combo.currentTextChanged.connect(self.apply_filters)

        left_layout.addWidget(filter_widget)

        left_widget.setLayout(left_layout)
        left_dock.setWidget(left_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)

    def apply_filters(self):
        filter_text = self.filter_edit.text().lower()
        type_filter = self.type_combo.currentText()

        root = self.knobs_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_visible = False

            if type_filter == "All Types" or category_item.text(0) == type_filter:
                for j in range(category_item.childCount()):
                    knob_item = category_item.child(j)
                    knob_visible = filter_text in knob_item.text(0).lower()
                    knob_item.setHidden(not knob_visible)
                    if knob_visible:
                        category_visible = True

            category_item.setHidden(not category_visible)

    def create_right_panel(self):
        right_dock = QDockWidget("Properties", self)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Property Editor
        property_table = QTableWidget()
        property_table.setColumnCount(2)
        property_table.setHorizontalHeaderLabels(["Property", "Value"])
        right_layout.addWidget(property_table)

        # Output Panel
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        output_layout.addWidget(output_text)
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)

        right_widget.setLayout(right_layout)
        right_dock.setWidget(right_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)

    def create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")

    def populate_knobs_tree(self, tree):
        right_arrow = os.path.join(self.icon_path, "right-arrow.svg").replace("\\", "/")
        down_arrow = os.path.join(self.icon_path, "down-arrow.svg").replace("\\", "/")

        try:
            import nuke
            all_knob_types = nuke.knobTypes()
        except:
            all_knob_types = {
                "Basic Input": {
                    "icon": "basic_input",
                    "knobs": [
                        ("String_Knob", "string_knob"),
                        ("Int_Knob", "number_knob"),
                        ("Double_Knob", "number_knob"),
                        ("Boolean_Knob", "button_knob"),
                        ("Password_Knob", "string_knob"),
                        ("Text_Knob", "string_knob"),
                        ("Multiline_Eval_String_Knob", "string_knob")
                    ]
                },
                "Color & Transform": {
                    "icon": "color_transform",
                    "knobs": [
                        ("Color_Knob", "color_knob"),
                        ("AColor_Knob", "color_knob"),
                        ("XY_Knob", "transform_knob"),
                        ("XYZ_Knob", "transform_knob"),
                        ("UV_Knob", "transform_knob"),
                        ("WH_Knob", "transform_knob"),
                        ("Box3_Knob", "transform_knob"),
                        ("Scale_Knob", "transform_knob"),
                        ("Format_Knob", "transform_knob")
                    ]
                },
                "Array & Vector": {
                    "icon": "array_vector",
                    "knobs": [
                        ("Array_Knob", "array_vector"),
                        ("BBox_Knob", "array_vector"),
                        ("ColorChip_Knob", "color_knob"),
                        ("Channel_Knob", "array_vector"),
                        ("ChannelMask_Knob", "array_vector"),
                        ("Link_Knob", "array_vector")
                    ]
                },
                "Button & Menu": {
                    "icon": "button_knob",
                    "knobs": [
                        ("PyScript_Knob", "button_knob"),
                        ("PyCustom_Knob", "button_knob"),
                        ("Enumeration_Knob", "button_knob"),
                        ("Pulldown_Knob", "button_knob"),
                        ("Radio_Knob", "button_knob"),
                        ("Button_Knob", "button_knob")
                    ]
                }
            }

        tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #2d2d2d;
                border: none;
                color: #e0e0e0;
            }}
            QTreeWidget::item {{
                padding: 4px;
                border: none;
            }}
            QTreeWidget::item:hover {{
                background-color: #3d3d3d;
            }}
            QTreeWidget::item:selected {{
                background-color: #4b4b4b;
            }}
            QTreeView::branch {{
                background: transparent;
                border: none;
            }}
            QTreeView::branch:has-siblings {{
                border-image: none;
                background: transparent;
            }}
            QTreeView::branch:has-siblings:adjoins-item {{
                border-image: none;
                background: transparent;
            }}
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: url({right_arrow});
            }}
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {{
                border-image: none;
                image: url({down_arrow});
            }}
        """)

        tree.setRootIsDecorated(True)
        tree.setExpandsOnDoubleClick(True)

        for category, data in all_knob_types.items():
            category_item = QTreeWidgetItem(tree)
            category_item.setText(0, category)
            category_icon_path = self.get_icon_path(data["icon"])
            category_item.setIcon(0, QIcon(category_icon_path))

            for knob_name, icon_key in data["knobs"]:
                knob_item = QTreeWidgetItem(category_item)
                knob_item.setText(0, knob_name)
                knob_icon_path = self.get_icon_path(icon_key)
                knob_item.setIcon(0, QIcon(knob_icon_path))

    def generate_code(self):
        # Kod üretme mantığı buraya gelecek
        pass

    def clear_codes(self):
        # Kod silme func
        pass

    def get_icon_path(self, icon_name):
        icon_paths = {
            "basic_input": os.path.join(self.icon_path, "basic-input-icon.svg"),
            "color_transform": os.path.join(self.icon_path, "color-transform-icon.svg"),
            "array_vector": os.path.join(self.icon_path, "array-vector-icon.svg"),
            "string_knob": os.path.join(self.icon_path, "string-knob-icon.svg"),
            "number_knob": os.path.join(self.icon_path, "number-knob-icon.svg"),
            "color_knob": os.path.join(self.icon_path, "color-knob-icon.svg"),
            "transform_knob": os.path.join(self.icon_path, "transform-knob-icon.svg"),
            "file_knob": os.path.join(self.icon_path, "file-knob-icon.svg"),
            "button_knob": os.path.join(self.icon_path, "button-knob-icon.svg")
        }
        default_icon = os.path.join(self.icon_path, "default-icon.svg")
        icon_path = icon_paths.get(icon_name, default_icon)

        if not os.path.exists(icon_path):
            print(f"Icon not found: {icon_path}")
            return ""
        return icon_path

def show_panel_builder():
    global panel_builder
    panel_builder = MacroPanelBuilder()
    panel_builder.show()