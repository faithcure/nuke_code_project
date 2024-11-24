import subprocess
import json
import sys
import requests
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QStackedWidget, QWidget,
    QVBoxLayout, QLabel, QComboBox, QLineEdit, QCheckBox, QSpinBox, QPushButton,
    QHBoxLayout, QFormLayout, QDialogButtonBox, QGroupBox, QTextEdit, QFrame, QFontComboBox, QFileDialog, QSpacerItem,
    QSizePolicy, QMessageBox, QProgressBar, QProgressDialog
)
from PySide2.QtCore import Qt, QThread, Signal
from PySide2.QtGui import QFontDatabase, QFont
import os
import time
import re
from editor.settings.settings_ux import ui_modes

class ModuleInstallerThread(QThread):
    progress_updated = Signal(int, str)  # Signal for progress bar
    download_info = Signal(str)  # Signal for detailed download info
    completed = Signal()  # Signal when installation completes
    error_occurred = Signal(str)  # Signal for errors

    def __init__(self, install_path, required_modules, python_path):
        super().__init__()
        self.install_path = install_path
        self.required_modules = required_modules
        self.python_path = python_path

    def run(self):
        try:
            for i, module in enumerate(self.required_modules):
                self.progress_updated.emit(i, f"Installing {module}...")

                # Start the pip process
                process = subprocess.Popen(
                    [self.python_path, "-m", "pip", "install", module, "--target", self.install_path, "--progress-bar", "off"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Parse the output of pip to extract download details
                for line in process.stdout:
                    match = re.search(r"(\d+\.?\d*)\s?([kMG]B)\s?/?\s?(\d+\.?\d*)?\s?([kMG]B)?", line)
                    if match:
                        downloaded = match.group(1) + " " + match.group(2)
                        total = match.group(3) + " " + match.group(4) if match.group(3) else "unknown"
                        self.download_info.emit(f"Downloading {module}: {downloaded} of {total}")
                    if "Installing collected packages" in line:
                        self.download_info.emit(f"Installing package files for {module}...")

                # Wait for the process to complete
                process.wait()

                # Check if the process exited with an error
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, process.args)

                time.sleep(0.5)  # Simulate delay for better progress visualization

            self.completed.emit()
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(f"Error while installing {module}:\n{str(e)}")
        except Exception as ex:
            self.error_occurred.emit(f"Unexpected error:\n{str(ex)}")

class SettingsWindow(QMainWindow):
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

    def __init__(self):
        super().__init__()
        self.status_label = None
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("QLabel { color: white; }")

        # **self.settings Özelliğini İlk Olarak Tanımlayın**
        self.settings = self.load_settings()

        # Arama Kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search in settings...")
        self.search_box.textChanged.connect(self.filter_settings)

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
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.search_box)  # Arama kutusunu üst kısma ekle
        main_content_layout = QHBoxLayout()
        main_content_layout.addWidget(self.category_list, 1)
        main_content_layout.addWidget(self.settings_panels, 3)
        main_layout.addLayout(main_content_layout)
        main_layout.addWidget(button_box)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Apply settings to widgets
        self.apply_settings_to_widgets()

    def filter_settings(self, search_text):
        """Highlights matching widgets based on the search text or resets styles when empty."""
        search_text = search_text.lower()

        DEFAULT_STYLE = "background-color: none; "  # Varsayılan stil
        HIGHLIGHT_STYLE = "background-color: rgba(247, 153, 42, 0.5); "  # Saydam turuncu

        for category_index in range(self.settings_panels.count()):
            panel = self.settings_panels.widget(category_index)
            found = False  # Panelde herhangi bir eşleşme olup olmadığını takip etmek için

            for widget_type in [QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox]:
                for widget in panel.findChildren(widget_type):
                    widget_name = widget.objectName().lower() if widget.objectName() else ""
                    widget_text = widget.text().lower() if hasattr(widget, "text") else ""

                    if search_text:  # Eğer arama metni varsa
                        if search_text in widget_name or search_text in widget_text:
                            widget.setStyleSheet(HIGHLIGHT_STYLE)
                            found = True
                        else:
                            widget.setStyleSheet(DEFAULT_STYLE)
                    else:  # Arama kutusu boşsa
                        widget.setStyleSheet(DEFAULT_STYLE)

            # Kategori gizlenmesin ama highlight durumu ayarlansın
            self.category_list.item(category_index).setHidden(False)

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
        layout = QVBoxLayout()

        # Language & Theme settings in a horizontal layout
        lang_theme_layout = QHBoxLayout()

        language_combobox = QComboBox()
        language_combobox.setObjectName("default_language")
        language_combobox.addItem("English")
        language_combobox.setEnabled(False)

        theme_combobox = QComboBox()
        theme_combobox.setObjectName("default_theme")
        theme_combobox.addItem("Nuke Default")
        theme_combobox.setEnabled(False)

        # Separator between language and theme
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: lightgrey;")

        lang_theme_layout.addWidget(QLabel("Language:"))
        lang_theme_layout.addWidget(language_combobox)
        lang_theme_layout.addWidget(separator)
        lang_theme_layout.addWidget(QLabel("Theme:"))
        lang_theme_layout.addWidget(theme_combobox)
        lang_theme_layout.addStretch()  # Push to the left
        layout.addLayout(lang_theme_layout)

        # Add explanatory text below language and theme
        settings_note = QLabel("Some settings are mandatory for Nuke because you are working in the Nuke environment.")
        settings_note.setStyleSheet("color: Grey;")
        settings_note.setWordWrap(True)
        layout.addWidget(settings_note)

        # Start at Login
        start_group = QGroupBox("Start at Login")
        start_layout = QVBoxLayout()
        startup_checkbox = QCheckBox("Enable start at login")
        startup_checkbox.setObjectName("startup_checkbox")
        start_description = QLabel("Automatically start the application when logging into the system.")
        start_description.setStyleSheet("color: Grey;")
        start_description.setWordWrap(True)
        start_layout.addWidget(startup_checkbox)
        start_layout.addWidget(start_description)
        start_group.setLayout(start_layout)
        start_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(start_group)

        # UI Settings Group for Code Editor Default Interface
        ui_settings_group = QGroupBox("UI Settings")
        ui_settings_layout = QFormLayout()

        # Default Interface Mode ComboBox
        interface_mode_combobox = QComboBox()
        interface_mode_combobox.setObjectName("default_interface_mode")
        interface_label = QLabel("Set default UX automatically when this ide is open.")
        interface_label.setStyleSheet("color: Grey;")

        interface_mode_combobox.addItems(ui_modes.keys())
        interface_mode_combobox.setToolTip("Set the default startup interface mode for the code editor.")
        ui_settings_layout.addRow("Default Interface Mode:", interface_mode_combobox)
        ui_settings_layout.addRow(interface_label)
        ui_settings_group.setLayout(ui_settings_layout)
        ui_settings_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(ui_settings_group)

        # Add "Resume Last Project" Option
        last_project_group = QGroupBox("Project Settings")
        last_project_layout = QVBoxLayout()
        last_project_checkbox = QCheckBox("Resume with last worked project")
        last_project_checkbox.setObjectName("resume_last_project")
        last_project_note = QLabel("Otherwise, the IDE will start with an empty session.")
        last_project_note.setStyleSheet("color: Grey;")
        last_project_note.setWordWrap(True)
        last_project_layout.addWidget(last_project_checkbox)
        last_project_layout.addWidget(last_project_note)
        last_project_group.setLayout(last_project_layout)
        last_project_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(last_project_group)

        # Add spacer for pushing elements up in the window
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

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

        # Agreement Checkbox
        agreement_group = QGroupBox("Terms and Agreement")
        agreement_layout = QVBoxLayout()
        agreement_checkbox = QCheckBox(
            "By proceeding, you confirm that you have the advanced technical knowledge required to configure\n"
            "and use this integration. You accept that any unintended issues or damages are at your own \n"
            "responsibility. Please proceed cautiously. By using this integration, you acknowledge that unexpected\n"
            "issues may arise and agree that the provider is not responsible for any losses or damages incurred."
        )
        agreement_checkbox.setChecked(True)
        agreement_checkbox.setEnabled(False)
        agreement_layout.addWidget(agreement_checkbox)
        agreement_group.setLayout(agreement_layout)
        layout.addWidget(agreement_group)

        # GitHub Information
        github_info = QLabel(
            "GitHub Settings: Configure your GitHub integration with username and personal access token.")
        github_info.setEnabled(False)
        github_info.setWordWrap(True)
        layout.addWidget(github_info)
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # GitHub Credentials Group
        credentials_group = QGroupBox("GitHub Credentials")
        credentials_layout = QFormLayout()

        # Username Input
        username_input = QLineEdit()
        username_input.setObjectName("github_username")
        credentials_layout.addRow("Username:", username_input)

        # Token Input
        token_input = QLineEdit()
        token_input.setObjectName("github_token")
        token_input.setEchoMode(QLineEdit.Password)
        credentials_layout.addRow("Token:", token_input)

        # Repository URL Input
        repo_url_input = QLineEdit()
        repo_url_input.setObjectName("github_repo_url")
        repo_url_input.setPlaceholderText("https://github.com/username/repository.git")
        credentials_layout.addRow("Repository URL:", repo_url_input)

        # Validate Button
        validate_button = QPushButton("Test Connection")
        validate_button.clicked.connect(lambda: self.validate_credentials(username_input, token_input))
        credentials_layout.addRow(validate_button)

        # Status Label
        self.status_label = QLabel("Not validated")
        self.status_label.setStyleSheet("color: #ff6f61; font-weight: bold;")  # Pastel kırmızı
        credentials_layout.addRow(self.status_label)

        # Token Description
        token_description = QLabel(
            "Provide a personal access token to enable secure GitHub operations.\n"
            "Ensure the token has the necessary scopes for your integration (e.g., repo, workflow)."
        )
        token_description.setWordWrap(True)
        credentials_layout.addRow(token_description)

        # Documentation Link
        documentation_label = QLabel(
            "<a href='https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token' "
            "style='color:white;'>Learn how to create a personal access token</a>"
        )
        documentation_label.setOpenExternalLinks(True)
        credentials_layout.addRow(documentation_label)

        credentials_group.setLayout(credentials_layout)
        layout.addWidget(credentials_group)

        # Add spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Environment Check Group
        environment_group = QGroupBox("Environment Check")
        environment_layout = QVBoxLayout()

        # Modules Message
        modules_message = QLabel()
        modules_message.setWordWrap(True)

        # Modül kontrolü
        install_path = os.path.join(os.path.dirname(__file__), "modules")
        required_modules = ["gitdb", "GitPython"]
        installed_modules = self.check_github_modules(install_path, required_modules)
        path_in_sys_path = install_path in sys.path

        if installed_modules and path_in_sys_path:
            modules_message.setText(
                "GitHub modules are successfully installed, and the 'modules' path is added to init.py."
            )
            modules_message.setStyleSheet("color: palegreen;")
        elif installed_modules and not path_in_sys_path:
            modules_message.setText(
                "GitHub modules are installed, but the 'modules' directory is not in sys.path."
            )
            modules_message.setStyleSheet("color: lightcoral;")

            # Buton ekle
            fix_path_button = QPushButton("Fix Path")
            fix_path_button.setStyleSheet("background-color: lightcoral; color: white;")
            fix_path_button.clicked.connect(lambda: self.show_fix_instructions(install_path))
            environment_layout.addWidget(fix_path_button)
        else:
            modules_message.setText("Required GitHub modules are missing in the specified environment.")
            modules_message.setStyleSheet("color: lightcoral;")

        environment_layout.addWidget(modules_message)

        # Install Button
        install_button = QPushButton("Install GitHub Modules")
        install_button.setEnabled(not installed_modules)
        install_button.clicked.connect(self.install_github_modules)
        environment_layout.addWidget(install_button)

        # Update Button
        update_button = QPushButton("Update GitHub Modules")
        update_button.setEnabled(installed_modules)
        update_button.clicked.connect(lambda: self.update_github_modules(install_path, required_modules))
        environment_layout.addWidget(update_button)

        # Explanation
        explanation_label = QLabel(
            "The GitHub integration requires specific modules to function. If they are missing, install them using the button above."
        )
        explanation_label.setWordWrap(True)
        environment_layout.addWidget(explanation_label)

        environment_group.setLayout(environment_layout)
        layout.addWidget(environment_group)

        # Documentation Link
        doc_link = QLabel("<a href='https://docs.github.com/en' style='color:white;'>GitHub Documentation</a>")
        doc_link.setOpenExternalLinks(True)
        layout.addWidget(doc_link)

        panel.setLayout(layout)
        return panel

    def validate_credentials(self, username_input, token_input):
        """
        Kullanıcıdan gelen GitHub kullanıcı adı ve token bilgilerini doğrular.
        """
        username = username_input.text().strip()
        token = token_input.text().strip()

        if not username or not token:
            QMessageBox.warning(self, "Validation Failed", "Username or token cannot be empty.")
            return

        if self.check_github_credentials(username, token):
            # Doğrulama başarılıysa
            self.status_label.setText("Validated successfully")
            self.status_label.setStyleSheet("color: #8bc34a; font-weight: bold;")  # Pastel yeşil
            # QMessageBox.information(self, "Validation Successful", "The GitHub credentials are valid.")
        else:
            # Doğrulama başarısızsa
            self.status_label.setText("Validation failed")
            self.status_label.setStyleSheet("color: #ff6f61; font-weight: bold;")  # Pastel kırmızı
            QMessageBox.critical(self, "Validation Failed", "Invalid GitHub credentials. Please try again.")

    def check_github_credentials(self, username, token):
        """
        GitHub kullanıcı adı ve token doğrulama işlevi.
        """
        if not username or not token:
            QMessageBox.critical(
                self,
                "Validation Error",
                "Please enter both username and token."
            )
            return False

        try:
            url = "https://api.github.com/user"
            response = requests.get(url, auth=(username, token))

            if response.status_code == 200:
                # API'den dönen kullanıcı adı
                api_username = response.json().get('login', '')

                # Kullanıcı adı eşleşiyor mu?
                if username == api_username:
                    QMessageBox.information(
                        self,
                        "Validation Successful",
                        f"Welcome, {api_username}!, The GitHub credentials are valid."
                    )
                    return True
                else:
                    QMessageBox.critical(
                        self,
                        "Username Mismatch",
                        f"Provided username does not match the token owner.\n"
                        f"Expected: {api_username}\nProvided: {username}"
                    )
                    return False
            elif response.status_code == 401:
                QMessageBox.critical(
                    self,
                    "Authentication Failed",
                    "Authentication failed. Please check your username and token."
                )
                return False
            else:
                QMessageBox.critical(
                    self,
                    "Authentication Error",
                    f"Unexpected error: {response.json().get('message', 'Unknown error')}."
                )
                return False
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Network Error", f"An error occurred: {e}")
            return False

    def show_fix_instructions(self, install_path):
        """
        Provide a clear explanation and option to automatically add the modules path.
        Ensures compatibility across all platforms (Windows, macOS, Linux).
        """
        confirmation = QMessageBox.question(
            self,
            "Fix Path Confirmation",
            f"The required modules path is not in sys.path. It may be corrupted.\n\n"
            f"We can correct the following files:\n\n"
            f"{install_path}\n\n"
            "Would you like to proceed with this change?\n\n"
            "You will need to restart Nuke to apply the changes.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            try:
                # Determine the init_ide.py path
                nuke_code_project_dir = os.path.join(os.path.expanduser("~"), ".nuke", "nuke_code_project")
                ide_init_path = os.path.join(nuke_code_project_dir, "init_ide.py")

                # Ensure the directory exists
                os.makedirs(nuke_code_project_dir, exist_ok=True)

                # Check if the file exists and is writable
                if os.path.exists(ide_init_path) and not os.access(ide_init_path, os.W_OK):
                    raise PermissionError(f"Cannot write to {ide_init_path}. Check file permissions.")

                # Append the install path to init_ide.py
                with open(ide_init_path, "a") as ide_init_file:
                    ide_init_file.write(f"\n# Automatically added modules path\n")
                    ide_init_file.write(f"import sys\n")
                    ide_init_file.write(f"sys.path.append({repr(install_path)})\n")



                self.prompt_restart_nuke()

            except PermissionError as pe:
                QMessageBox.critical(self, "Permission Error", str(pe))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update init_ide.py: {e}")
        else:
            QMessageBox.information(
                self,
                "Action Canceled",
                "The path was not added. If you change your mind, you can use the Fix Path option again."
            )

    def install_github_modules(self):
        """
        Install GitHub modules to the 'modules' directory using a background thread and show detailed progress.
        After installation, add the 'modules' path to sys.path in the .nuke/init.py file and ask the user to restart Nuke.
        """
        # Hedef dizini belirle
        install_path = os.path.join(os.path.dirname(__file__), "modules")
        required_modules = ["gitdb", "GitPython"]

        # .nuke klasörünü bul
        user_home = os.path.expanduser("~")
        nuke_dir = os.path.join(user_home, ".nuke")
        init_path = os.path.join(nuke_dir, "init.py")
        print (init_path, "init path")

        # 'modules' klasörü yoksa oluştur
        if not os.path.exists(install_path):
            os.makedirs(install_path)

        # Sistem Python yorumlayıcısını bul
        python_path = "python"
        if "PYTHON_HOME" in os.environ:
            python_path = os.path.join(os.environ["PYTHON_HOME"], "python.exe")
        else:
            # Kullanıcının ana dizinini bul
            user_home = os.path.expanduser("~")  # Dinamik olarak kullanıcı dizinini alır

            possible_paths = [
                # Dinamik Windows Yolları
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python311", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python310", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python39", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python38", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python37", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Microsoft", "WindowsApps", "python.exe"),
                os.path.join(user_home, "anaconda3", "python.exe"),
                os.path.join(user_home, "miniconda3", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Continuum", "anaconda3", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Continuum", "miniconda3", "python.exe"),

                # Sabit Windows Yolları
                r"C:\Python311\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python39\python.exe",
                r"C:\Python38\python.exe",
                r"C:\Python37\python.exe",
                r"C:\Python36\python.exe",
                r"C:\Program Files\Python311\python.exe",
                r"C:\Program Files\Python310\python.exe",
                r"C:\Program Files\Python39\python.exe",
                r"C:\Program Files\Python38\python.exe",
                r"C:\Program Files (x86)\Python37\python.exe",
                r"C:\Program Files (x86)\Python36\python.exe",

                # Linux ve MacOS Yolları
                "/usr/bin/python3.11",
                "/usr/bin/python3.10",
                "/usr/bin/python3.9",
                "/usr/bin/python3.8",
                "/usr/bin/python3.7",
                "/usr/bin/python3.6",
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3.11",
                "/usr/local/bin/python3.10",
                "/usr/local/bin/python3.9",
                "/usr/local/bin/python3.8",
                "/usr/local/bin/python3.7",
                "/usr/local/bin/python3",
                "/usr/local/bin/python",
                "/opt/python3.11/bin/python3",
                "/opt/python3.10/bin/python3",
                "/opt/python3.9/bin/python3",
                "/opt/python3.8/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.8/bin/python3",

                # Virtualenv veya Conda Sanal Ortamları
                os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin", "python"),
                os.path.join(os.environ.get("CONDA_PREFIX", ""), "bin", "python"),

                # Pyenv Python Yolları
                os.path.join(user_home, ".pyenv", "shims", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.11.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.10.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.9.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.8.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.7.0", "bin", "python"),

                # Custom Paths
                r"D:\Python311\python.exe",
                r"D:\Python310\python.exe",
                r"D:\Python39\python.exe"
            ]

            # Çıktıyı kontrol et
            for path in possible_paths:
                print(f"Checking: {path}")

            for path in possible_paths:
                if os.path.exists(path):
                    python_path = path
                    break
            else:
                QMessageBox.critical(
                    self,
                    "Python Not Found",
                    "System Python could not be located. Please install Python or specify its path using the PYTHON_HOME environment variable."
                )
                return

        # Progress Dialog oluştur
        progress = QProgressDialog("Installing GitHub modules...", "Cancel", 0, len(required_modules))
        progress.setWindowTitle("Installation Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        # Modül kurulum işlemi için thread başlat
        thread = ModuleInstallerThread(install_path, required_modules, python_path)
        thread.progress_updated.connect(lambda value, text: (
            progress.setValue(value),
            progress.setLabelText(text)
        ))
        thread.download_info.connect(lambda info: progress.setLabelText(info))

        def on_completed():
            try:
                ide_init_path = os.path.join(os.path.dirname(init_path), "init_ide.py")  # Yeni dosya adı ve konumu

                # init_ide.py dosyasını oluştur veya mevcut dosyayı güncelle
                if not os.path.exists(ide_init_path):
                    with open(ide_init_path, "w") as ide_init_file:
                        ide_init_file.write(f"# Added modules path\n")
                        ide_init_file.write(f"import sys\n")
                        ide_init_file.write(f"sys.path.append({repr(install_path)})\n")

                # init.py dosyasını güncelle (import işlemi kontrolü)
                if os.path.exists(init_path):
                    with open(init_path, "r+") as init_file:
                        content = init_file.read()
                        import_statement = "exec(open(os.path.join(os.path.dirname(__file__), 'init_ide.py')).read())"
                        if import_statement not in content:
                            init_file.write(f"\n# Import init_ide.py\n")
                            init_file.write(f"import os\n")
                            init_file.write(f"{import_statement}\n")

                QMessageBox.information(
                    self,
                    "Success",
                    "Modules installed and linked successfully."
                )

            except Exception:
                QMessageBox.warning(
                    self,
                    "Error",
                    "An error occurred during the installation process."
                )

            progress.setValue(len(required_modules))
            self.prompt_restart_nuke()

        thread.completed.connect(on_completed)
        thread.error_occurred.connect(lambda error: QMessageBox.critical(self, "Installation Error", error))
        progress.canceled.connect(lambda: thread.terminate())
        thread.start()

    def update_github_modules(self, install_path, required_modules):
        """
        Update the specified GitHub modules in the 'modules' directory.
        Args:
            install_path (str): Path to the folder where modules are installed.
            required_modules (list): List of required module names to update.
        """
        # Sistem Python yorumlayıcısını bul
        python_path = "python"
        if "PYTHON_HOME" in os.environ:
            python_path = os.path.join(os.environ["PYTHON_HOME"], "python.exe")
        else:
            # Kullanıcının ana dizinini bul
            user_home = os.path.expanduser("~")  # Dinamik olarak kullanıcı dizinini alır

            possible_paths = [
                # Dinamik Windows Yolları
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python311", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python310", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python39", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python38", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python37", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Microsoft", "WindowsApps", "python.exe"),
                os.path.join(user_home, "anaconda3", "python.exe"),
                os.path.join(user_home, "miniconda3", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Continuum", "anaconda3", "python.exe"),
                os.path.join(user_home, "AppData", "Local", "Continuum", "miniconda3", "python.exe"),

                # Sabit Windows Yolları
                r"C:\Python311\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python39\python.exe",
                r"C:\Python38\python.exe",
                r"C:\Python37\python.exe",
                r"C:\Python36\python.exe",
                r"C:\Program Files\Python311\python.exe",
                r"C:\Program Files\Python310\python.exe",
                r"C:\Program Files\Python39\python.exe",
                r"C:\Program Files\Python38\python.exe",
                r"C:\Program Files (x86)\Python37\python.exe",
                r"C:\Program Files (x86)\Python36\python.exe",

                # Linux ve MacOS Yolları
                "/usr/bin/python3.11",
                "/usr/bin/python3.10",
                "/usr/bin/python3.9",
                "/usr/bin/python3.8",
                "/usr/bin/python3.7",
                "/usr/bin/python3.6",
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3.11",
                "/usr/local/bin/python3.10",
                "/usr/local/bin/python3.9",
                "/usr/local/bin/python3.8",
                "/usr/local/bin/python3.7",
                "/usr/local/bin/python3",
                "/usr/local/bin/python",
                "/opt/python3.11/bin/python3",
                "/opt/python3.10/bin/python3",
                "/opt/python3.9/bin/python3",
                "/opt/python3.8/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3",
                "/Library/Frameworks/Python.framework/Versions/3.8/bin/python3",

                # Virtualenv veya Conda Sanal Ortamları
                os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin", "python"),
                os.path.join(os.environ.get("CONDA_PREFIX", ""), "bin", "python"),

                # Pyenv Python Yolları
                os.path.join(user_home, ".pyenv", "shims", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.11.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.10.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.9.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.8.0", "bin", "python"),
                os.path.join(user_home, ".pyenv", "versions", "3.7.0", "bin", "python"),

                # Custom Paths
                r"D:\Python311\python.exe",
                r"D:\Python310\python.exe",
                r"D:\Python39\python.exe"
            ]

            # Çıktıyı kontrol et
            for path in possible_paths:
                print(f"Checking: {path}")

            for path in possible_paths:
                if os.path.exists(path):
                    python_path = path
                    break
            else:
                QMessageBox.critical(
                    self,
                    "Python Not Found",
                    "System Python could not be located. Please install Python or specify its path using the PYTHON_HOME environment variable."
                )
                return

        # Progress Dialog oluştur
        progress = QProgressDialog("Updating GitHub modules...", "Cancel", 0, len(required_modules))
        progress.setWindowTitle("Update Progress")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        # Modül güncelleme işlemi için thread başlat
        thread = ModuleInstallerThread(install_path, required_modules, python_path)

        def on_completed():
            progress.setValue(len(required_modules))
            QMessageBox.information(
                self,
                "Update Complete",
                "GitHub modules have been successfully updated."
            )

        def on_error(error):
            progress.close()
            QMessageBox.critical(self, "Update Error", error)

        thread.progress_updated.connect(lambda value, text: (
            progress.setValue(value),
            progress.setLabelText(text)
        ))

        def on_cancel():
            if thread.isRunning():
                thread.terminate()
            progress.close()

        thread.download_info.connect(lambda info: progress.setLabelText(info))
        thread.completed.connect(on_completed)
        thread.error_occurred.connect(on_error)
        progress.canceled.connect(lambda: thread.terminate())
        progress.canceled.connect(on_cancel)
        thread.start()


    def prompt_restart_nuke(self):
        """
        Prompt the user to restart Nuke after module installation, explaining why it is necessary.
        """
        response = QMessageBox.question(
            self,
            "Restart Nuke",
            "The installed modules will take effect only after restarting Nuke. "
            "Do you want to restart Nuke now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.Yes:
            self.restart_nuke()

    def restart_nuke(self):
        """
        Restart Nuke by terminating the current process and starting a new instance.
        """
        QMessageBox.information(self, "Restarting Nuke", "Nuke is restarting...")
        # Nuke yeniden başlatma işlemi burada yapılabilir
        # (örneğin, os.execv ile mevcut uygulama yeniden başlatılabilir)
        python_executable = sys.executable
        os.execv(python_executable, [python_executable] + sys.argv)

    def check_github_modules(self, install_path, required_modules):
        """
        Check if required modules are present in the specified folder.
        Args:
            install_path (str): Path to the target folder where modules are installed.
            required_modules (list): List of required module names.
        Returns:
            bool: True if all required modules are found, False otherwise.
        """
        if not os.path.exists(install_path):
            return False

        installed_modules = os.listdir(install_path)  # List all directories/files in the install path
        for module in required_modules:
            if not any(module.lower() in item.lower() for item in installed_modules):
                return False
        return True

    def other_apps_settings(self):
        panel = QWidget()
        layout = QVBoxLayout()

        # Description Group
        description_group = QGroupBox("Description Live Links for other Apps.")
        description_layout = QVBoxLayout()
        description_label = QLabel(
            "<div style='line-height:1.3;'>"
            "For those who wish to use an external program at higher standards, this panel contains the necessary explanations. "
            "Thanks to a plugin developed by me, you can dynamically develop Python code within Nuke and perform Node manipulations "
            "using PyCharm or VS Code.<br><br>"
            "You can find the necessary information for setting up VS Code and PyCharm LL here:<br>"
            "<a href='https://example.com/vscode-docs' style='color:white;'>VS Code LL Documentation</a><br>"
            "<a href='https://example.com/pycharm-docs' style='color:white;'>PyCharm LL Documentation</a>"
            "</div>"
        )
        description_label.setWordWrap(True)
        description_layout.addWidget(description_label)
        description_label.setOpenExternalLinks(True)
        description_group.setLayout(description_layout)
        layout.addWidget(description_group)

        # PyCharm Group
        pycharm_group = QGroupBox("Configure PyCharm")
        pycharm_layout = QVBoxLayout()
        pycharm_label = QLabel(
            "You can find the necessary information for setting up PyCharm Live Link here: "
            "<a href='https://example.com/pycharm-docs' style='color:white;'>PyCharm Live Link Documentation</a>"
        )
        pycharm_label.setOpenExternalLinks(True)
        pycharm_label.setWordWrap(True)
        pycharm_layout.addWidget(pycharm_label)
        pycharm_group.setLayout(pycharm_layout)
        layout.addWidget(pycharm_group)

        # VS Code Group
        vscode_group = QGroupBox("Configure VS Code")
        vscode_layout = QVBoxLayout()
        vscode_label = QLabel(
            "You can find the necessary information for setting up VS Code Live Link here: "
            "<a href='https://example.com/vscode-docs' style='color:white;'>VS Code Live Link Documentation</a>"
        )
        vscode_label.setOpenExternalLinks(True)
        vscode_label.setWordWrap(True)
        vscode_layout.addWidget(vscode_label)
        vscode_group.setLayout(vscode_layout)
        layout.addWidget(vscode_group)

        # Add spacer to push Groups upward
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

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
        """
        Applies settings from the loaded JSON file to the widgets in the settings panels.

        This function maps each widget's objectName to the corresponding setting key in the JSON data.
        The settings panels are indexed in the following order:
        - 0: General
        - 1: Code Editor
        - 2: Environment
        - 3: Licence
        - 4: GitHub
        - 5: Other Apps
        """

        # General Panel
        general_panel = self.settings_panels.widget(0)
        general_data = self.settings.get("General", {})
        for widget in general_panel.findChildren(QCheckBox):
            if widget.objectName() and widget.objectName() in general_data:
                widget.setChecked(general_data[widget.objectName()])
        for widget in general_panel.findChildren(QComboBox):
            if widget.objectName() and widget.objectName() in general_data:
                index = widget.findText(general_data[widget.objectName()])
                if index != -1:  # Ensure the value exists
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