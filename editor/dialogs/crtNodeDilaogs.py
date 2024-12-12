import os
import nuke
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QSpinBox, QDoubleSpinBox, QCheckBox, QMenu, QComboBox, QTextEdit, QApplication
)
from PySide2.QtCore import Qt

def crtNodeDialogsPane():
    dialog = QDialog()
    dialog.setWindowTitle("Create Node")

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

    main_layout = QVBoxLayout()

    code_settings_group = QGroupBox("Code Settings")
    code_settings_layout = QVBoxLayout()

    node_name_input = QLineEdit()
    node_name_input.setPlaceholderText("Enter node variable name...")
    code_settings_layout.addWidget(node_name_input)

    is_function_checkbox = QCheckBox("isFunction?")
    function_name_input = QLineEdit()
    function_name_input.setPlaceholderText("Enter function name...")
    function_name_input.setVisible(False)

    def toggle_function_name_input(state):
        function_name_input.setVisible(state)

    is_function_checkbox.stateChanged.connect(toggle_function_name_input)
    code_settings_layout.addWidget(is_function_checkbox)
    code_settings_layout.addWidget(function_name_input)

    code_settings_group.setLayout(code_settings_layout)
    main_layout.addWidget(code_settings_group)

    node_group = QGroupBox("Node List")
    node_layout = QVBoxLayout()

    node_list_widget = QListWidget()
    node_list_widget.setMaximumHeight(100)
    node_list_widget.addItems(node_classes)
    node_layout.addWidget(node_list_widget)

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

    knob_group = QGroupBox("Knob List")
    knob_layout = QVBoxLayout()

    knob_table_widget = QTableWidget()
    knob_table_widget.setMinimumHeight(300)
    knob_table_widget.setColumnCount(4)
    knob_table_widget.setHorizontalHeaderLabels(["Knob Name", "Set New Value", "Value Type", "Default Value"])
    knob_layout.addWidget(knob_table_widget)

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

    button_layout = QHBoxLayout()
    create_button = QPushButton("Get Code")
    cancel_button = QPushButton("Cancel")
    button_layout.addWidget(create_button)
    button_layout.addWidget(cancel_button)
    main_layout.addLayout(button_layout)

    code_preview = QTextEdit()
    code_preview.setReadOnly(True)
    main_layout.addWidget(code_preview)

    copy_button = QPushButton("Copy Code")
    main_layout.addWidget(copy_button)

    def create_node_with_knobs():
        selected_node = node_list_widget.currentItem().text() if node_list_widget.currentItem() else None
        if not selected_node:
            QMessageBox.warning(dialog, "Input Error", "Please select a node from the list.")
            return

        node_var_name = node_name_input.text().strip()
        if not node_var_name:
            QMessageBox.warning(dialog, "Input Error", "Please enter a valid node variable name.")
            return

        if is_function_checkbox.isChecked():
            function_name = function_name_input.text().strip()
            if not function_name:
                QMessageBox.warning(dialog, "Input Error", "Please enter a valid function name.")
                return

        try:
            node_code = ""
            if is_function_checkbox.isChecked():
                node_code += f"def {function_name}():\n"

            node_code += f"    {node_var_name} = nuke.createNode('{selected_node}')\n"
            used_knobs = []

            for row in range(knob_table_widget.rowCount()):
                knob_name_item = knob_table_widget.item(row, 0)
                new_value_item = knob_table_widget.item(row, 1)
                value_type_item = knob_table_widget.item(row, 2)
                default_value_item = knob_table_widget.item(row, 3)

                if not knob_name_item or (value_type_item and value_type_item.text() == "NoneType"):
                    knob_table_widget.setRowHidden(row, True)
                    continue

                if knob_name_item and new_value_item and new_value_item.text():
                    knob_name = knob_name_item.text()
                    new_value = new_value_item.text()
                    value_type = value_type_item.text() if value_type_item else ""

                    if value_type == "int":
                        new_value = int(float(new_value))
                    elif value_type == "float":
                        new_value = float(new_value)
                    elif value_type == "bool":
                        new_value = new_value.lower() == "true"
                    elif value_type == "str":
                        new_value = str(new_value)

                    used_knobs.append(f"{knob_name}: {new_value}")
                    node_code += f"    {node_var_name}[\"{knob_name}\"].setValue({repr(new_value)})\n"

            code_preview.setPlainText(node_code)
            print("Generated Node Code:\n", node_code)
            print("Used Knobs:", ", ".join(used_knobs))
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error creating node: {e}")

    def copy_code_to_clipboard():
        clipboard = QApplication.clipboard()
        clipboard.setText(code_preview.toPlainText())
        QMessageBox.information(dialog, "Copy Code", "Code has been copied to clipboard.")

    def on_filter_update():
        search_text = filter_name_input.text().lower()
        selected_category = filter_category_combo.currentText()

        filtered_nodes = [
            node for node in node_classes
            if (search_text in node.lower()) and (selected_category == "All" or selected_category.lower() in node.lower())
        ]
        node_list_widget.clear()
        node_list_widget.addItems(filtered_nodes)

    def on_knob_filter_update():
        filter_text = knob_filter_input.text().lower()
        selected_value_type = value_type_filter_combo.currentText()
        for row in range(knob_table_widget.rowCount()):
            name_item = knob_table_widget.item(row, 0)
            type_item = knob_table_widget.item(row, 2)

            matches_name = filter_text in name_item.text().lower() if name_item else False
            matches_type = (selected_value_type == "All" or (type_item and type_item.text() == selected_value_type))

            knob_table_widget.setRowHidden(row, not (matches_name and matches_type))

    def on_node_select():
        selected_node = node_list_widget.currentItem().text() if node_list_widget.currentItem() else None
        if selected_node:
            knob_table_widget.setRowCount(0)
            try:
                temp_node = nuke.createNode(selected_node, inpanel=False)
                for knob_name, knob in temp_node.knobs().items():
                    row_position = knob_table_widget.rowCount()
                    knob_table_widget.insertRow(row_position)
                    knob_table_widget.setItem(row_position, 0, QTableWidgetItem(knob_name))

                    value_type = type(knob.value()).__name__
                    value_type_item = QTableWidgetItem(value_type)
                    value_type_item.setFlags(value_type_item.flags() ^ Qt.ItemIsEditable)
                    knob_table_widget.setItem(row_position, 2, value_type_item)

                    default_value_item = QTableWidgetItem(str(knob.value()))
                    default_value_item.setFlags(default_value_item.flags() ^ Qt.ItemIsEditable)
                    knob_table_widget.setItem(row_position, 3, default_value_item)

                    if value_type == "float":
                        spin_box = QDoubleSpinBox()
                        spin_box.setRange(-999999.0, 999999.0)
                        spin_box.setSingleStep(0.1)
                        spin_box.setValue(knob.value() if isinstance(knob.value(), float) else 0.0)
                        spin_box.valueChanged.connect(
                            lambda val, r=row_position: knob_table_widget.setItem(r, 1, QTableWidgetItem(str(val)))
                        )
                        knob_table_widget.setCellWidget(row_position, 1, spin_box)
                    elif value_type == "int":
                        spin_box = QSpinBox()
                        spin_box.setRange(-999999, 999999)
                        spin_box.setValue(knob.value() if isinstance(knob.value(), int) else 0)
                        spin_box.valueChanged.connect(
                            lambda val, r=row_position: knob_table_widget.setItem(r, 1, QTableWidgetItem(str(val)))
                        )
                        knob_table_widget.setCellWidget(row_position, 1, spin_box)
                    elif value_type == "bool":
                        combo_box = QComboBox()
                        combo_box.addItems(["True", "False"])
                        combo_box.setCurrentText(str(knob.value()))
                        combo_box.currentTextChanged.connect(
                            lambda val, r=row_position: knob_table_widget.setItem(r, 1, QTableWidgetItem(val))
                        )
                        knob_table_widget.setCellWidget(row_position, 1, combo_box)

                nuke.delete(temp_node)
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error creating node: {e}")

    create_button.clicked.connect(create_node_with_knobs)
    cancel_button.clicked.connect(dialog.reject)
    filter_name_input.textChanged.connect(on_filter_update)
    filter_category_combo.currentIndexChanged.connect(on_filter_update)
    knob_filter_input.textChanged.connect(on_knob_filter_update)
    value_type_filter_combo.currentIndexChanged.connect(on_knob_filter_update)
    node_list_widget.currentItemChanged.connect(on_node_select)

    dialog.setLayout(main_layout)
    dialog.exec_()
