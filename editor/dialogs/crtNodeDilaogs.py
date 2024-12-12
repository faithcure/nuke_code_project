import os
import nuke
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QSpinBox, QStatusBar
)
from PySide2.QtCore import Qt


def crtNodeDialogsPane():
    """
    Creates a dialog for creating nodes with advanced options.
    """
    # Dialog oluştur
    dialog = QDialog()
    dialog.setWindowTitle("Create Node")
    dialog.setMinimumSize(600, 400)

    # Node türlerini dinamik olarak Nuke'nin plugin yolundan al
    extensions = ('gizmo', 'dll', 'dylib', 'so')
    excluded_nodes = ["A_RestoreEdgePremult"]
    excluded_prefixes = ["NST_"]
    node_classes = sorted(
        os.path.splitext(f)[0]
        for directory in nuke.pluginPath() if os.path.exists(directory)
        for f in os.listdir(directory)
        if f.endswith(extensions) and f not in excluded_nodes and not any(
            f.startswith(prefix) for prefix in excluded_prefixes)
    )

    # Ana Layout
    main_layout = QVBoxLayout()



    # Node Listesi ve Filtreleme
    node_group = QGroupBox("Node List")
    node_layout = QVBoxLayout()

    node_list_widget = QListWidget()
    node_list_widget.addItems(node_classes)  # Node isimlerini listeye ekle
    node_layout.addWidget(node_list_widget)

    # Filtreleme Widget'ları (Node List Grubunun Altına Eklendi)
    filter_layout = QHBoxLayout()

    filter_name_input = QLineEdit()
    filter_name_input.setPlaceholderText("Search by name...")

    filter_category_combo = QComboBox()
    filter_category_combo.addItems(["All", "Transform", "Color", "Merge", "Other"])
    filter_category_combo.setCurrentIndex(0)

    filter_layout.addWidget(QLabel("Search:"))
    filter_layout.addWidget(filter_name_input)
    filter_layout.addWidget(QLabel("Category:"))
    filter_layout.addWidget(filter_category_combo)
    node_layout.addLayout(filter_layout)

    node_group.setLayout(node_layout)
    main_layout.addWidget(node_group)

    # Knob Listesi
    knob_group = QGroupBox("Knob List")
    knob_layout = QVBoxLayout()

    knob_table_widget = QTableWidget()
    knob_table_widget.setColumnCount(4)
    knob_table_widget.setHorizontalHeaderLabels(["Knob Name", "Set New Value", "Value Type", "Default Value"])
    knob_layout.addWidget(knob_table_widget)

    # Filtreleme Sistemi
    knob_filter_layout = QHBoxLayout()

    knob_filter_input = QLineEdit()
    knob_filter_input.setPlaceholderText("Filter knobs by name...")

    value_type_filter_combo = QComboBox()
    value_type_filter_combo.addItems(["All", "str", "int", "float", "bool"])
    value_type_filter_combo.setMinimumWidth(150)
    value_type_filter_combo.setCurrentIndex(0)

    knob_filter_layout.addWidget(QLabel("Knob Filter:"))
    knob_filter_layout.addWidget(knob_filter_input)
    knob_filter_layout.addWidget(QLabel("Value Type:"))
    knob_filter_layout.addWidget(value_type_filter_combo)

    knob_layout.addLayout(knob_filter_layout)

    knob_group.setLayout(knob_layout)
    main_layout.addWidget(knob_group)

    # Butonlar
    button_layout = QHBoxLayout()
    create_button = QPushButton("Create Node")
    cancel_button = QPushButton("Cancel")
    button_layout.addWidget(create_button)
    button_layout.addWidget(cancel_button)
    main_layout.addLayout(button_layout)



    def show_error_message(message):
        """Show an error message dialog and update the status bar."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Input Error")
        msg.exec_()

    def validate_and_set_value(row, new_value):
        """Validate the new value based on the value type and set it."""
        value_type_item = knob_table_widget.item(row, 2)
        if value_type_item is not None:
            value_type = value_type_item.text()
            try:
                if value_type == "str":
                    validated_value = str(new_value)
                elif value_type == "int":
                    validated_value = int(float(new_value))  # Convert float to int if necessary
                elif value_type == "float":
                    validated_value = float(new_value)
                elif value_type == "bool":
                    if isinstance(new_value, str):
                        validated_value = new_value.lower() == "true"
                    else:
                        validated_value = bool(new_value)
                else:
                    raise ValueError("Unsupported value type.")

                # Set the validated value in the table
                knob_table_widget.setItem(row, 1, QTableWidgetItem(str(validated_value)))
            except ValueError:
                show_error_message(f"Invalid input for type {value_type}. Please enter a valid {value_type} value.")

    def create_input_widget_for_value_type(row, value_type):
        """Create appropriate input widget for the given value type."""
        if value_type == "bool":
            combo_box = QComboBox()
            combo_box.addItems(["True", "False"])
            combo_box.currentIndexChanged.connect(
                lambda: knob_table_widget.setItem(row, 1, QTableWidgetItem(combo_box.currentText()))
            )
            knob_table_widget.setCellWidget(row, 1, combo_box)
        elif value_type == "int":
            spin_box = QSpinBox()
            spin_box.setRange(-999999, 999999)
            spin_box.valueChanged.connect(
                lambda: knob_table_widget.setItem(row, 1, QTableWidgetItem(str(spin_box.value())))
            )
            knob_table_widget.setCellWidget(row, 1, spin_box)

    def on_create_node():
        selected_node = node_list_widget.currentItem().text() if node_list_widget.currentItem() else "None"
        dialog.accept()  # Pencereyi kapat

    def on_filter_update():
        """Listeyi filtrele."""
        search_text = filter_name_input.text().lower()
        selected_category = filter_category_combo.currentText()

        filtered_nodes = [
            node for node in node_classes
            if
            (search_text in node.lower()) and (selected_category == "All" or selected_category.lower() in node.lower())
        ]
        node_list_widget.clear()
        node_list_widget.addItems(filtered_nodes)

    def on_knob_filter_update():
        """Knob listesini filtrele."""
        filter_text = knob_filter_input.text().lower()
        selected_value_type = value_type_filter_combo.currentText()
        for row in range(knob_table_widget.rowCount()):
            name_item = knob_table_widget.item(row, 0)  # Knob Name sütunu
            type_item = knob_table_widget.item(row, 2)  # Value Type sütunu

            matches_name = filter_text in name_item.text().lower() if name_item else False
            matches_type = (selected_value_type == "All" or (type_item and type_item.text() == selected_value_type))

            knob_table_widget.setRowHidden(row, not (matches_name and matches_type))

    def on_cancel():
        dialog.reject()  # Pencereyi kapat

    def on_node_select():
        """Seçilen node'un knoblarını güncelle."""
        selected_node = node_list_widget.currentItem().text() if node_list_widget.currentItem() else None
        if selected_node:
            knob_table_widget.setRowCount(0)  # Tabloyu temizle
            try:
                # Yeni bir node oluşturulup knobları alınabilir (örneğin: nuke.createNode)
                temp_node = nuke.createNode(selected_node, inpanel=False)
                for knob_name, knob in temp_node.knobs().items():
                    try:
                        row_position = knob_table_widget.rowCount()
                        knob_table_widget.insertRow(row_position)
                        knob_table_widget.setItem(row_position, 0, QTableWidgetItem(knob_name))

                        # Value Type field
                        value_type = type(knob.value()).__name__
                        value_type_item = QTableWidgetItem(value_type)
                        value_type_item.setFlags(value_type_item.flags() ^ Qt.ItemIsEditable)  # Değiştirilemez yap
                        knob_table_widget.setItem(row_position, 2, value_type_item)

                        # Default Value field
                        default_value_item = QTableWidgetItem(str(knob.value()))
                        default_value_item.setFlags(
                            default_value_item.flags() ^ Qt.ItemIsEditable)  # Değiştirilemez yap
                        knob_table_widget.setItem(row_position, 3, default_value_item)

                        # Create appropriate input widget for Set New Value
                        create_input_widget_for_value_type(row_position, value_type)
                    except Exception as e:
                        print(f"Error processing knob {knob_name}: {e}")
                nuke.delete(temp_node)  # Geçici node'u sil
            except Exception as e:
                print(f"Error creating node {selected_node}: {e}")

    # Sinyaller
    create_button.clicked.connect(on_create_node)
    cancel_button.clicked.connect(on_cancel)
    filter_name_input.textChanged.connect(on_filter_update)
    filter_category_combo.currentIndexChanged.connect(on_filter_update)
    knob_filter_input.textChanged.connect(on_knob_filter_update)
    value_type_filter_combo.currentIndexChanged.connect(on_knob_filter_update)
    node_list_widget.currentItemChanged.connect(on_node_select)
    dialog.setLayout(main_layout)
    dialog.exec_()
