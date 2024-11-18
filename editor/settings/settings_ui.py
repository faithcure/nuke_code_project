import sys
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget, QWidget,
    QVBoxLayout, QLabel, QComboBox, QLineEdit, QCheckBox, QSpinBox, QPushButton,
    QHBoxLayout, QFormLayout, QDialogButtonBox, QGroupBox, QTextEdit, QFrame, QFontComboBox, QFileDialog, QSpacerItem,
    QSizePolicy
)
from PySide2.QtCore import Qt
from PySide2.QtGui import QFontDatabase, QFont
import os
import json


class SettingsWindow(QMainWindow):
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    print(SETTINGS_FILE)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("QLabel { color: white; }")

        # **self.settings Özelliğini İlk Olarak Tanımlayın**
        self.settings = self.load_settings()

        # Category List
        self.category_list = QListWidget()
        self.category_list.addItems(["General", "Code Editor", "Environment", "Licence", "Github", "Other Apps"])
        self.category_list.currentRowChanged.connect(self.display_category)

        # Setting Panels for Each Category
        self.settings_panels = QStackedWidget()
        self.settings_panels.addWidget(self.general_settings())
        self.settings_panels.addWidget(self.code_editor_settings())
        self.settings_panels.addWidget(self.environment_settings())
        self.settings_panels.addWidget(self.licence_settings())
        self.settings_panels.addWidget(self.github_settings())
        self.settings_panels.addWidget(self.other_apps_settings())

        # Apply, OK, Cancel Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Reset | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.save_and_close)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)

        # Main Layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.category_list, 1)
        main_layout.addWidget(self.settings_panels, 3)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)

        # Bottom Layout (buttons)
        layout = QVBoxLayout()
        layout.addWidget(central_widget)
        layout.addWidget(button_box)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Apply settings to widgets
        self.apply_settings_to_widgets()

    def load_settings(self):
        """Loads settings from a JSON file if it exists, otherwise returns default settings."""
        if os.path.exists(self.SETTINGS_FILE):
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as file:
                print(f"Loading settings from {self.SETTINGS_FILE}")
                return json.load(file)
        else:
            print(f"{self.SETTINGS_FILE} not found. Creating default settings.")
            return {}

    def save_settings(self):
        """Saves current widget states to a JSON file."""
        self.to_json()

    def general_settings(self):
        panel = QWidget()
        layout = QFormLayout()

        # Language & Theme settings (existing)
        language_combobox = QComboBox()
        language_combobox.setObjectName("default_language")
        language_combobox.addItem("English")
        language_combobox.setEnabled(False)
        layout.addRow("Language:", language_combobox)

        theme_combobox = QComboBox()
        theme_combobox.addItem("Nuke Default")
        theme_combobox.setObjectName("default_theme")
        theme_combobox.setEnabled(False)
        layout.addRow("Theme:", theme_combobox)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addRow("Other Settings:", separator)

        # Start at Login
        start_group = QGroupBox("Start at Login")
        start_layout = QVBoxLayout()
        startup_checkbox = QCheckBox("Enable start at login")
        startup_checkbox.setObjectName("startup_checkbox")
        start_description = QLabel("Automatically start the application when logging into the system.")
        start_description.setWordWrap(True)
        start_layout.addWidget(startup_checkbox)
        start_layout.addWidget(start_description)
        start_group.setLayout(start_layout)
        layout.addWidget(start_group)

        # New UI Settings Group for Code Editor Default Interface
        ui_settings_group = QGroupBox("UI Settings")
        ui_settings_layout = QFormLayout()

        # Default Interface Mode ComboBox
        interface_mode_combobox = QComboBox()
        interface_mode_combobox.setObjectName("default_interface_mode")
        interface_mode_combobox.addItems(["Default", "Focus Coding", "Project Management", "Debug"])
        interface_mode_combobox.setToolTip("Set the default startup interface mode for the code editor.")
        ui_settings_layout.addRow("Default Interface Mode:", interface_mode_combobox)

        # Add the UI settings group to layout
        ui_settings_group.setLayout(ui_settings_layout)
        layout.addWidget(ui_settings_group)

        # Warning box for mandatory settings
        warning_box = QGroupBox("Notice")
        warning_layout = QVBoxLayout()
        warning_label = QLabel("Some settings are mandatory for Nuke because you are working in the Nuke environment.")
        warning_label.setStyleSheet("color: Grey;")
        warning_layout.addWidget(warning_label)
        warning_box.setLayout(warning_layout)
        layout.addWidget(warning_box)

        panel.setLayout(layout)
        return panel

    def code_editor_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # Font Grubu
        font_group = QGroupBox("Font")
        font_layout = QFormLayout()

        # Font Seçici
        font_label = QLabel("Font:")
        font_selector = QFontComboBox()
        font_selector.setObjectName("default_selected_font")
        font_selector.setCurrentFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))  # Varsayılan olarak Consolas
        font_layout.addRow(font_label, font_selector)

        # Font Boyutu ve Zoom with Mouse Wheel
        font_size_spinbox = QSpinBox()
        font_size_spinbox.setMinimumWidth(100)
        font_size_spinbox.setMinimumHeight(30)
        font_size_spinbox.setObjectName("default_font_size")
        font_size_spinbox.setRange(8, 48)
        font_size_spinbox.setValue(11)

        zoom_checkbox = QCheckBox("Zoom with Mouse Wheel")
        zoom_checkbox.setObjectName("is_wheel_zoom")
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(font_size_spinbox)
        font_size_layout.addWidget(zoom_checkbox)

        font_layout.addRow("Font Size:", font_size_layout)

        # Açıklama Metni
        zoom_explanation = QLabel("The default font size is 11. You can scale the font up and down with Ctrl+NumPad+ and Ctrl+NumPad-. "
                                  "The 'Zoom with Mouse Wheel' option allows faster zooming with your mouse wheel.")
        zoom_explanation.setWordWrap(True)
        font_layout.addRow(zoom_explanation)

        # JetBrains Font Install Link
        install_jetbrains_font = QLabel()
        install_jetbrains_font.setText("<a href='https://www.jetbrains.com/fonts/' style='color:white;'>Install JetBrains Mono font for your system</a>")
        install_jetbrains_font.setOpenExternalLinks(True)
        font_layout.addRow(install_jetbrains_font)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Ek Ayarlar Grubu
        extra_settings_group = QGroupBox("Additional Settings")
        extra_layout = QFormLayout()

        # Tab Size Ayarı
        tab_size_spinbox = QSpinBox()
        tab_size_spinbox.setObjectName("default_tab_size")
        tab_size_spinbox.setRange(2, 8)
        tab_size_layout = QHBoxLayout()
        tab_size_layout.addWidget(tab_size_spinbox)
        tab_size_description = QLabel("Defines the number of spaces per tab.")
        tab_size_layout.addWidget(tab_size_description)
        extra_layout.addRow("Tab Size:", tab_size_layout)

        # Disable Smart Compilation
        disable_smart_compilation_checkbox = QCheckBox("Disable Smart Compilation")
        disable_smart_compilation_checkbox.setObjectName("disable_smart_compilation")
        extra_layout.addRow(disable_smart_compilation_checkbox)

        # Disable Inline Suggestion
        disable_inline_suggestion_checkbox = QCheckBox("Disable Inline Suggestion (Ghosting text)")
        disable_inline_suggestion_checkbox.setObjectName("disable_suggestion")
        extra_layout.addRow(disable_inline_suggestion_checkbox)

        # Disable Fuzzy Compilation
        disable_fuzzy_completion_checkbox = QCheckBox("Disable Fuzzy Completion")
        disable_fuzzy_completion_checkbox.setObjectName("disable_fuzzy_compilation")
        extra_layout.addRow(disable_fuzzy_completion_checkbox)

        # Nuke Completer Settings Grubu
        nuke_completer_group = QGroupBox("Nuke Completer Settings")
        nuke_completer_layout = QFormLayout()
        disable_node_completer_checkbox = QCheckBox("Disable Node Completer")
        disable_node_completer_checkbox.setObjectName("disable_node_completer")
        nuke_completer_layout.addRow(disable_node_completer_checkbox)
        nuke_completer_group.setLayout(nuke_completer_layout)
        extra_layout.addWidget(nuke_completer_group)

        extra_settings_group.setLayout(extra_layout)
        layout.addWidget(extra_settings_group)

        # Kod Önizleme Alanı
        preview_label = QLabel("Font Preview:")
        layout.addWidget(preview_label)

        self.preview_editor = QTextEdit()
        self.preview_editor.setReadOnly(True)
        self.preview_editor.setText(
            """def apply_effect(node):
    node.setInput(0, 'Image')
    node.knob('color').setValue(0.5)
    for i in range(10):
        node.knob('fade').setValue(i * 0.1)
    print("Effect applied")
    return node"""
        )
        layout.addWidget(self.preview_editor)

        # Font ve Boyut Seçiminde Değişiklik Olduğunda Önizlemeyi Güncelle
        font_selector.currentFontChanged.connect(lambda font: self.preview_editor.setFont(font))
        font_size_spinbox.valueChanged.connect(lambda size: self.preview_editor.setFontPointSize(size))

        panel.setLayout(layout)
        return panel

    def environment_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # Memory Settings Group
        memory_group = QGroupBox("Memory Settings")
        memory_layout = QFormLayout()

        memory_limit_spinbox = QSpinBox()
        memory_limit_spinbox.setObjectName("memory_limit_settings")
        memory_limit_spinbox.setRange(256, 32768)
        memory_limit_spinbox.setSuffix(" MB")
        memory_layout.addRow("Memory Limit:", memory_limit_spinbox)
        memory_limit_spinbox.setMinimumWidth(100)
        memory_limit_spinbox.setMinimumHeight(30)

        timeout_spinbox = QSpinBox()
        timeout_spinbox.setObjectName("timeout_limit_settings")
        timeout_spinbox.setRange(1, 60)
        timeout_spinbox.setSuffix(" mins")
        timeout_spinbox.setMinimumWidth(100)
        timeout_spinbox.setMinimumHeight(30)
        memory_layout.addRow("Script Timeout:", timeout_spinbox)

        cpu_priority_checkbox = QCheckBox("Set High CPU Priority")
        cpu_priority_checkbox.setObjectName("cpu_priority_settings")
        memory_layout.addRow(cpu_priority_checkbox)

        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)

        # Nuke Path Settings Group
        nuke_path_group = QGroupBox("Nuke Path Settings")
        nuke_path_layout = QFormLayout()

        nuke_plugin_path_1 = QLineEdit("/path/to/nuke/plugin1")
        nuke_plugin_path_1.setObjectName("nuke_plugin_path_01")
        nuke_plugin_path_2 = QLineEdit("/path/to/nuke/plugin2")
        nuke_plugin_path_2.setObjectName("nuke_plugin_path_02")
        nuke_path_layout.addRow("Plugin Path 1:", nuke_plugin_path_1)
        nuke_path_layout.addRow("Plugin Path 2:", nuke_plugin_path_2)

        nuke_path_group.setLayout(nuke_path_layout)
        layout.addWidget(nuke_path_group)

        panel.setLayout(layout)
        return panel

    def licence_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # Lisans Açıklaması
        licence_info = QLabel("Please enter your license key or load a license file to activate the product.")
        licence_info.setWordWrap(True)
        layout.addWidget(licence_info)

        # .lic Dosyasını Yükleme
        load_lic_button = QPushButton("Load .lic File")
        load_lic_button.clicked.connect(self.load_licence_file)
        layout.addWidget(load_lic_button)

        # Lisans Anahtarı Girişi
        licence_key_group = QGroupBox("Enter License Key")
        licence_key_layout = QFormLayout()
        licence_key_input = QLineEdit()
        licence_key_layout.addRow("License Key:", licence_key_input)
        licence_key_group.setLayout(licence_key_layout)
        layout.addWidget(licence_key_group)

        # Mevcut Lisans Durumu
        licence_status = QLabel("Current License Status: Not Activated")
        layout.addWidget(licence_status)

        # Documentation Grup
        documentation_group = QGroupBox("Documentation")
        doc_layout = QVBoxLayout()
        doc_links = [
            "<a href='https://nuke.docs.example.com' style='color:white;'>Nuke Documentation</a>",
            "<a href='https://nuke.support.example.com' style='color:white;'>Nuke Support</a>",
            "<a href='https://nuke.community.example.com' style='color:white;'>Nuke Community</a>",
            "<a href='https://nuke.community.example.com' style='color:white;'>Code Editor Document</a>",
            "<a href='https://nuke.community.example.com' style='color:white;'>Licence Problems?</a>",

        ]
        for link in doc_links:
            doc_label = QLabel(link)
            doc_label.setOpenExternalLinks(True)
            doc_layout.addWidget(doc_label)
        documentation_group.setLayout(doc_layout)
        layout.addWidget(documentation_group)

        panel.setLayout(layout)
        return panel

    def github_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # Github Bilgilendirme Metni
        github_info = QLabel("Github Ayarları: Github entegrasyonu için gerekli bilgileri ve token ayarlarını yapılandırabilirsiniz.")
        github_info.setWordWrap(True)
        layout.addWidget(github_info)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Github Kullanıcı Adı
        username_group = QGroupBox("Github Username")
        username_layout = QFormLayout()
        username_input = QLineEdit()
        username_layout.addRow("Username:", username_input)
        username_group.setLayout(username_layout)
        layout.addWidget(username_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # GitHub Token
        token_group = QGroupBox("Github Token")
        token_layout = QFormLayout()
        token_input = QLineEdit()
        token_input.setEchoMode(QLineEdit.Password)  # Güvenlik için gizli giriş
        token_layout.addRow("Token:", token_input)
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Daha Fazla Bilgi Linki
        more_info_label = QLabel()
        more_info_label.setText('''<a href='#', 
                                 style=color:white>Get Help...</a>''')
        more_info_label.setOpenExternalLinks(True)
        layout.addWidget(more_info_label)

        panel.setLayout(layout)
        return panel

    def other_apps_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # PyCharm Ayarları
        pycharm_group = QGroupBox("PyCharm")
        pycharm_layout = QVBoxLayout()
        pycharm_description = QLabel("PyCharm, Python geliştirmeleri için güçlü bir IDE'dir. "
                                     "Yüksek performans, entegre hata ayıklama ve otomatik tamamlama sağlar.")
        pycharm_description.setWordWrap(True)
        pycharm_layout.addWidget(pycharm_description)
        pycharm_group.setLayout(pycharm_layout)
        layout.addWidget(pycharm_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # VS Code Ayarları
        vscode_group = QGroupBox("VS Code")
        vscode_layout = QVBoxLayout()
        vscode_description = QLabel("VS Code, hafif ama güçlü bir editördür. Çeşitli programlama dilleriyle uyumludur "
                                    "ve zengin eklenti desteğine sahiptir.")
        vscode_description.setWordWrap(True)
        vscode_layout.addWidget(vscode_description)
        vscode_group.setLayout(vscode_layout)
        layout.addWidget(vscode_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Atom Ayarları
        atom_group = QGroupBox("Atom")
        atom_layout = QVBoxLayout()
        atom_description = QLabel("Atom, açık kaynaklı ve modern bir metin editörüdür. "
                                  "Özelleştirilebilir ve geniş bir eklenti yelpazesine sahiptir.")
        atom_description.setWordWrap(True)
        atom_layout.addWidget(atom_description)
        atom_group.setLayout(atom_layout)
        layout.addWidget(atom_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Sublime Editor Ayarları
        sublime_group = QGroupBox("Sublime Editor")
        sublime_layout = QVBoxLayout()
        sublime_description = QLabel("Sublime Text, hızlı ve verimli bir metin editörüdür. "
                                     "Sade arayüzü ve güçlü özellikleriyle tanınır.")
        sublime_description.setWordWrap(True)
        sublime_layout.addWidget(sublime_description)
        sublime_group.setLayout(sublime_layout)
        layout.addWidget(sublime_group)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        panel.setLayout(layout)
        return panel

    def load_licence_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load License File", "", "License Files (*.lic)")
        if file_name:
            print(f"Loaded license file: {file_name}")

    # Ayarları Uygula, Kaydet ve Kapat Fonksiyonları
    def apply_settings(self):
        print("Applying settings...")
        self.to_json()

    def save_and_close(self):
        self.save_settings()
        self.close()

    def display_category(self, index):
        self.settings_panels.setCurrentIndex(index)

    def apply_settings_to_widgets(self):
        """Applies loaded settings to widgets."""
        # General Panel
        general_panel = self.settings_panels.widget(0)
        general_data = self.settings.get("General", {})
        for widget in general_panel.findChildren(QComboBox):
            if widget.objectName() and widget.objectName() in general_data:
                index = widget.findText(general_data[widget.objectName()])
                if index != -1:  # Değer bulunursa
                    widget.setCurrentIndex(index)

        # Code Editor Panel
        code_editor_panel = self.settings_panels.widget(1)
        code_editor_data = self.settings.get("Code Editor", {})
        for widget in code_editor_panel.findChildren(QFontComboBox):
            font_family = code_editor_data.get(widget.objectName(), "Consolas")  # Varsayılan font
            widget.setCurrentFont(QFont(font_family))  # JSON'dan gelen değeri ayarla
        for widget in code_editor_panel.findChildren(QSpinBox):
            widget.setValue(code_editor_data.get(widget.objectName(), widget.value()))
        for widget in code_editor_panel.findChildren(QCheckBox):
            widget.setChecked(code_editor_data.get(widget.objectName(), widget.isChecked()))

        # Environment Panel
        environment_panel = self.settings_panels.widget(2)
        environment_data = self.settings.get("Environment", {})
        for widget in environment_panel.findChildren(QSpinBox):
            widget.setValue(environment_data.get(widget.objectName(), widget.value()))
        for widget in environment_panel.findChildren(QLineEdit):
            widget.setText(environment_data.get(widget.objectName(), widget.text()))

        # Licence Panel
        licence_panel = self.settings_panels.widget(3)
        licence_data = self.settings.get("Licence", {})
        for widget in licence_panel.findChildren(QLineEdit):
            widget.setText(licence_data.get(widget.objectName(), widget.text()))

        # GitHub Panel
        github_panel = self.settings_panels.widget(4)
        github_data = self.settings.get("Github", {})
        for widget in github_panel.findChildren(QLineEdit):
            widget.setText(github_data.get(widget.objectName(), widget.text()))

        # Other Apps Panel
        other_apps_panel = self.settings_panels.widget(5)
        other_apps_data = self.settings.get("Other Apps", {})
        for widget in other_apps_panel.findChildren(QLabel):
            widget.setText(other_apps_data.get(widget.objectName(), widget.text()))

    def to_json(self):
        """Saves the current state of all widgets to the settings file."""
        settings_data = {}

        # General Settings
        general_data = {}
        general_panel = self.settings_panels.widget(0)  # General Panel
        for widget in general_panel.findChildren(QCheckBox):
            if widget.objectName():
                general_data[widget.objectName()] = widget.isChecked()
        for widget in general_panel.findChildren(QComboBox):  # QComboBox'ları ekleyin
            if widget.objectName():
                general_data[widget.objectName()] = widget.currentText()  # Seçili metni al
        settings_data["General"] = general_data

        # Code Editor Settings
        code_editor_data = {}
        code_editor_panel = self.settings_panels.widget(1)
        for widget in code_editor_panel.findChildren(QFontComboBox):
            if widget.objectName():
                code_editor_data[widget.objectName()] = widget.currentFont().family()
        for widget in code_editor_panel.findChildren(QSpinBox):
            if widget.objectName():
                code_editor_data[widget.objectName()] = widget.value()
        for widget in code_editor_panel.findChildren(QCheckBox):
            if widget.objectName():
                code_editor_data[widget.objectName()] = widget.isChecked()
        settings_data["Code Editor"] = code_editor_data

        # Environment Settings
        environment_data = {}
        environment_panel = self.settings_panels.widget(2)
        for widget in environment_panel.findChildren(QSpinBox):
            if widget.objectName():
                environment_data[widget.objectName()] = widget.value()
        for widget in environment_panel.findChildren(QLineEdit):
            if widget.objectName():
                environment_data[widget.objectName()] = widget.text()
        settings_data["Environment"] = environment_data

        # Licence Settings
        licence_data = {}
        licence_panel = self.settings_panels.widget(3)
        for widget in licence_panel.findChildren(QLineEdit):
            if widget.objectName():
                licence_data[widget.objectName()] = widget.text()
        settings_data["Licence"] = licence_data

        # GitHub Settings
        github_data = {}
        github_panel = self.settings_panels.widget(4)
        for widget in github_panel.findChildren(QLineEdit):
            if widget.objectName():
                github_data[widget.objectName()] = widget.text()
        settings_data["Github"] = github_data

        # Other Apps Settings
        other_apps_data = {}
        other_apps_panel = self.settings_panels.widget(5)
        for widget in other_apps_panel.findChildren(QLabel):
            if widget.objectName():
                other_apps_data[widget.objectName()] = widget.text()
        settings_data["Other Apps"] = other_apps_data

        # Save JSON to file
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(settings_data, file, indent=4, ensure_ascii=False)

        print(f"Settings saved to {self.SETTINGS_FILE}")


def launch_settings():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    settings_window = SettingsWindow()
    settings_window.show()
    app.exec_()

