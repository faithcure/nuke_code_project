import sys
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget, QWidget,
    QVBoxLayout, QLabel, QComboBox, QLineEdit, QCheckBox, QSpinBox, QPushButton,
    QHBoxLayout, QFormLayout, QDialogButtonBox
)
from PySide2.QtCore import Qt


class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 800, 600)

        # Kategori Listesi
        self.category_list = QListWidget()
        self.category_list.addItems(["General", "Appearance", "Editor", "Code Completion", "Environment", "Advanced"])
        self.category_list.currentRowChanged.connect(self.display_category)

        # Ayar Panelleri için QStackedWidget
        self.settings_panels = QStackedWidget()
        self.settings_panels.addWidget(self.general_settings())
        self.settings_panels.addWidget(self.appearance_settings())
        self.settings_panels.addWidget(self.editor_settings())
        self.settings_panels.addWidget(self.code_completion_settings())
        self.settings_panels.addWidget(self.environment_settings())
        self.settings_panels.addWidget(self.advanced_settings())

        # Apply, OK, Cancel Düğmeleri
        button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.save_and_close)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        # Ana Layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.category_list, 1)
        main_layout.addWidget(self.settings_panels, 3)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        # Alt Layout (düğmeler)
        layout = QVBoxLayout()
        layout.addWidget(central_widget)
        layout.addWidget(button_box)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # Her Kategori İçin Ayar Panelleri

    def general_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        layout.addRow("Language:", QComboBox())
        theme_box = QComboBox()
        theme_box.addItems(["Light", "Dark"])
        layout.addRow("Theme:", theme_box)
        startup_checkbox = QCheckBox("Start at Login")
        layout.addRow(startup_checkbox)

        panel.setLayout(layout)
        return panel

    def appearance_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        font_box = QComboBox()
        font_box.addItems(["Arial", "Verdana", "Courier New"])
        layout.addRow("Font:", font_box)

        font_size_spinbox = QSpinBox()
        font_size_spinbox.setRange(8, 48)
        layout.addRow("Font Size:", font_size_spinbox)

        line_number_checkbox = QCheckBox("Show Line Numbers")
        layout.addRow(line_number_checkbox)

        panel.setLayout(layout)
        return panel

    def editor_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        tab_size_spinbox = QSpinBox()
        tab_size_spinbox.setRange(2, 8)
        layout.addRow("Tab Size:", tab_size_spinbox)

        auto_complete_checkbox = QCheckBox("Enable Auto-Completion")
        layout.addRow(auto_complete_checkbox)

        panel.setLayout(layout)
        return panel

    def code_completion_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        code_suggestions_checkbox = QCheckBox("Show Code Suggestions")
        layout.addRow(code_suggestions_checkbox)

        auto_import_checkbox = QCheckBox("Enable Auto Imports")
        layout.addRow(auto_import_checkbox)

        panel.setLayout(layout)
        return panel

    def environment_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        memory_limit_spinbox = QSpinBox()
        memory_limit_spinbox.setRange(256, 32768)
        memory_limit_spinbox.setSuffix(" MB")
        layout.addRow("Memory Limit:", memory_limit_spinbox)

        cpu_priority_checkbox = QCheckBox("Set High CPU Priority")
        layout.addRow(cpu_priority_checkbox)

        panel.setLayout(layout)
        return panel

    def advanced_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        dev_mode_checkbox = QCheckBox("Enable Developer Mode")
        layout.addRow(dev_mode_checkbox)

        experimental_features_checkbox = QCheckBox("Enable Experimental Features")
        layout.addRow(experimental_features_checkbox)

        panel.setLayout(layout)
        return panel

    # Ayarları Uygula, Kaydet ve Kapat Fonksiyonları
    def apply_settings(self):
        print("Applying settings...")  # Ayarları uygula

    def save_and_close(self):
        self.apply_settings()
        self.close()

    def display_category(self, index):
        self.settings_panels.setCurrentIndex(index)


# Uygulamayı Başlat
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
