from PySide2.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QWidget, QLabel, QFormLayout, QCheckBox, QSpinBox,
    QPushButton, QStackedWidget, QColorDialog, QSlider, QLineEdit,
    QComboBox, QTabWidget, QFrame, QSpacerItem, QSizePolicy
)
from PySide2.QtGui import QColor
from PySide2.QtCore import Qt


class SettingsWindow(QMainWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()
        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 900, 700)

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Left-side menu (Categories)
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(250)
        self.menu_list.itemClicked.connect(self.switch_category)
        main_layout.addWidget(self.menu_list)

        # Right-side settings area
        self.settings_area = QStackedWidget()
        main_layout.addWidget(self.settings_area)

        self.setCentralWidget(central_widget)

        # Add categories to the menu
        self.add_category("General Settings", self.general_settings_ui())
        self.add_category("Editor Settings", self.editor_settings_ui())
        self.add_category("Code Completion", self.completion_settings_ui())
        self.add_category("Advanced Settings", self.advanced_settings_ui())
        self.add_category("Themes & Colors", self.theme_settings_ui())
        self.add_category("GitHub Integration", self.github_integration_ui())
        self.add_category("License Management", self.license_management_ui())
        self.add_category("Donate", self.donate_ui())

        # Set the first category as default
        self.menu_list.setCurrentRow(0)

    def add_category(self, name, widget):
        """Add a category name and its corresponding widget to the menu."""
        item = QListWidgetItem(name)
        self.menu_list.addItem(item)
        self.settings_area.addWidget(widget)

    def switch_category(self, item):
        """Switch to the selected category."""
        index = self.menu_list.row(item)
        self.settings_area.setCurrentIndex(index)

    def general_settings_ui(self):
        """UI for General Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Theme color selection
        self.theme_color_button = QPushButton("Select Theme Color")
        self.theme_color_button.clicked.connect(self.choose_theme_color)
        layout.addRow("Theme Color:", self.theme_color_button)

        # Language selection
        language_combo = QComboBox()
        language_combo.addItems(["English", "Spanish", "French", "German", "Chinese"])
        layout.addRow("Language:", language_combo)

        # Auto-update
        auto_update_check = QCheckBox("Enable Auto-Update")
        layout.addWidget(auto_update_check)

        return widget

    def editor_settings_ui(self):
        """UI for Editor Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Font size selection
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 24)
        font_size_spin.setValue(12)
        layout.addRow("Font Size:", font_size_spin)

        # Auto-save interval
        auto_save_spin = QSpinBox()
        auto_save_spin.setRange(1, 60)
        layout.addRow("Auto-Save Interval (minutes):", auto_save_spin)

        # Show line numbers
        show_line_numbers = QCheckBox("Show Line Numbers")
        show_line_numbers.setChecked(True)
        layout.addWidget(show_line_numbers)

        return widget

    def completion_settings_ui(self):
        """UI for Code Completion Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Enable completion
        enable_completer = QCheckBox("Enable Code Completion")
        enable_completer.setChecked(True)
        layout.addRow(enable_completer)

        # Sensitivity level
        sensitivity_slider = QSlider(Qt.Horizontal)
        sensitivity_slider.setRange(1, 10)
        sensitivity_slider.setValue(5)
        layout.addRow("Sensitivity Level:", sensitivity_slider)

        # Add keyword
        self.keyword_input = QLineEdit()
        self.add_keyword_button = QPushButton("Add Keyword")
        self.add_keyword_button.clicked.connect(self.add_keyword)
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(self.keyword_input)
        keyword_layout.addWidget(self.add_keyword_button)
        layout.addRow("Add New Keyword:", keyword_layout)

        return widget

    def advanced_settings_ui(self):
        """UI for Advanced Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Enable linting
        enable_linting = QCheckBox("Enable Code Linting")
        layout.addRow(enable_linting)

        # Enable debugging mode
        enable_debugging = QCheckBox("Enable Debugging Mode")
        layout.addRow(enable_debugging)

        # Line spacing
        line_spacing_spin = QSpinBox()
        line_spacing_spin.setRange(1, 5)
        layout.addRow("Line Spacing:", line_spacing_spin)

        return widget

    def theme_settings_ui(self):
        """UI for Theme & Color Settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        color_form = QFormLayout()
        layout.addLayout(color_form)

        # Primary color
        primary_color_button = QPushButton("Select Primary Color")
        primary_color_button.clicked.connect(self.choose_primary_color)
        color_form.addRow("Primary Color:", primary_color_button)

        # Secondary color
        secondary_color_button = QPushButton("Select Secondary Color")
        secondary_color_button.clicked.connect(self.choose_secondary_color)
        color_form.addRow("Secondary Color:", secondary_color_button)

        # Accent color
        accent_color_button = QPushButton("Select Accent Color")
        accent_color_button.clicked.connect(self.choose_accent_color)
        color_form.addRow("Accent Color:", accent_color_button)

        # Theme switch
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark", "Solarized"])
        color_form.addRow("Theme:", theme_combo)

        return widget

    def github_integration_ui(self):
        """UI for GitHub Integration Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # GitHub username
        github_username = QLineEdit()
        layout.addRow("GitHub Username:", github_username)

        # GitHub token
        github_token = QLineEdit()
        github_token.setEchoMode(QLineEdit.Password)
        layout.addRow("GitHub Personal Access Token:", github_token)

        # Test connection button
        test_connection_button = QPushButton("Test Connection")
        test_connection_button.clicked.connect(self.test_github_connection)
        layout.addWidget(test_connection_button)

        return widget

    def license_management_ui(self):
        """UI for License Management Settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # License key input
        license_key_input = QLineEdit()
        license_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("License Key:", license_key_input)

        # Activate license button
        activate_license_button = QPushButton("Activate License")
        activate_license_button.clicked.connect(self.activate_license)
        layout.addWidget(activate_license_button)

        # License status
        self.license_status = QLabel("Status: Unlicensed")
        layout.addRow(self.license_status)

        return widget

    def donate_ui(self):
        """UI for Donation Settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Donation description
        description = QLabel("Support development by donating:")
        layout.addWidget(description)

        # Donation options
        donation_options = QComboBox()
        donation_options.addItems(["$5", "$10", "$20", "$50", "Custom"])
        layout.addWidget(donation_options)

        # Donation button
        donate_button = QPushButton("Donate Now")
        layout.addWidget(donate_button)

        return widget

    def choose_theme_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.theme_color_button.setStyleSheet(f"background-color: {color.name()};")

    def choose_primary_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.primary_color_button.setStyleSheet(f"background-color: {color.name()};")

    def choose_secondary_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.secondary_color_button.setStyleSheet(f"background-color: {color.name()};")

    def choose_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.accent_color_button.setStyleSheet(f"background-color: {color.name()};")

    def test_github_connection(self):
        # Placeholder function for GitHub connection testing
        print("Testing GitHub connection...")

    def activate_license(self):
        # Placeholder function for license activation
        print("Activating license...")

    def add_keyword(self):
        new_keyword = self.keyword_input.text()
        if new_keyword:
            print(f"Keyword added: {new_keyword}")
            self.keyword_input.clear()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
