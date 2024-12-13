import os
import re
import nuke
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QListWidget,
    QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QApplication, QTextEdit, QSplitter, QTreeWidget,
    QTreeWidgetItem, QCompleter, QMenu, QAction, QWidget
)
from PySide2.QtCore import Qt, QEvent
from PySide2.QtGui import QKeySequence, QIcon, QFont


class NukeNodeCreatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuke Node Creator Pro")
        self.resize(800, 600)
        self.setup_ui()
        self.setup_connections()
        self.load_node_classes()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Horizontal splitter for left and right panels
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel - Node Selection
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Advanced node search
        search_layout = QHBoxLayout()
        self.node_search_input = QLineEdit()
        self.node_search_input.setPlaceholderText("🔍 Search nodes...")

        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "All", "Transform", "Color", "Merge", "Filter",
            "Channel", "Keyer", "Draw", "Time", "Other"
        ])

        search_layout.addWidget(self.node_search_input)
        search_layout.addWidget(self.category_combo)

        # Node tree view
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Node", "Type"])
        self.node_tree.setColumnWidth(0, 200)

        left_layout.addLayout(search_layout)
        left_layout.addWidget(self.node_tree)
        left_panel.setLayout(left_layout)

        # Right panel - Node Configuration and Code Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Vertical splitter for node configuration and code preview
        config_code_splitter = QSplitter(Qt.Vertical)

        # Node details group
        node_details_group = QGroupBox("Node Configuration")
        node_details_layout = QVBoxLayout()

        # Node variable name
        var_name_layout = QHBoxLayout()
        var_name_layout.addWidget(QLabel("Node Variable:"))
        self.node_var_input = QLineEdit()
        self.node_var_input.setPlaceholderText("Enter node variable name")
        var_name_layout.addWidget(self.node_var_input)
        node_details_layout.addLayout(var_name_layout)

        # Function checkbox
        self.is_function_check = QCheckBox("Wrap in Function")
        self.function_name_input = QLineEdit()
        self.function_name_input.setPlaceholderText("Function name")
        self.function_name_input.setVisible(False)

        node_details_layout.addWidget(self.is_function_check)
        node_details_layout.addWidget(self.function_name_input)

        # Knob configuration table
        self.knob_table = QTableWidget()
        self.knob_table.setColumnCount(4)
        self.knob_table.setHorizontalHeaderLabels([
            "Knob Name", "New Value", "Type", "Default Value"
        ])
        node_details_layout.addWidget(self.knob_table)

        node_details_group.setLayout(node_details_layout)

        # Code preview
        code_preview_group = QGroupBox("Code Preview")
        code_preview_layout = QVBoxLayout()
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(False)  # Make it editable
        # Set Consolas font
        code_font = QFont("Consolas", 10)
        self.code_preview.setFont(code_font)
        code_preview_layout.addWidget(self.code_preview)
        code_preview_group.setLayout(code_preview_layout)

        # Add widgets to vertical splitter
        config_code_splitter.addWidget(node_details_group)
        config_code_splitter.addWidget(code_preview_group)

        # Add the vertical splitter to right panel
        right_layout.addWidget(config_code_splitter)

        # Action buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Code")
        self.copy_button = QPushButton("Copy Code")
        self.close_button = QPushButton("Close")

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.close_button)
        right_layout.addLayout(button_layout)

        right_panel.setLayout(right_layout)

        # Add panels to main splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def setup_connections(self):
        # Search and filter connections
        self.node_search_input.textChanged.connect(self.filter_nodes)
        self.category_combo.currentTextChanged.connect(self.filter_nodes)
        self.node_tree.itemSelectionChanged.connect(self.on_node_selected)

        # Dynamic code preview connections
        self.node_var_input.textChanged.connect(self.update_code_preview)
        self.is_function_check.stateChanged.connect(self.on_function_check_changed)
        self.function_name_input.textChanged.connect(self.update_code_preview)

        # Knob table connections for dynamic updates
        self.knob_table.itemChanged.connect(self.update_code_preview)
        self.knob_table.cellWidget = self.create_cell_widget_with_update

        # Button connections
        self.generate_button.clicked.connect(self.generate_node_code)
        self.copy_button.clicked.connect(self.copy_code_to_clipboard)
        self.close_button.clicked.connect(self.reject)

    def create_cell_widget_with_update(self, row, col, widget):
        """Helper method to add update triggering to cell widgets"""
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self.update_code_preview)
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(self.update_code_preview)
        elif isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.update_code_preview)
        return widget

    def on_function_check_changed(self, state):
        self.function_name_input.setVisible(state)
        self.update_code_preview()

    def update_code_preview(self):
        # Generate and update code preview automatically when inputs change
        self.generate_node_code()

    def load_node_classes(self):
        # Improved node class detection
        extensions = ('gizmo', 'dll', 'dylib', 'so')
        excluded_nodes = ["A_RestoreEdgePremult"]
        excluded_prefixes = ["NST_"]

        category_map = {
            "Transform": ["transform", "move", "position", "crop"],
            "Color": ["color", "grade", "exposure", "saturation"],
            "Merge": ["merge", "combine", "blend"],
            "Filter": ["blur", "sharpen", "denoise", "filter"],
            "Channel": ["channel", "shuffle", "copy"],
            "Keyer": ["keyer", "key", "chroma"],
            "Draw": ["draw", "paint", "roto"],
            "Time": ["time", "frame", "retiming"]
        }

        self.node_tree.clear()
        category_items = {}

        for category in list(category_map.keys()) + ["Other"]:
            category_item = QTreeWidgetItem(self.node_tree, [category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            category_items[category] = category_item

        for directory in nuke.pluginPath():
            if not os.path.exists(directory):
                continue

            for f in os.listdir(directory):
                if (f.endswith(extensions) and
                        f not in excluded_nodes and
                        not any(f.startswith(prefix) for prefix in excluded_prefixes)):

                    node_name = os.path.splitext(f)[0]

                    # Determine category
                    found_category = "Other"
                    for cat, keywords in category_map.items():
                        if any(keyword in node_name.lower() for keyword in keywords):
                            found_category = cat
                            break

                    node_item = QTreeWidgetItem(category_items[found_category],
                                                [node_name, found_category])

        self.node_tree.sortItems(0, Qt.AscendingOrder)

        # Add search completer
        all_nodes = []
        for i in range(self.node_tree.topLevelItemCount()):
            category_item = self.node_tree.topLevelItem(i)
            for j in range(category_item.childCount()):
                all_nodes.append(category_item.child(j).text(0))

        completer = QCompleter(all_nodes)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.node_search_input.setCompleter(completer)

    def filter_nodes(self):
        search_text = self.node_search_input.text().lower()
        selected_category = self.category_combo.currentText()

        for i in range(self.node_tree.topLevelItemCount()):
            category_item = self.node_tree.topLevelItem(i)
            category_visible = False

            for j in range(category_item.childCount()):
                node_item = category_item.child(j)

                # Check category filter
                category_match = (selected_category == "All" or
                                  selected_category == node_item.text(1))

                # Check search text
                name_match = (not search_text or
                              search_text in node_item.text(0).lower())

                node_visible = category_match and name_match
                node_item.setHidden(not node_visible)

                if node_visible:
                    category_visible = True

            category_item.setHidden(not category_visible)

    def on_node_selected(self):
        selected_items = self.node_tree.selectedItems()
        if not selected_items or selected_items[0].parent() is None:
            return

        selected_node = selected_items[0].text(0)
        self.populate_knob_table(selected_node)

        # Suggest variable name
        suggested_var = re.sub(r'\W+', '_', selected_node.lower())
        self.node_var_input.setText(suggested_var)

    def populate_knob_table(self, node_name):
        self.knob_table.setRowCount(0)

        try:
            temp_node = nuke.createNode(node_name, inpanel=False)

            for knob_name, knob in temp_node.knobs().items():
                row = self.knob_table.rowCount()
                self.knob_table.insertRow(row)

                # Knob name
                name_item = QTableWidgetItem(knob_name)
                name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
                self.knob_table.setItem(row, 0, name_item)

                # Value type
                value_type = type(knob.value()).__name__
                type_item = QTableWidgetItem(value_type)
                type_item.setFlags(type_item.flags() ^ Qt.ItemIsEditable)
                self.knob_table.setItem(row, 2, type_item)

                # Default value
                default_item = QTableWidgetItem(str(knob.value()))
                default_item.setFlags(default_item.flags() ^ Qt.ItemIsEditable)
                self.knob_table.setItem(row, 3, default_item)

                # Input widget for new value
                if value_type == "float":
                    spin_box = QDoubleSpinBox()
                    spin_box.setRange(-999999.0, 999999.0)
                    spin_box.setValue(float(knob.value()))
                    spin_box.valueChanged.connect(
                        lambda val, r=row: self.knob_table.setItem(r, 1, QTableWidgetItem(str(val)))
                    )
                    self.knob_table.setCellWidget(row, 1, spin_box)
                elif value_type == "int":
                    spin_box = QSpinBox()
                    spin_box.setRange(-999999, 999999)
                    spin_box.setValue(int(knob.value()))
                    spin_box.valueChanged.connect(
                        lambda val, r=row: self.knob_table.setItem(r, 1, QTableWidgetItem(str(val)))
                    )
                    self.knob_table.setCellWidget(row, 1, spin_box)
                elif value_type == "bool":
                    combo_box = QComboBox()
                    combo_box.addItems(["True", "False"])
                    combo_box.setCurrentText(str(knob.value()))
                    combo_box.currentTextChanged.connect(
                        lambda val, r=row: self.knob_table.setItem(r, 1, QTableWidgetItem(val))
                    )
                    self.knob_table.setCellWidget(row, 1, combo_box)
                else:
                    line_edit = QLineEdit(str(knob.value()))
                    line_edit.textChanged.connect(
                        lambda val, r=row: self.knob_table.setItem(r, 1, QTableWidgetItem(val))
                    )
                    self.knob_table.setCellWidget(row, 1, line_edit)

            nuke.delete(temp_node)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating node: {e}")

    def generate_node_code(self):
        # Check if node is selected
        if not self.node_tree.selectedItems():
            return

        selected_node = self.node_tree.selectedItems()[0].text(0)
        node_var = self.node_var_input.text().strip()

        if not node_var:
            return

        # Generate code
        code_lines = []

        # Optional function wrapper
        if self.is_function_check.isChecked():
            func_name = self.function_name_input.text().strip()
            if not func_name:
                return
            code_lines.append(f"def {func_name}():")
            indent = "    "
        else:
            indent = ""

        # Node creation
        code_lines.append(f"{indent}{node_var} = nuke.createNode('{selected_node}')")

        # Knob configuration
        for row in range(self.knob_table.rowCount()):
            knob_name_item = self.knob_table.item(row, 0)
            new_value_item = self.knob_table.item(row, 1)
            type_item = self.knob_table.item(row, 2)

            if (not knob_name_item or not new_value_item or
                    not type_item or not new_value_item.text()):
                continue

            knob_name = knob_name_item.text()
            new_value = new_value_item.text()
            value_type = type_item.text()

            # Type conversion
            try:
                if value_type == "int":
                    converted_value = int(float(new_value))
                elif value_type == "float":
                    converted_value = float(new_value)
                elif value_type == "bool":
                    converted_value = new_value.lower() == "true"
                else:
                    converted_value = new_value

                # Generate knob setting code
                code_lines.append(
                    f"{indent}{node_var}['{knob_name}'].setValue({repr(converted_value)})"
                )
            except ValueError:
                continue

        # Return statement if wrapped in function
        if self.is_function_check.isChecked():
            code_lines.append(f"{indent}return {node_var}")

        # Combine and display code
        full_code = "\n".join(code_lines)

        # Only update if the code has changed to prevent cursor position reset
        if self.code_preview.toPlainText() != full_code:
            self.code_preview.setPlainText(full_code)

        return full_code

    def copy_code_to_clipboard(self):
        code = self.code_preview.toPlainText()
        if not code:
            QMessageBox.warning(self, "Copy Error", "No code to copy.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(code)
        QMessageBox.information(self, "Code Copied", "Node creation code copied to clipboard.")


def show_nuke_node_creator():
    """
    Convenience function to show the Nuke Node Creator dialog.
    Can be called directly from Nuke's script editor or menu.
    """
    dialog = NukeNodeCreatorDialog()
    dialog.exec_()


# Example usage:
if __name__ == "__main__":
    show_nuke_node_creator()