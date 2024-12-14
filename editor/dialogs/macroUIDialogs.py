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
        self.selected_knobs = []
        self.create_tool_bar()

        self.content_splitter = QSplitter(Qt.Horizontal)
        self.create_left_panel()
        self.create_center_panel()
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

        # Tab widget oluştur
        self.tab_widget = QTabWidget()

        # Knobs tab'ı
        knobs_tab = QWidget()
        knobs_layout = QVBoxLayout(knobs_tab)

        # Knobs Tree
        self.knobs_tree = QTreeWidget()
        self.knobs_tree.setHeaderHidden(True)
        self.knobs_tree.setIconSize(QSize(16, 16))
        self.populate_knobs_tree(self.knobs_tree)
        knobs_layout.addWidget(self.knobs_tree)

        # Layouts tab'ı
        layouts_tab = QWidget()
        layouts_layout = QVBoxLayout(layouts_tab)

        # Layouts Tree
        self.layouts_tree = QTreeWidget()
        self.layouts_tree.setHeaderHidden(True)
        self.layouts_tree.setIconSize(QSize(16, 16))
        self.populate_layouts_tree()
        layouts_layout.addWidget(self.layouts_tree)

        # Tab'ları ekle
        self.tab_widget.addTab(knobs_tab, "Knobs")
        self.tab_widget.addTab(layouts_tab, "Layouts")

        left_layout.addWidget(self.tab_widget)

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

    def create_center_panel(self):
        self.center_widget = QWidget()
        self.center_layout = QVBoxLayout(self.center_widget)

        # Drop alanı için frame
        self.drop_frame = QFrame()
        self.drop_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.drop_frame.setMinimumSize(400, 500)
        self.drop_frame.setAcceptDrops(True)

        # Grid çizgileri için custom paint
        class GridFrame(QFrame):
            def paintEvent(self, event):
                super().paintEvent(event)
                painter = QPainter(self)
                painter.setPen(QPen(QColor(100, 100, 100, 50), 1, Qt.DashLine))

                # Dikey çizgiler
                for x in range(0, self.width(), 20):
                    painter.drawLine(x, 0, x, self.height())

                # Yatay çizgiler
                for y in range(0, self.height(), 20):
                    painter.drawLine(0, y, self.width(), y)

        self.drop_frame = GridFrame()
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #444;
            }
        """)

        # Drop event handlers
        def dragEnterEvent(event):
            if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
                event.accept()
            else:
                event.ignore()

        def dropEvent(event):
            pos = event.pos()
            data = event.mimeData()
            layout_data = self.get_layout_data_from_mime(data)
            if layout_data:
                self.create_layout_widget(layout_data, pos)
            event.accept()

        self.drop_frame.dragEnterEvent = dragEnterEvent
        self.drop_frame.dropEvent = dropEvent

        self.center_layout.addWidget(self.drop_frame)
        self.content_splitter.addWidget(self.center_widget)

    def get_layout_data_from_mime(self, mime_data):
        # MIME verisinden layout bilgisini çıkart
        encoded_data = mime_data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.ReadOnly)
        while not stream.atEnd():
            row = stream.readInt32()
            col = stream.readInt32()
            item_data = {}
            for role in range(stream.readInt32()):
                key = stream.readInt32()
                value = stream.readQVariant()
                if key == Qt.UserRole:
                    return value
        return None

    def create_right_panel(self):
        right_dock = QDockWidget("Properties", self)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(2)

        # Property Editor
        self.property_table = QTableWidget()
        self.property_table.setColumnCount(2)
        self.property_table.setHorizontalHeaderLabels(["Property", "Value"])

        # Tablo ayarları
        self.property_table.setShowGrid(False)  # Grid çizgilerini kaldır
        self.property_table.setAlternatingRowColors(True)  # Alternatif satır renkleri
        self.property_table.horizontalHeader().setStretchLastSection(True)
        self.property_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.property_table.horizontalHeader().setDefaultSectionSize(140)
        self.property_table.verticalHeader().setVisible(False)
        self.property_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Nuke stil table tasarımı
        self.property_table.setStyleSheet("""
            QTableWidget {
                background-color: #282828;
                alternate-background-color: #2e2e2e;
                color: #d8d8d8;
                border: none;
                font-size: 11px;
                gridline-color: transparent;
            }

            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #383838;
            }

            QTableWidget::item:selected {
                background-color: #4b5052;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #333333;
                color: #d8d8d8;
                padding: 4px;
                border: none;
                border-bottom: 2px solid #444444;
                font-weight: bold;
            }

            QScrollBar:vertical {
                background-color: #282828;
                width: 12px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #444444;
                min-height: 20px;
                border-radius: 2px;
                margin: 2px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        right_layout.addWidget(self.property_table)
        right_widget.setLayout(right_layout)
        right_dock.setWidget(right_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)

    def update_property_editor(self, knob_data):
        """Property editörünü seçili knob'a göre günceller"""
        if not knob_data:
            self.property_table.setRowCount(0)
            return

        # Knob tipine göre özellikleri belirle
        properties = self.get_knob_properties(knob_data["type"])
        self.property_table.setRowCount(len(properties))

        for row, (prop_name, prop_data) in enumerate(properties.items()):
            # Property adını ayarla
            name_item = QTableWidgetItem(prop_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Salt okunur
            self.property_table.setItem(row, 0, name_item)

            # Property değer widget'ını oluştur
            value_widget = self.create_property_widget(prop_data)
            if value_widget:
                self.property_table.setCellWidget(row, 1, value_widget)

    def create_property_widget(self, prop_data):
        """Property tipine göre uygun widget oluşturur"""
        prop_type = prop_data["type"]
        default_value = prop_data["default"]

        if prop_type == "string":
            widget = QLineEdit()
            widget.setText(str(default_value))
            widget.textChanged.connect(lambda: self.on_property_changed(widget))
            return widget

        elif prop_type == "bool":
            widget = QWidget()
            layout = QHBoxLayout(widget)
            checkbox = QCheckBox()
            checkbox.setChecked(default_value)
            checkbox.stateChanged.connect(lambda: self.on_property_changed(checkbox))
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            return widget

        elif prop_type == "float":
            widget = QDoubleSpinBox()
            widget.setRange(-1e6, 1e6)
            widget.setValue(default_value)
            widget.valueChanged.connect(lambda: self.on_property_changed(widget))
            return widget

        elif prop_type == "color":
            widget = QPushButton()
            widget.setStyleSheet(f"background-color: {default_value};")
            widget.clicked.connect(lambda: self.show_color_dialog(widget))
            return widget

        elif prop_type == "file":
            widget = QWidget()
            layout = QHBoxLayout(widget)
            line_edit = QLineEdit(default_value)
            browse_btn = QPushButton("...")
            browse_btn.clicked.connect(lambda: self.show_file_dialog(line_edit))
            layout.addWidget(line_edit)
            layout.addWidget(browse_btn)
            return widget

        return None

    def on_property_changed(self, widget):
        """Property değeri değiştiğinde çağrılır"""
        try:
            # Property değişikliklerini takip et ve işle
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()

            # Değişiklikleri kaydet veya uygula
            self.update_knob_property(value)
        except Exception as e:
            print(f"Error updating property: {str(e)}")

    def show_color_dialog(self, button):
        """Renk seçim dialogunu gösterir"""
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
            self.update_knob_property(color.name())

    def show_file_dialog(self, line_edit):
        """Dosya seçim dialogunu gösterir"""
        file_path, _ = QFileDialog.getOpenFileName()
        if file_path:
            line_edit.setText(file_path)
            self.update_knob_property(file_path)

    def get_knob_properties(self, knob_type):
        """Knob tipine göre mevcut özellikleri döndürür"""
        common_properties = {
            "Name": {"type": "string", "default": ""},
            "Label": {"type": "string", "default": ""},
            "Tooltip": {"type": "string", "default": ""},
            "Hidden": {"type": "bool", "default": False},
        }

        type_specific_properties = {
            "string_knob": {
                "Default Value": {"type": "string", "default": ""},
                "Multiline": {"type": "bool", "default": False},
            },
            "number_knob": {
                "Default Value": {"type": "float", "default": 0.0},
                "Min": {"type": "float", "default": -1e6},
                "Max": {"type": "float", "default": 1e6},
                "Step": {"type": "float", "default": 1.0},
            },
            "color_knob": {
                "Default Color": {"type": "color", "default": "#000000"},
                "Alpha": {"type": "bool", "default": False},
            },
            "button_knob": {
                "Command": {"type": "string", "default": ""},
                "Icon": {"type": "file", "default": ""},
            },
        }

        # Temel özellikleri al ve tipe özel özellikleri ekle
        properties = common_properties.copy()
        if knob_type in type_specific_properties:
            properties.update(type_specific_properties[knob_type])

        return properties

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

                if knob_name == "String_Knob":
                    knob_item.setText(0, "Text Field")
                elif knob_name == "Int_Knob":
                    knob_item.setText(0, "Integer Field")
                elif knob_name == "Double_Knob":
                    knob_item.setText(0, "Float Field")
                elif knob_name == "Boolean_Knob":
                    knob_item.setText(0, "Checkbox")
                elif knob_name == "Password_Knob":
                    knob_item.setText(0, "Password Field")
                elif knob_name == "Text_Knob":
                    knob_item.setText(0, "Multiline Text")
                elif knob_name == "Multiline_Eval_String_Knob":
                    knob_item.setText(0, "Multiline Expression")
                elif knob_name == "Color_Knob":
                    knob_item.setText(0, "Color Picker")
                elif knob_name == "AColor_Knob":
                    knob_item.setText(0, "Advanced Color Picker")
                elif knob_name == "XY_Knob":
                    knob_item.setText(0, "XY Coordinate")
                elif knob_name == "XYZ_Knob":
                    knob_item.setText(0, "XYZ Coordinate")
                elif knob_name == "UV_Knob":
                    knob_item.setText(0, "UV Coordinate")
                elif knob_name == "WH_Knob":
                    knob_item.setText(0, "Width/Height")
                elif knob_name == "Box3_Knob":
                    knob_item.setText(0, "3D Bounding Box")
                elif knob_name == "Scale_Knob":
                    knob_item.setText(0, "Scale")
                elif knob_name == "Format_Knob":
                    knob_item.setText(0, "Format")
                elif knob_name == "Array_Knob":
                    knob_item.setText(0, "Array")
                elif knob_name == "BBox_Knob":
                    knob_item.setText(0, "Bounding Box")
                elif knob_name == "ColorChip_Knob":
                    knob_item.setText(0, "Color Chip")
                elif knob_name == "Channel_Knob":
                    knob_item.setText(0, "Channel")
                elif knob_name == "ChannelMask_Knob":
                    knob_item.setText(0, "Channel Mask")
                elif knob_name == "Link_Knob":
                    knob_item.setText(0, "Link")
                elif knob_name == "PyScript_Knob":
                    knob_item.setText(0, "Python Script")
                elif knob_name == "PyCustom_Knob":
                    knob_item.setText(0, "Python Custom")
                elif knob_name == "Enumeration_Knob":
                    knob_item.setText(0, "Dropdown")
                elif knob_name == "Pulldown_Knob":
                    knob_item.setText(0, "Pulldown")
                elif knob_name == "Radio_Knob":
                    knob_item.setText(0, "Radio Button")
                elif knob_name == "Button_Knob":
                    knob_item.setText(0, "Button")
                else:
                    knob_item.setText(0, knob_name)

                knob_icon_path = self.get_icon_path(icon_key)
                knob_item.setIcon(0, QIcon(knob_icon_path))
                knob_item.setData(1, Qt.UserRole, {"name": knob_item.text(0), "type": icon_key,
                                                   "icon_path": os.path.join(self.icon_path, "knobs",
                                                                             f"{knob_name.lower()}_thumb.png")})

        self.knobs_tree.currentItemChanged.connect(self.update_knob_preview)

    def populate_layouts_tree(self):
        # Layouts tree için aynı stili uygula
        self.layouts_tree.setStyleSheet(self.knobs_tree.styleSheet())

        layouts = {
            "Containers": {
                "icon": "container_icon.svg",
                "items": [
                    ("Tab Layout", "tab_layout_icon.svg"),
                    ("Group Box", "group_box_icon.svg"),
                    ("Collapsible Frame", "collapsible_frame_icon.svg")
                ]
            },
            "Basic Layouts": {
                "icon": "basic_layout_icon.svg",
                "items": [
                    ("Vertical Layout", "vertical_layout_icon.svg"),
                    ("Horizontal Layout", "horizontal_layout_icon.svg"),
                    ("Grid Layout", "grid_layout_icon.svg")
                ]
            }
        }

        for category, data in layouts.items():
            category_item = QTreeWidgetItem(self.layouts_tree)
            category_item.setText(0, category)
            category_icon = QIcon(os.path.join(self.icon_path, data["icon"]))
            category_item.setIcon(0, category_icon)

            for item_name, icon_file in data["items"]:
                layout_item = QTreeWidgetItem(category_item)
                layout_item.setText(0, item_name)
                layout_icon = QIcon(os.path.join(self.icon_path, icon_file))
                layout_item.setIcon(0, layout_icon)
                layout_item.setData(1, Qt.UserRole, {
                    "name": item_name,
                    "type": item_name.lower().replace(" ", "_"),
                    "class": self.get_layout_class(item_name)
                })

        # Sürükle-bırak için event'leri ayarla
        self.layouts_tree.setDragEnabled(True)
        self.layouts_tree.setDragDropMode(QAbstractItemView.DragOnly)

        # Çift tıklama event'i
        self.layouts_tree.itemDoubleClicked.connect(self.add_layout_to_center)

    def get_layout_class(self, layout_type):
        """Layout tipine göre uygun sınıfı döndürür"""
        # Layout tipleri ve karşılık gelen sınıflar
        layout_classes = {
            "tab_layout": QTabWidget,
            "group_box": QGroupBox,
            "collapsible_frame": QFrame,
            "vertical_layout": QVBoxLayout,
            "horizontal_layout": QHBoxLayout,
            "grid_layout": QGridLayout,
            "form_layout": QFormLayout
        }

        # Layout tipini normalize et
        normalized_type = layout_type.lower().replace(" ", "_")
        return layout_classes.get(normalized_type, QVBoxLayout)  # Varsayılan olarak QVBoxLayout

    def add_layout_to_center(self, item):
        """Çift tıklama ile layout ekleme"""
        if not item or not item.parent():  # Eğer item yok veya kategori başlığı ise
            return

        layout_data = item.data(1, Qt.UserRole)
        if layout_data:
            # Layout widget'ı merkeze ekle
            widget = self.create_layout_widget(layout_data)
            if widget:
                # Widget'ı ortala
                drop_frame_rect = self.drop_frame.rect()
                widget_rect = widget.rect()
                center_pos = QPoint(
                    (drop_frame_rect.width() - widget_rect.width()) // 2,
                    (drop_frame_rect.height() - widget_rect.height()) // 2
                )
                widget.move(center_pos)

    def create_layout_widget(self, layout_data, pos=None):
        """Layout widget'ı oluşturur ve yapılandırır"""
        if not layout_data:
            print("No layout data provided")
            return None

        try:
            layout_type = layout_data.get("type", "")
            layout_name = layout_data.get("name", "Unnamed Layout")

            # Ana container widget'ı oluştur
            container = QWidget(self.drop_frame)
            container.setMinimumSize(100, 100)
            container.setStyleSheet("""
                QWidget {
                    background-color: rgba(60, 60, 60, 150);
                    border: 1px solid #555;
                }
            """)

            # Layout tipine göre widget oluştur
            if layout_type == "tab_layout":
                tab_widget = QTabWidget(container)
                tab_widget.addTab(QWidget(), "Tab 1")
                tab_widget.addTab(QWidget(), "Tab 2")
                QVBoxLayout(container).addWidget(tab_widget)

            elif layout_type == "group_box":
                group_box = QGroupBox(layout_name, container)
                group_box.setLayout(QVBoxLayout())
                QVBoxLayout(container).addWidget(group_box)

            elif layout_type == "collapsible_frame":
                frame = QFrame(container)
                frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
                frame.setLayout(QVBoxLayout())
                QVBoxLayout(container).addWidget(frame)

            else:
                # Basit layout'lar için
                layout_class = self.get_layout_class(layout_type)
                container.setLayout(layout_class())

            # Pozisyon ayarla
            if pos:
                container.move(pos)

            container.show()
            return container

        except Exception as e:
            print(f"Error creating layout widget: {str(e)}")
            return None



    def update_knob_preview(self, current, previous):
        """Seçilen knob için önizleme panelini günceller"""

        # Önizleme alanını temizle
        def clear_preview():
            self.knob_preview_label.clear()
            self.knob_preview_name_label.clear()
            self.knob_preview_type_label.clear()

        knob_data = current.data(1, Qt.UserRole) if current and current.parent() else None
        self.update_property_editor(knob_data)

        # Eğer seçili item yoksa veya kategori başlığı ise önizlemeyi temizle
        if not current or not current.parent():
            clear_preview()
            return

        # Knob verilerini al
        knob_data = current.data(1, Qt.UserRole)
        if not knob_data:
            clear_preview()
            return

        try:
            # İkon yolunu kontrol et
            icon_path = knob_data.get("icon_path", "")
            if icon_path and os.path.exists(icon_path):
                knob_icon = QPixmap(icon_path)
                self.knob_preview_label.setPixmap(
                    knob_icon.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.knob_preview_label.clear()

            # İsim ve tip bilgilerini göster
            self.knob_preview_name_label.setText(knob_data.get("name", ""))
            self.knob_preview_type_label.setText(knob_data.get("type", ""))

        except Exception as e:
            print(f"Error updating preview: {str(e)}")
            clear_preview()

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