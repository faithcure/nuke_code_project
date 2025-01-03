import ast
import importlib
import json
import os
import re
import shutil
import webbrowser
from functools import partial
from PySide2.QtCore import QPropertyAnimation, QEasingCurve
from PySide2.QtCore import QStringListModel
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtGui import QPixmap, QPainter, QPainterPath, QBrush
from PySide2.QtGui import QTextCursor, QGuiApplication
from PySide2.QtWidgets import *
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QGraphicsDropShadowEffect, QFrame
import editor.code_editor
import editor.core
import editor.output
import editor.new_nuke_project
import editor.dialogs.searchDialogs
import settings.github_utils
import main_toolbar
from editor.nlink import update_nuke_functions, load_nuke_functions
from editor.core import PathFromOS, CodeEditorSettings
from editor.code_editor import CodeEditor
from PySide2.QtWidgets import QDockWidget, QTextEdit, QMainWindow, QPushButton, QHBoxLayout, QWidget
from PySide2.QtCore import Qt, QRect, QSize
from PySide2.QtGui import QColor, QTextCharFormat, QFont
from editor.output import OutputWidget
import traceback
import platform
import socket
import nuke
from editor.output import execute_python_code, execute_nuke_code  # output.py dosyasından fonksiyonları çekiyoruz
from editor.console import ConsoleWidget
from editor.new_nuke_project import NewNukeProjectDialog
from editor.dialogs.searchDialogs import SearchDialog
from editor.dialogs.replaceDialogs import ReplaceDialogs  # Döngüsel içe aktarma sorununu çözmek için fonksiyon içinde import
from editor.dialogs.goToLineDialogs import GoToLineDialog
# from init_ide import settings_path
from settings.github_utils import commit_changes, push_to_github, pull_from_github, get_status
importlib.reload(editor.core)
importlib.reload(editor.code_editor)
importlib.reload(editor.output)
importlib.reload(editor.new_nuke_project)
importlib.reload(editor.dialogs.searchDialogs)
importlib.reload(settings.github_utils)
importlib.reload(main_toolbar)
from editor.code_editor import PygmentsHighlighter
from main_toolbar import MainToolbar
class EditorApp(QMainWindow):
    """
    Main application window for the Nuke Code Editor.

    Features:
    - Provides a custom integrated development environment for Python and Nuke scripting.
    - Includes toolbar, status bar, dock widgets, and tab-based editor functionalities.
    - Supports creating, opening, editing, and saving Python and Nuke script files.
    - Includes additional features such as a workspace explorer, outliner, and customizable UI components.
    """

    def __init__(self):
        super().__init__()

        # Initialize the main toolbar
        MainToolbar.create_toolbar(self)

        # Load settings
        self.settings = CodeEditorSettings()
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Window title and initial properties
        self.empty_project_win_title = "Nuke Code Editor (Beta): "  # Default title for an empty project
        self.setWindowTitle("Nuke Code Editor (Beta): Empty Project**")  # Title will change with Open and New projects
        self.setGeometry(100, 100, 1200, 800)

        # Center the window on the screen
        qr = self.frameGeometry()
        screen = QGuiApplication.primaryScreen()
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Variables for new project and file operations
        self.project_dir = None # Current project directory
        self.current_file_path = None  # Current file

        # Create and configure the status bar
        self.status_bar = self.statusBar()  # Status bar oluşturma
        self.status_bar.showMessage("Ready")  # İlk mesajı göster
        self.font_size_label = QLabel(f"Font Size: {self.settings.main_font_size} | ", self)
        self.status_bar.addPermanentWidget(self.font_size_label)
        self.status_bar = self.statusBar()

        # Add a label for replace operations on the right side
        self.replace_status_label = QLabel()
        self.status_bar.addPermanentWidget(self.replace_status_label)  # Add to the right corner
        self.replace_status_label.setText("Status")  # Initial message

        # Project settings paths and other configurations
        self.item_colors = {} # Dictionary to manage item-specific colors
        self.color_settings_path = os.path.join(os.getcwd(), "assets", "item_colors.json")
        self.settings_path = os.path.join(PathFromOS().settings_db, "settings.json")

        # Create a tabbed editor (Tab Widget)
        self.tab_widget = QTabWidget()
        self.python_icon = QIcon(os.path.join(PathFromOS().icons_path, 'python_tab.svg'))
        self.tab_widget.setIconSize(QSize(15, 15))

        # Close button and icon settings
        self.close_icon = os.path.join(PathFromOS().icons_path, 'new_file.png')  # Ensure the path is correct
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                
            }}

            QTabBar::tab {{
                background-color: #2B2B2B;
                color: #B0B0B0;
                padding: 5px 10px;
                border: none;
                font-size: 10pt;
                min-width: 150px;  /* Genişlik ayarı */
                min-height: 15px;  /* Yükseklik ayarı */
            }}

            QTabBar::tab:selected {{
                background-color: #3C3C3C;
                color: #FFFFFF;
                border-bottom: 2px solid #3C88E3;
            }}
            
            QTabBar::tab:!selected {{
                background-color: #323232;
            }}
            QTabBar::tab:hover {{
                background-color: #3C3C3C;
                color: #E0E0E0;
            }}
            
        """)

        self.tab_widget.setTabsClosable(True)

        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.ensure_tab)
        self.setCentralWidget(self.tab_widget)

        # Create the top menu
        self.create_menu()

        # Dockable lists
        self.create_docks()

        # Open a blank "untitled.py" tab at startup
        self.add_new_tab("untitled.py", initial_content= CodeEditorSettings().temp_codes)

        # Load colors at startup
        self.load_colors_from_file()

        # Recent projects are stored as a JSON list
        self.recent_projects_list = []
        # self.recent_projects_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "./",  "assets", "recent_projects.json")
        self.recent_projects_path = os.path.join(PathFromOS().json_path, "recent_projects.json")
        # Load colors and recent projects
        self.load_recent_projects()
        self.load_last_project()
        self.create_bottom_tabs() # Conolse / Output Widgets
        # Define Ctrl+Enter shortcut and bind to the run_code function
        run_shortcut = QShortcut(QKeySequence("Ctrl+Enter"), self)
        run_shortcut.activated.connect(self.run_code)
        # Ctrl + Shift + R kısayolunu replace_selected_word ile bağla
        self.replace_shortcut = QShortcut(QKeySequence("Ctrl+Shift+R"), self)
        self.replace_shortcut.activated.connect(self.open_replace_dialog)

    def keyPressEvent(self, event):
        """
        Captures key press events and handles specific shortcuts.

        Args:
            event (QKeyEvent): The key event triggered by the user.
        """
        if event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.run_code()
        else:
            super().keyPressEvent(event)
        super().keyPressEvent(event)

    def mark_as_modified(self, dock, file_path):
        """
        Marks a file as modified by appending '*' to the title.

        Args:
            dock (QDockWidget): The dock widget containing the file.
            file_path (str): Path to the file being modified.
        """
        if dock.windowTitle()[-1] != '*':
            dock.setWindowTitle(f"{os.path.basename(file_path)}*")

    def create_bottom_tabs(self):
        """
        Creates and configures bottom dock widgets for Output, Console, and NukeAI.
        """

        # Output Dock Widget
        self.output_dock = QDockWidget("OUTPUT", self)
        self.output_widget = OutputWidget()
        title_font = QFont("JetBrains Mono", 10)
        self.output_widget.setFont(title_font)
        self.output_widget.setReadOnly(True)
        self.output_dock.setWidget(self.output_widget)
        self.output_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.output_dock.setFloating(False)
        output_icon = QIcon(os.path.join(PathFromOS().icons_path, "play_orange.svg"))
        self.set_custom_dock_title(self.output_dock, "OUTPUT", output_icon)
        self.addDockWidget(self.settings.OUTPUT_DOCK_POS, self.output_dock)
        self.output_dock.setVisible(self.settings.OUTPUT_VISIBLE)

        # Console Dock Widget
        self.console_dock = QDockWidget("CONSOLE", self)
        self.console_widget = ConsoleWidget()
        self.console_dock.setWidget(self.console_widget)
        self.console_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.console_dock.setFloating(False)

        # Console Dock Widget Style and Icon Addition
        console_icon = QIcon(os.path.join(PathFromOS().icons_path, "python_tab.svg"))
        self.set_custom_dock_title(self.console_dock, "CONSOLE", console_icon)
        self.addDockWidget(self.settings.CONSOLE_DOCK_POS, self.console_dock)
        self.console_dock.setVisible(self.settings.CONSOLE_VISIBLE)

        # NukeAI Dock Widget
        self.nuke_ai_dock = QDockWidget("NUKEAI", self)
        self.nuke_ai_widget = QWidget()
        nuke_ai_layout = QVBoxLayout(self.nuke_ai_widget)

        # NukeAI Response Panel (Top Section)
        self.ai_response = QTextEdit()
        self.ai_response.setReadOnly(True)
        self.ai_response.setFont(title_font)
        self.ai_response.setStyleSheet("border: none;")  # Çerçevesiz yapıyoruz
        nuke_ai_layout.addWidget(self.ai_response)

        # NukeAI Input and Button (Bottom Section Side-by-Side)
        input_layout = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Komutunuzu buraya girin (örneğin: Blur nodu oluştur)")
        self.ai_input.setStyleSheet("border: none;")  # Çerçevesiz yapıyoruz
        input_layout.addWidget(self.ai_input)

        self.ai_button = QPushButton("Send")
        self.ai_button.setFlat(True)
        self.ai_button.setStyleSheet("""
            QPushButton {
                color: #FFA500;
                padding: 6px 12px;
                font-weight: bold;
            }
        """)
        self.ai_button.clicked.connect(self.process_ai_request)
        input_layout.addWidget(self.ai_button)

        nuke_ai_layout.addLayout(input_layout)
        self.nuke_ai_dock.setWidget(self.nuke_ai_widget)
        self.nuke_ai_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        nuke_ai_icon = QIcon(os.path.join(PathFromOS().icons_path, "ai_icon.svg"))
        self.set_custom_dock_title(self.nuke_ai_dock, "NUKEAI", nuke_ai_icon)
        self.addDockWidget(self.settings.NUKEAI_DOCK_POS, self.nuke_ai_dock)
        self.nuke_ai_dock.setVisible(self.settings.NUKEAI_VISIBLE)

        # Dockları alt kısımda sekmeli bir yapı ile gruplandırın
        self.tabifyDockWidget(self.output_dock, self.console_dock)
        self.tabifyDockWidget(self.output_dock, self.nuke_ai_dock)
        self.output_dock.raise_()  # Output sekmesini öne alıyoruz

    def process_ai_request(self):
        """
        Processes the user's command or prompt entered in the NukeAI input panel.

        This function is responsible for:
        - Retrieving the user input from the text field.
        - Generating a placeholder response to simulate AI processing.
        - Displaying the response in the NukeAI response panel.
        - Clearing the input field after processing.

        Steps:
        1. Get the input text from the `QLineEdit`.
        2. Generate a formatted response string as feedback to the user.
        3. Update the response panel with the simulated response.
        4. Clear the input field to prepare for the next command.

        Example Usage:
        - User enters "Create Blur Node" in the input field.
        - Response: "AI Response: 'Create Blur Node' is being processed."

        """
        # Retrieve the user input from the text field
        prompt = self.ai_input.text()

        # Simulate a response for the input
        response = f"AI Response: '{prompt}' is being processed."

        # Display the response in the NukeAI response panel
        self.ai_response.setText(response)

        # Clear the input field
        self.ai_input.clear()

    def set_custom_dock_title(self, dock_widget, title, icon):
        """
        Sets a custom style and icon for the title bar of a dock widget.
        This function customizes the appearance of the dock widget's title bar by:
        - Replacing the default title bar with a QWidget.
        - Adding an icon and a title label to the title bar.
        - Applying specific font styles to the title.
        - Aligning the content to the left while adding stretchable space for better layout.

        Parameters:
        - dock_widget (QDockWidget): The dock widget whose title bar is being customized.
        - title (str): The text to display in the title bar.
        - icon (QIcon): The icon to display next to the title.
        """
        # Create a custom title bar widget
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)  # Remove inner margins
        title_layout.setAlignment(Qt.AlignLeft)  # Align content to the left

        # Add the icon
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(16, 16))  # Set the icon size to 16x16
        title_layout.addWidget(icon_label)

        # Add the title text
        title_label = QLabel(title.upper())  # Convert the title text to uppercase
        title_font = QFont("Arial", 10)
        title_font.setBold(True)  # Make the font bold
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)

        # Add stretchable space to align the content properly
        title_layout.addStretch()

        # Set the custom title bar widget for the dock widget
        dock_widget.setTitleBarWidget(title_bar)

    def clear_output(self):
        """
        Clears all content from the output panel.

        This resets the display area of the output widget, removing any text or messages.
        """
        self.output_widget.clear()  # Clear the output panel

    def run_code(self):
        """
        Executes the code in the current active tab and displays the results or errors in the output panel.

        - Clears the output panel before execution.
        - Displays environment info like Python version, Nuke version, computer name, and timestamp.
        - Executes the selected or full content of the active editor tab.
        - Handles both Python and Nuke-specific code execution.
        - Outputs success or error messages back to the output panel.
        """
        # Clear the Output Widget
        self.output_widget.clear()

        from datetime import datetime

        python_version = platform.python_version()  # Get Python version
        nuke_version = nuke.env['NukeVersionString']  # Get Nuke version
        computer_name = socket.gethostname()  # Get the computer name

        # Get the current date and time
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Get the name of the active tab
        active_tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())

        # Display system and environment info in the output
        info_message = (
            f'<span style="color: grey;">'
            f'Python: {python_version} | Nuke: {nuke_version} | Active File: {active_tab_name} | Computer: {computer_name} | {formatted_time}'
            f'</span>'
        )
        self.output_widget.append(info_message)

        # Execute the code from the active editor
        current_editor = self.tab_widget.currentWidget()

        if isinstance(current_editor, QPlainTextEdit):
            cursor = current_editor.textCursor()
            code = cursor.selectedText().strip() or current_editor.toPlainText()
            try:
                if "nuke." in code:
                    # Execute Nuke-specific code
                    execute_nuke_code(code, self.output_widget)
                else:
                    # Execute standard Python code
                    execute_python_code(code, self.output_widget)

                # Add a success message
                success_message = '<span style="color: grey;">...End of the line</span>'
                self.output_widget.append(success_message)

            except Exception as e:
                # Handle and display errors
                error_message = traceback.format_exc()
                user_friendly_message = f"<b style='color: red;'>Problem encountered while running: {str(e)}</b>"
                self.output_widget.append_error_output(user_friendly_message)
                self.output_widget.append_error_output(error_message)

    def update_toolbar_spacer(self, orientation: Qt.Orientation, spacer: QWidget):
        """
        Adjusts the spacer's size policy based on the toolbar's orientation.

        Args:
            orientation (Qt.Orientation): The current orientation of the toolbar (Qt.Horizontal or Qt.Vertical).
            spacer (QWidget): The spacer widget to be adjusted.

        Behavior:
            - Expands width if the toolbar is horizontal.
            - Expands height if the toolbar is vertical.
        """
        if orientation == Qt.Horizontal:
            # Expand width for horizontal orientation
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            # Expand height for vertical orientation
            spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def show_search_dialog(self):
        """
        Opens a modal search dialog and allows the user to search within the current document.

        Behavior:
            - Instantiates the `SearchDialog` with the main window as its parent.
            - Displays the dialog in a modal state to block interaction with other windows until closed.
        """
        dialog = SearchDialog(self)  # Pass the main window reference
        dialog.exec_()  # Open the dialog modally

    def find_and_highlight(self, search_term):
        """
        Highlights occurrences of a given search term in the active code editor.

        Args:
            search_term (str): The term to search and highlight in the editor.

        Behavior:
            - Searches for all occurrences of the `search_term` in the current editor.
            - Applies a yellow background to highlight matching terms.
            - If no editor is open, displays an error message in the output widget.
        """
        current_editor = self.tab_widget.currentWidget()
        if current_editor is None:
            self.output_widget.append_error_output("Please open an active tab for coding...")
            return

        cursor = current_editor.textCursor()  # Get the editor's cursor
        document = current_editor.document()  # Get the text document

        # Clear existing highlights
        current_editor.setExtraSelections([])

        # Store results for highlighting
        extra_selections = []

        # Begin bulk changes to the cursor
        cursor.beginEditBlock()

        # Move cursor to the start of the document
        cursor.movePosition(QTextCursor.Start)

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))  # Set highlight color to yellow

        # Search for all matches of the term
        while not cursor.isNull() and not cursor.atEnd():
            cursor = document.find(search_term, cursor)
            if not cursor.isNull():
                # Create a selection for the found term
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = highlight_format
                extra_selections.append(selection)

        # End bulk changes
        cursor.endEditBlock()

        # Apply highlights to the editor
        current_editor.setExtraSelections(extra_selections)

    def populate_outliner_with_functions(self):
        """
        Populates the OUTLINER with classes and functions from specific files,
        excluding the headers from `nuke.py` and `nukescripts.py`.

        Behavior:
            - Reads class and function definitions from the `nuke.py` and `nukescripts.py` files.
            - Adds these definitions to the OUTLINER view.
        Steps:
            1. Load file paths from `PathFromOS`.
            2. Parse the files to extract class and function definitions.
            3. Add the parsed definitions to the OUTLINER view.
        Dependencies:
            - PathFromOS(): Provides paths to `nuke.py` and `nukescripts.py`.
            - `list_classes_from_file`: Parses files for classes and functions.
            - `add_classes_and_functions_to_tree`: Adds definitions to the OUTLINER tree.
        """
        # Define paths to the Nuke and Nukescripts files
        nuke_file_path = PathFromOS().nuke_ref_path
        nukescripts_file_path = PathFromOS().nukescripts_ref_path

        # Extract classes and functions from the files
        nuke_classes = self.list_classes_from_file(nuke_file_path)
        nukescripts_classes = self.list_classes_from_file(nukescripts_file_path)

        # Add parsed definitions directly to the OUTLINER
        self.add_classes_and_functions_to_tree(nuke_classes)
        self.add_classes_and_functions_to_tree(nukescripts_classes)

    def add_nuke_functions_to_outliner(self, nuke_functions):
        """
        Adds Nuke-specific functions to the existing OUTLINER without altering other entries.
        Parameters:
            nuke_functions (list of dict): A list of dictionaries where each dictionary represents a function
            with a key `name` for the function name.
        Behavior:
            - Searches for an existing "Nuke Functions" category in the OUTLINER.
            - If not found, creates a new "Nuke Functions" parent category.
            - Adds each function as a child under "Nuke Functions" with a specific icon.
            - Ensures only "Nuke Functions" items are expanded for better visibility.
        Steps:
            1. Search for "Nuke Functions" in the OUTLINER.
            2. Create the category if it does not exist.
            3. Append each function as a child of "Nuke Functions".
            4. Expand only the "Nuke Functions" category for better organization.
        """
        if nuke_functions:
            # Search for "Nuke Functions" header in OUTLINER
            parent_item = None
            for i in range(self.outliner_list.topLevelItemCount()):
                item = self.outliner_list.topLevelItem(i)
                if item.text(0) == "Nuke Functions":
                    parent_item = item
                    break

            if not parent_item:
                # Create "Nuke Functions" header if not present
                parent_item = QTreeWidgetItem(self.outliner_list)
                parent_item.setText(0, "Nuke Functions")
                parent_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'folder_tree.svg')))  # Folder Icon

            # Add each function under "Nuke Functions"
            for func in nuke_functions:
                func_item = QTreeWidgetItem(parent_item)
                func_item.setText(0, func["name"])  # Extract function name
                func_item.setIcon(0, QIcon(
                    os.path.join(PathFromOS().icons_path, 'M_red.svg')))  # Set the function icon

            # Expand only the "Nuke Functions" category
            self.outliner_list.expandItem(parent_item)

    def add_classes_and_functions_to_tree(self, classes):
        """
        Adds classes and their methods directly to the OUTLINER.
        Parameters:
            classes (list of tuples): A list where each tuple contains:
                - class_name (str): The name of the class.
                - methods (list of str): A list of method names belonging to the class.
        Behavior:
            - Each class is added as a top-level item in the OUTLINER.
            - Each method of a class is added as a child of the corresponding class item.
            - Icons are assigned to both classes and methods for better visual representation.
            - All items in the OUTLINER are expanded for visibility.
        Steps:
            1. Loop through the provided list of classes.
            2. Add each class as a top-level item with an associated class icon.
            3. For each class, add its methods as child items with an associated method icon.
            4. Expand all items in the OUTLINER for improved visibility.
        """
        for class_name, methods in classes:
            # Add class to OUTLINER
            class_item = QTreeWidgetItem(self.outliner_list)
            class_item.setText(0, class_name)
            class_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'C_logo.svg')))  # Assign class icon

            # Add methods for the class
            for method in methods:
                method_item = QTreeWidgetItem(class_item)
                method_item.setText(0, method)
                method_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'M_logo.svg')))  # Assign method icon

        # Expand all items in the OUTLINER for better visibility
        self.outliner_list.expandAll()

    # DEVAM EDECEK
    def list_classes_from_file(self, file_path):
        """Verilen dosyadaki sınıfları ve metotları bulur, özel metotları filtreler."""
        if not os.path.exists(file_path):
            print(f"Error: {file_path} dosyası bulunamadı!")
            return []

        # Dosya içeriğini okuyor ve AST'ye dönüştürüyoruz
        with open(file_path, 'r') as file:
            file_content = file.read()
        tree = ast.parse(file_content)
        classes = []

        # AST üzerinde gezinerek sınıf ve metodları buluyoruz
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                # Sınıf içinde, __init__ gibi özel metodları filtreliyoruz
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('__')]
                classes.append((class_name, methods))

        return classes

    def create_menu(self):
        """Genişletilmiş ve yeniden düzenlenmiş menü çubuğunu oluşturur."""
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { padding: 4px 4px; font-size: 8pt; }")  # Menü çubuğu boyutu

        # 1. File Menüsü
        file_menu = menubar.addMenu('File')
        self.new_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'new_project.png')),
                                          'New Project', self)
        self.new_project_action.setShortcut(QKeySequence("Ctrl+N"))

        # New Project alt menüleri (Nuke ve Custom projeler)
        new_project_menu = QMenu('New Project', self)
        nuke_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'nuke_project.png')),
                                      'Nuke Project (.nuke)', self)
        custom_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'custom_project.png')),
                                        'Custom Project', self)

        custom_project_action.triggered.connect(self.new_project_dialog)
        nuke_project_action.triggered.connect(self.open_nuke_project_dialog)
        new_project_menu.addAction(nuke_project_action)
        new_project_menu.addAction(custom_project_action)

        # File menüsü diğer aksiyonlar
        open_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'open_project.png')), 'Open Project',
                                      self)
        new_file_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'new_file.png')), 'New File', self)
        new_file_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        open_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'open.png')), 'Open File', self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), 'Save', self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_as_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save_as.png')), 'Save As', self)
        exit_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'exit.png')), 'Exit', self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))

        # Preferences öğesi
        preferences_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'settings.png')), 'Preferences', self)

        # File menüsüne eklemeler
        file_menu.addMenu(new_project_menu)
        file_menu.addAction(open_project_action)
        file_menu.addSeparator()
        file_menu.addAction(new_file_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(preferences_action)
        file_menu.addSeparator()
        self.recent_projects = file_menu.addMenu('Recent Projects')
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # 2. Edit Menüsü
        edit_menu = menubar.addMenu('Edit')
        undo_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'undo.png')), 'Undo', self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        redo_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'redo.png')), 'Redo', self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))

        # Go To Line öğesi
        go_to_line_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'goto_line.png')), 'Go To Line', self)
        go_to_line_action.setShortcut(QKeySequence("Ctrl+G"))

        find_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), 'Find', self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        replace_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'replace.png')), 'Replace', self)
        clear_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'clear.svg')), 'Clear Output', self)

        cut_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'cut.png')), 'Cut', self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        copy_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'copy.png')), 'Copy', self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        paste_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'paste.png')), 'Paste', self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))

        # Edit menüsüne eklemeler
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(go_to_line_action)  # Go To Line eklenmesi
        edit_menu.addAction(find_action)
        edit_menu.addAction(replace_action)
        edit_menu.addSeparator()
        edit_menu.addAction(clear_action)

        # 3. View Menüsü
        view_menu = menubar.addMenu('View')

        # Zoom işlemleri
        zoom_in_action = QAction('Zoom In', self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_out_action = QAction('Zoom Out', self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        reset_zoom_action = QAction('Reset Zoom', self)  # Reset Zoom eklendi

        # View menüsüne eklemeler
        view_menu.addAction(zoom_in_action)
        view_menu.addAction(zoom_out_action)
        view_menu.addAction(reset_zoom_action)  # Reset Zoom menüye eklendi
        view_menu.addSeparator()

        # Reset ve Varsayılan UI aksiyonları
        reset_ui_action = QAction('Reset UI', self)
        set_default_ui_action = QAction('Set Default UI', self)
        view_menu.addAction(reset_ui_action)
        view_menu.addAction(set_default_ui_action)

        # Zoom işlevlerini bağlama
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_out_action.triggered.connect(self.zoom_out)
        reset_zoom_action.triggered.connect(self.reset_zoom)  # Reset Zoom işlevine bağlama

        # 4. Run Menüsü
        run_menu = menubar.addMenu('Run')
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), 'Run Current Code', self)
        run_action.setShortcut(QKeySequence("F5"))
        stop_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'stop.png')), 'Stop Execution', self)
        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

        # 5. Tools Menüsü
        tools_menu = menubar.addMenu('Tools')
        live_connection_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'pycharm.png')), 'LCV PyCharm', self)
        live_connection_action.setEnabled(False)

        # GitHub alt menüsü
        github_menu = tools_menu.addMenu(QIcon(os.path.join(PathFromOS().icons_path, 'github.svg')), 'GitHub')
        git_commit_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'commit.png')), 'Commit', self)
        git_push_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'push.png')), 'Push', self)
        git_pull_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'pull.png')), 'Pull', self)
        git_status_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'status.png')), 'Status', self)

        github_menu.addAction(git_commit_action)
        github_menu.addAction(git_push_action)
        github_menu.addAction(git_pull_action)
        github_menu.addAction(git_status_action)

        # Menü eylemleri için fonksiyon bağlama
        git_commit_action.triggered.connect(lambda: commit_changes(self))
        git_push_action.triggered.connect(lambda: push_to_github(self))
        git_pull_action.triggered.connect(lambda: pull_from_github(self))
        git_status_action.triggered.connect(lambda: get_status(self))

        tools_menu.addAction(live_connection_action)

        # 6. Help Menüsü
        help_menu = menubar.addMenu('Help')
        documentation_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'documentation.png')),
                                       'Documentation', self)
        licence_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'licence.png')), 'Licence', self)
        about_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'about.png')), 'About', self)
        update_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'update.png')), 'Update', self)

        help_menu.addAction(documentation_action)
        help_menu.addAction(licence_action)
        help_menu.addAction(about_action)
        help_menu.addSeparator()
        help_menu.addAction(update_action)

        # İşlevleri Fonksiyonlara Bağlama
        self.new_project_action.triggered.connect(self.new_project_dialog)
        self.new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        new_file_action.triggered.connect(self.create_new_file_dialog)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        exit_action.triggered.connect(self.file_exit)
        find_action.triggered.connect(self.show_search_dialog)
        replace_action.triggered.connect(self.trigger_replace_in_active_editor)
        cut_action.triggered.connect(self.cut_text)
        copy_action.triggered.connect(self.copy_text)
        paste_action.triggered.connect(self.paste_text)
        stop_action.triggered.connect(self.stop_code)
        reset_ui_action.triggered.connect(self.reset_ui)
        set_default_ui_action.triggered.connect(self.set_default_ui)
        preferences_action.triggered.connect(self.open_settings)

        # Go To Line işlevini bağlama
        go_to_line_action.triggered.connect(self.show_go_to_line_dialog)

    def zoom_in(self):
        """Yazı boyutunu büyütür."""
        self.settings.main_font_size += 1
        self.apply_font_size()

    def zoom_out(self):
        """YDecreases the font size."""
        if self.settings.main_font_size > 1:  # En küçük yazı boyutu kontrolü
            self.settings.main_font_size -= 1
        self.apply_font_size()

    def reset_zoom(self):
        """Yazı boyutunu varsayılan değere sıfırlar."""
        self.settings.main_font_size = 11  # Varsayılan font boyutunu ayarla
        self.apply_font_size()

    def apply_font_size(self):
        """Kod editöründeki yazı boyutunu günceller ve status barda gösterir."""
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor):
                font = editor.font()
                font.setPointSize(self.settings.main_font_size)
                editor.setFont(font)

        # Durum çubuğundaki yazı boyutu bilgisini güncelle
        self.font_size_label.setText(f"Font Size: {self.settings.main_font_size}")

    def show_go_to_line_dialog(self):
        """Go To Line diyalogunu gösterir."""
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            dialog = GoToLineDialog(current_editor)
            dialog.exec_()

    def stop_code(self):
        # Kodun çalışmasını durdurmak için işlemleri buraya yazın
        print("Execution stopped FUNC.")

    def open_settings(self):
        """Preferences menüsüne tıklanınca settings_ui.py'yi açar."""
        try:
            import settings.settings_ui
            settings.settings_ui.launch_settings()
        except Exception as e:
            print(f"Error while opening settings UI: {e}")

    def new_project_dialog(self):
        self.allowed_pattern = r'^[a-zA-Z0-9_ ]+$'
        """Yeni proje oluşturmak için diyalog kutusu."""
        bg_image_path = os.path.join(PathFromOS().icons_path, 'nuke_logo_bg_01.png')
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        new_project_dialog_size = QSize(500, 300)  # Yüksekliği artırıldı
        dialog.resize(new_project_dialog_size)

        # Gölge efekti
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(40)
        shadow_effect.setOffset(0, 12)  # Gölge aşağı kaydırıldı
        shadow_effect.setColor(QColor(0, 0, 0, 100))
        dialog.setGraphicsEffect(shadow_effect)

        # Ana layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Arka plan çerçevesi
        background_frame = QFrame(dialog)
        background_frame.setStyleSheet("""
            QFrame {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 9px;
            }
        """)

        # İçerik yerleşimi
        inner_layout = QVBoxLayout(background_frame)
        inner_layout.setContentsMargins(30, 30, 30, 20)
        layout.addWidget(background_frame)

        # İmajı yükle ve yuvarlak köşeli bir pixmap oluştur
        pixmap = QPixmap(bg_image_path)
        rounded_pixmap = QPixmap(pixmap.size())
        rounded_pixmap.fill(Qt.transparent)

        # Yuvarlak köşe maskesi uygulama
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, pixmap.width(), pixmap.height()), 9, 9)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        # Yuvarlatılmış pixmap'i image_label içinde göster
        image_label = QLabel(background_frame)
        image_label.setPixmap(rounded_pixmap)
        image_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        image_label.setFixedSize(dialog.size())

        # Başlık
        title_label = QLabel("Create New Project", background_frame)
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setStyleSheet("""
            color: #CFCFCF;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Myriad';
            border: none;
            background-color: transparent;
        """)
        inner_layout.addWidget(title_label)

        # Başlık altındaki boşluk
        inner_layout.addSpacing(20)

        # Proje ismi giriş alanı
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter Project Name")
        self.project_name_input.setMaxLength(20)  # Maksimum 20 karakter
        self.project_name_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E0E0E0;
                padding: 10px;
                padding-right: 40px;  /* Sağ tarafta karakter sayacı için boşluk */
                border: 1px solid #5A5A5A;
                border-radius: 8px;
            }
        """)
        inner_layout.addWidget(self.project_name_input)

        # Giriş doğrulama işlevi
        def validate_project_name():
            # İzin verilen karakterler

            if re.match(self.allowed_pattern, self.project_name_input.text()) and self.project_name_input.text() != "":
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_name_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        padding-right: 40px;
                        border: 1px solid #5A5A5A;
                        border-radius: 8px;
                    }
                """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçersiz giriş olduğunda kırmızı çerçeve
                self.project_name_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 100, 100, 0.08);
                        color: #ff9991;
                        padding: 10px;
                        padding-right: 40px;
                        border: 1px solid red;
                        border-radius: 8px;
                    }
                """)
                self.project_desc.setText("Incorrect file name!")

        self.project_name_input.textChanged.connect(validate_project_name)

        # Character counter
        char_count_label = QLabel("0/20", self.project_name_input)
        if self.project_name_input.text() == "":
            char_count_label.setText("")
        char_count_label.setStyleSheet("""
            color: rgba(160, 160, 160, 0.6);  /* %60 opaklık */
            font-size: 12px;
            border: none;
            background: transparent;
        """)
        char_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        char_count_label.setFixedSize(60, 30)

        # Function that updates character counter
        def update_char_count():
            current_length = str(len(self.project_name_input.text()))
            current_length_count = current_length + "/20"

            char_count_label.setText(current_length_count)
            char_count_label.move(self.project_name_input.width() - 75,
                                  (self.project_name_input.height() - char_count_label.height()) // 2)

        # Counter update with `textChanged` signal
        self.project_name_input.textChanged.connect(update_char_count)

        # QLineEdit'ler arasında ve title ile boşluk bırak
        inner_layout.addSpacing(20)

        # Project directory entry field and "Browse" button
        self.project_dir_input = QLineEdit()
        self.project_dir_input.setPlaceholderText("Select Project Directory")
        self.project_dir_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E0E0E0;
                padding: 10px;  /* Orijinal kalınlık */
                border: 1px solid #5A5A5A;
                border-radius: 8px;
            }
        """)

        def validate_project_directory(): # Directory validation function
            if not self.project_dir_input.text():
                # Red frame if no directory is selected
                self.project_dir_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        border: 1px solid red;
                        border-radius: 8px;
                    }
                """)
            else:
                # Return to original style when valid input
                self.project_dir_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        border: 1px solid #5A5A5A;
                        border-radius: 8px;
                    }
                """)

        # Dir selection layout
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.project_dir_input)

        # Browse Button
        project_dir_button = QPushButton("Browse")
        project_dir_button.setFixedHeight(self.project_dir_input.sizeHint().height())  # QLineEdit ile aynı yükseklik
        project_dir_button.setStyleSheet("""
            QPushButton {
                background-color: #4E4E4E;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6E6E6E;
            }
        """)
        dir_layout.addWidget(project_dir_button)
        inner_layout.addLayout(dir_layout)

        # Information Buttons
        self.project_desc = QLabel("Please ensure the correct information!")
        self.project_desc.setStyleSheet("""
            color: #A0A0A0;
            font-size: 11px;
            border: none;
            text-align: left;
            margin-top: 10px;
        """)
        inner_layout.addWidget(self.project_desc)

        # OK / Cancel Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #808080; /* Gri renk */
                color: #FFFFFF;
                font-family: 'Myriad';
                border-radius: 10px;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #A9A9A9; /* Daha açık gri */
            }
        """)
        button_layout.addWidget(ok_button)

        # Cancel Button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(80, 30)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #808080; /* Gri renk */
                color: #FFFFFF;
                font-family: 'Myriad';
                border-radius: 10px;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #A9A9A9; /* Daha açık gri */
            }
        """)
        button_layout.addWidget(cancel_button)

        # Label ile butonlar arasında boşluk ekleyin
        inner_layout.addSpacing(20)  # Label ile buton grubu arasında boşluk
        inner_layout.addLayout(button_layout)

        # Proje dizini seçiminde "Browse" butonuna tıklama işlemi
        project_dir_button.clicked.connect(lambda: self.browse_directory(self.project_dir_input))

        # OK butonuna tıklandığında proje oluşturma işlemi
        ok_button.clicked.connect(
            lambda: self.create_new_project(self.project_name_input.text(), self.project_dir_input.text(), dialog))

        # Cancel butonuna tıklanınca dialogu kapatma işlemi
        cancel_button.clicked.connect(dialog.close)
        dialog.exec_()

    def create_new_project(self, project_name, project_directory, dialog):
        """Create a new project directory and set project_dir to the new path."""
        if not project_name.strip():
            if re.match(self.allowed_pattern, self.project_name_input.text()) and self.project_name_input.text() != "":
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_name_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 255, 255, 0.08);
                            color: #E0E0E0;
                            padding: 10px;
                            padding-right: 40px;
                            border: 1px solid #5A5A5A;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçersiz giriş olduğunda kırmızı çerçeve
                self.project_name_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 100, 100, 0.08);
                            color: #ff9991;
                            padding: 10px;
                            padding-right: 40px;
                            border: 1px solid red;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Incorrect file name!")
            return

        # Directory denetleme OK'a basıldığında
        if not project_directory.strip():
            if not self.project_dir_input.text():
                # Dizin seçilmezse kırmızı çerçeve
                self.project_dir_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 255, 255, 0.08);
                            color: #E0E0E0;
                            padding: 10px;
                            border: 1px solid red;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_dir_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 100, 100, 0.08);
                            color: #ff9991;
                            padding: 10px;
                            border: 1px solid #5A5A5A;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please set a directory!")
            return

        # Create the new project directory
        project_path = os.path.join(project_directory, project_name)

        if os.path.exists(project_path):
            self.project_desc.setText("Project directory already exists.")
            return
        else:
            os.makedirs(project_path)

        # Set self.project_dir to the newly created project directory
        self.project_dir = project_path
        self.populate_workplace(self.project_dir)
        self.setWindowTitle(self.empty_project_win_title + os.path.basename(self.project_dir))

        # Projeyi recent_projects_list'e ekleyelim
        self.add_to_recent_projects(self.project_dir)

        # Close the dialog
        dialog.close()

    def open_nuke_project_dialog(self):
    # Returns the workplace after generating a project specific to Nuke
        dialog = NewNukeProjectDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint) # Make dialog Z +1
        if dialog.exec_():
            project_name = dialog.project_name_input.text().strip()
            project_dir = dialog.project_dir_input.text().strip()
            self.project_dir = os.path.join(project_dir, project_name)
            if os.path.exists(self.project_dir):
                self.populate_workplace(self.project_dir)
                self.add_to_recent_projects(self.project_dir)
                print ("Created: ", self.project_dir)
            else:
                print ("NOT Created: ", self.project_dir)


    def reset_ui(self):
        """Resets the UI layout."""
        QMessageBox.information(self, "Reset UI", "UI has been reset.")

    def set_default_ui(self):
        """Sets the default UI layout."""
        QMessageBox.information(self, "Set Default UI", "UI has been set to default.")

    def cut_text(self):
        """Cuts the selected text from the active editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.cut()

    def copy_text(self):
        """Copies the selected text from the active editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.copy()

    def paste_text(self):
        """Pastes the text from the clipboard into the active editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.paste()

    def open_replace_dialog(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            # Seçili metni kontrol et
            if current_editor.textCursor().selectedText().strip():
                dialog = ReplaceDialogs(current_editor)
                dialog.show()
            else:
                # Eğer metin seçili değilse uyarı göster
                self.status_bar.showMessage("Please select the text you want to replace.", 5000)

    def trigger_replace_in_active_editor(self):
        # Mevcut aktif sekmedeki editor'ü alalım
        current_editor = self.tab_widget.currentWidget()

        # Eğer aktif düzenleyici bir CodeEditor ise ve metin seçiliyse ReplaceDialogs fonksiyonunu çağırıyoruz
        if isinstance(current_editor, CodeEditor):
            if current_editor.textCursor().selectedText().strip():
                dialog = ReplaceDialogs(current_editor)  # current_editor'ü parametre olarak geçiyoruz
                dialog.show()  # Diyaloğu gösteriyoruz
            else:
                # Eğer metin seçili değilse uyarı göster
                self.status_bar.showMessage("Please select the text you want to replace.", 5000)
        else:
            # Eğer geçerli düzenleyici CodeEditor değilse hata mesajı göster
            self.status_bar.showMessage("Please open an editor tab.", 5000)

    def update_recent_projects_menu(self):
        """Recent Projects menüsünü günceller."""
        self.recent_projects.clear()
        # Her proje için menüye bir eylem ekleyelim
        for project_path in self.recent_projects_list:
            action = QAction(project_path, self)
            # 'checked' argümanını ekleyin ve path'i lambda'ya gönderin
            action.triggered.connect(partial(self.open_project_from_path, project_path))
            self.recent_projects.addAction(action)

    def load_last_project(self):
        """recent_paths listesinin ilk elemanını settings.json'daki resume_last_project durumuna göre yükler."""
        # Settings.json kontrolü
        resume_last_project = False
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, 'r') as settings_file:
                    settings_data = json.load(settings_file)
                    resume_last_project = settings_data["General"].get("resume_last_project", False)
            except Exception as e:
                print(f"Error reading settings.json: {e}")
        # Eğer settings.json'daki resume_last_project false ise işlem yapma
        if not resume_last_project:
            print("Resume last project is disabled in settings.json.!!")
            return
        # Recent projects.json kontrolü
        if os.path.exists(self.recent_projects_path):
            try:
                with open(self.recent_projects_path, 'r') as file:
                    data = json.load(file)
                    recent_paths = data.get("recent_paths", [])

                    # recent_paths'in ilk elemanını kontrol et ve yükle
                    if recent_paths:
                        last_project = recent_paths[0]
                        if os.path.exists(last_project):
                            self.project_dir = last_project
                            self.populate_workplace(self.project_dir)
                            self.setWindowTitle(self.empty_project_win_title + os.path.basename(self.project_dir))
                            print(f"Last project loaded: {last_project}")
                        else:
                            print(f"Last project path does not exist: {last_project}")
                    else:
                        print("No recent projects found in recent_projects.json.")
            except Exception as e:
                print(f"Error loading recent projects: {e}")
        else:
            print("recent_projects.json does not exist.")

    def open_project_from_path(self, project_path):
        """
        Opens a project from the given file path, updates the recent projects list,
        and dynamically refreshes the menu.
        """
        if os.path.exists(project_path):
            # Proje yolunu aç
            self.project_dir = project_path
            self.populate_workplace(project_path)
            self.setWindowTitle(self.empty_project_win_title + os.path.basename(project_path))

            # Recent Projects listesine güncel projeyi ekle
            if project_path in self.recent_projects_list:
                self.recent_projects_list.remove(project_path)  # Zaten varsa kaldır
            self.recent_projects_list.insert(0, project_path)  # En üste ekle

            # Güncellenen listeyi recent_projects.json'a kaydet
            try:
                with open(self.recent_projects_path, 'w') as file:
                    json.dump({"recent_paths": self.recent_projects_list}, file, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error updating recent projects file: {e}")

            # Menüdeki Recent Projects listesini dinamik olarak güncelle
            self.update_recent_projects_menu()
        else:
            QMessageBox.warning(self, "Error", f"Project directory {project_path} does not exist.")

    def new_project(self):
        """Yeni bir proje dizini seçer ve doğrudan dosya sistemine yansıtır."""
        # self.project_dir = QFileDialog.getExistingDirectory(self, "Proje Dizini Seç")
        if self.project_dir:
            self.populate_workplace(self.project_dir)

    def populate_workplace(self, directory):
        """Workplace'ı proje dizini ile doldurur."""
        self.workplace_tree.clear()  # Önceki dizini temizle
        root_item = QTreeWidgetItem(self.workplace_tree)
        root_item.setText(0, os.path.basename(directory))
        self.add_items_to_tree(root_item, directory)
        self.workplace_tree.expandAll()

    def add_items_to_tree(self, parent_item, directory):
        """Belirli uzantılara sahip dosyaları tree'ye ekler."""
        # İzin verilen uzantılar
        allowed_extensions = {'.py', '.txt', '.sh', '.cpp', '.png', '.jpg', '.jpeg'}

        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)

            # Eğer bir klasörse, içine girip tekrar `add_items_to_tree` çağır
            if os.path.isdir(file_path):
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, file_name)
                folder_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'folder_tree.svg')))
                self.add_items_to_tree(folder_item, file_path)
            else:
                # Dosya uzantısını kontrol et ve sadece izin verilenleri ekle
                _, extension = os.path.splitext(file_name)
                if extension.lower() in allowed_extensions:
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, file_name)
                    file_item.setData(0, Qt.UserRole, file_path)  # Sağ tık menüsü için yol bilgisi ekle

                    # Dosya tipine göre ikon ekle
                    if extension.lower() == '.py':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'python_tab.svg')))
                    elif extension.lower() == '.txt':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'text_icon.svg')))
                    elif extension.lower() == '.sh':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'shell_icon.svg')))
                    elif extension.lower() == '.cpp':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'cpp_icon.svg')))
                    elif extension.lower() in {'.png', '.jpg', '.jpeg'}:
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'image_icon.svg')))

    def on_workplace_item_double_clicked(self, item, column):
        """Workplace'deki bir dosya çift tıklanınca dosyayı aç."""
        file_path = item.data(0, Qt.UserRole)

        if file_path and file_path.endswith(".py"):
            # Öncelikle aynı dosya yoluna sahip bir sekmenin açık olup olmadığını kontrol edelim
            for index in range(self.tab_widget.count()):
                existing_editor = self.tab_widget.widget(index)
                if self.tab_widget.tabText(index) == os.path.basename(file_path):
                    # Eğer aynı isimde bir sekme açıksa, mevcut sekmeyi öne getir
                    self.tab_widget.setCurrentWidget(existing_editor)
                    return  # Yeni bir sekme açılmasını engelle ve çık

            # Aynı dosya açık değilse yeni bir sekme aç
            self.add_new_tab(file_path)

    def context_menu(self, position):
        """Sağ tıklama menüsünü oluştur."""
        menu = QMenu()
        if self.workplace_tree.topLevelItemCount() == 0:
            return None
        # 1. Explore file
        explore_file_action = QAction('Explore file', self)
        explore_file_action.triggered.connect(lambda: self.explore_file(self.workplace_tree.itemAt(position)))
        menu.addAction(explore_file_action)

        # 2. Open file
        open_file_action = QAction('Open file', self)
        open_file_action.triggered.connect(lambda: self.open_file_item(self.workplace_tree.itemAt(position)))
        menu.addAction(open_file_action)

        # 3. Set Color
        set_color_action = QAction('Set Color', self)
        set_color_action.triggered.connect(lambda: self.set_item_color(self.workplace_tree.itemAt(position)))
        menu.addAction(set_color_action)

        # Ayraç
        menu.addSeparator()

        # 4. Copy
        copy_action = QAction('Copy', self)
        copy_action.triggered.connect(lambda: self.copy_item(self.workplace_tree.itemAt(position)))
        menu.addAction(copy_action)

        # 5. Paste
        paste_action = QAction('Paste', self)

        paste_action.triggered.connect(self.paste_item)
        menu.addAction(paste_action)

        # 6. Delete file
        delete_file_action = QAction('Delete file', self)
        delete_file_action.triggered.connect(lambda: self.delete_file_item(self.workplace_tree.itemAt(position)))
        menu.addAction(delete_file_action)

        # Ayraç
        menu.addSeparator()

        # Expand All
        expand_all_action = QAction('Expand All', self)
        expand_all_action.triggered.connect(self.expand_all_items)
        menu.addAction(expand_all_action)

        # Collapse All
        collapse_all_action = QAction('Collapse All', self)
        collapse_all_action.triggered.connect(self.collapse_all_items)
        menu.addAction(collapse_all_action)

        menu.exec_(self.workplace_tree.viewport().mapToGlobal(position))

    def expand_all_items(self):
        """Expands all items in Workplace."""
        self.workplace_tree.expandAll()

    def collapse_all_items(self):
        """Collapses all items in Workplace."""
        self.workplace_tree.collapseAll()

    def explore_file(self, item):
        # We get Qt.UserRole data from item
        file_path = item.data(0, Qt.UserRole)

        # check if file_path is valid
        if file_path and os.path.exists(file_path):
            os.startfile(os.path.dirname(file_path))
        else:
            QMessageBox.warning(self, "Hata", "Please select sub dir or file.")

    def open_file_item(self, item):
        file_path = item.data(0, Qt.UserRole)

        if file_path and os.path.exists(file_path):
            # Öncelikle aynı dosya yoluna sahip bir sekmenin açık olup olmadığını kontrol edelim
            for index in range(self.tab_widget.count()):
                existing_editor = self.tab_widget.widget(index)
                if self.tab_widget.tabText(index) == os.path.basename(file_path):
                    # Eğer aynı isimde bir sekme açıksa, mevcut sekmeyi öne getir
                    self.tab_widget.setCurrentWidget(existing_editor)
                    return  # Yeni bir sekme açılmasını engelle ve çık

            # Aynı dosya açık değilse yeni bir sekme aç
            self.add_new_tab(file_path)
        else:
            QMessageBox.warning(self, "Hata", "Dosya mevcut değil.")

    def copy_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
        else:
            QMessageBox.warning(self, "Hata", "Kopyalanacak dosya mevcut değil.")

    def paste_item(self):
        clipboard = QApplication.clipboard()
        file_path = clipboard.text()
        if os.path.exists(file_path):
            dest_dir = self.project_dir  # Yapıştırma dizinini burada belirtin
            dest_file = os.path.join(dest_dir, os.path.basename(file_path))
            try:
                shutil.copy(file_path, dest_file)
                self.populate_workplace(self.project_dir)  # Yüklemeyi yenile
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Dosya yapıştırılamadı: {str(e)}")
        else:
            QMessageBox.warning(self, "Hata", "Yapıştırılacak dosya mevcut değil.")

    def delete_file_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            confirm = QMessageBox.question(self, "Sil", f"Dosya '{os.path.basename(file_path)}' silinsin mi?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    os.remove(file_path)
                    self.populate_workplace(self.project_dir)  # Workspace'i güncelle
                except Exception as e:
                    QMessageBox.warning(self, "Hata", f"Dosya silinemedi: {str(e)}")
        else:
            QMessageBox.warning(self, "Hata", "Silinecek dosya mevcut değil.")

    def set_item_color(self, item):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_item_color(item, color)  # Bu satırı kullanarak rengi güncelle ve kaydet

    def save_colors_to_file(self):
        """Renkleri JSON dosyasına kaydet."""
        try:
            with open(self.color_settings_path, 'w') as file:
                json.dump(self.item_colors, file)
        except Exception as e:
            print(f"Error saving colors: {e}")

    def load_colors_from_file(self):
        """Item renklerini JSON dosyasından yükler."""
        if os.path.exists(self.color_settings_path):
            with open(self.color_settings_path, 'r') as file:
                self.item_colors = json.load(file)

            # Ağaçtaki renkleri geri yüklemek için
            def apply_color_to_item(item):
                file_path = item.data(0, Qt.UserRole)
                if file_path in self.item_colors:
                    color = QColor(self.item_colors[file_path])
                    item.setBackground(0, QBrush(color))

            # Tüm öğeleri dolaşarak renkleri uygula
            def iterate_tree_items(item):
                apply_color_to_item(item)
                for i in range(item.childCount()):
                    iterate_tree_items(item.child(i))

            iterate_tree_items(self.workplace_tree.invisibleRootItem())

    def update_item_color(self, item, color):
        file_path = item.data(0, Qt.UserRole)  # Dosya yolunu al
        if file_path:  # Eğer dosya yolu geçerliyse
            # Rengi kaydet
            self.item_colors[file_path] = color.name()  # Renk bilgisini kaydet (örn. '#RRGGBB')
            # Öğenin arka plan rengini değiştir
            item.setBackground(0, QBrush(color))
            # Değişiklikleri hemen kaydet
            self.save_colors_to_file()

    def new_file(self):
        """Yeni Python dosyası oluşturur."""
        print ("new_file 1310")
        if not self.project_dir:
            QMessageBox.warning(self, "Save Error", "Project directory is not set.")
            return
        self.add_new_tab("untitled.py")

    def load_suggestions(self):
        # suggestions.json'dan önerileri yükler
        with open(PathFromOS().json_path + "/suggestions.json", "r") as file:
            data = json.load(file)
        return data.get("suggestions", [])
        print (PathFromOS().json_path + "/suggestions.json")

    def create_new_file_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        dialog.resize(500, 80)

        # Pencereyi ortalamak
        qr = dialog.frameGeometry()
        qr.moveCenter(self.frameGeometry().center())
        dialog.move(qr.topLeft())

        # Gölge efekti
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(30)
        shadow_effect.setOffset(0, 8)
        shadow_effect.setColor(QColor(0, 0, 0, 150))
        dialog.setGraphicsEffect(shadow_effect)

        # Ana layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Ana pencere çerçevesine (input_frame) sadece stroke ekliyoruz
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(48, 48, 48, 230); /* Saydam koyu arka plan */
                border: 1px solid rgba(80, 80, 80, 200); /* Kenarlık sadece çerçevede */
                border-radius: 10px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(input_frame)

        # Python logosu (Kenarlık olmadan, saydamlık ile)
        icon_label = QLabel()
        python_icon_path = os.path.join(PathFromOS().icons_path, "python_logo.png")
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)
        python_icon = QPixmap(python_icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(python_icon)
        icon_label.setGraphicsEffect(opacity_effect)
        icon_label.setFixedSize(30, 30)
        icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        input_layout.addWidget(icon_label)

        # Dosya adı giriş alanı ve stil ayarları
        file_name_input = QLineEdit()
        file_name_input.setPlaceholderText("Enter file name (e.g., example)")
        file_name_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: rgba(128, 128, 128, 1); /* Normal yazı rengi gri */
                border: none;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5); /* Placeholder %50 saydam beyaz */
            }
        """)
        input_layout.addWidget(file_name_input)

        # Öneriler veya hata mesajı için dinamik alan (sağa yaslanmış, ortalanmış, %50 transparan)
        suggestion_label = QLabel("No suggestions.")
        suggestion_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Sağa yasla ve yukarıdan/aşağıdan ortala
        suggestion_label.setStyleSheet(
            "color: rgba(255, 165, 0, 0.5); border: none;")  # Turuncu ve %50 transparan, kenar çizgisi yok
        suggestion_label.setFixedWidth(200)  # Genişliği ayarla
        input_layout.addWidget(suggestion_label)

        # JSON'dan önerileri yükle
        suggestions = self.load_suggestions()

        # Dinamik öneri ve hata mesajı işlevi
        def on_text_changed():
            text = file_name_input.text()
            suggestion_label.setStyleSheet(
                "color: rgba(255, 165, 0, 0.5); border: none;")  # Öneri için turuncu %50 transparan

            # Uygun bir öneri bul
            found_suggestion = None
            for suggestion in suggestions:
                if suggestion.lower().startswith(text.lower()) and suggestion.lower() != text.lower():
                    found_suggestion = suggestion
                    break

            # Öneri veya hata mesajını güncelle
            if found_suggestion:
                suggestion_label.setText(found_suggestion)
            elif not is_valid_file_name(text):
                suggestion_label.setText("Invalid file name")
                suggestion_label.setStyleSheet(
                    "color: rgba(255, 94, 94, 1); border: none;")  # Hata mesajı için kırmızı %50 transparan
            else:
                suggestion_label.setText("")

        # Tamamlama için Tab tuşuna basıldığında öneriyi kabul et
        def complete_text():
            if suggestion_label.text() != "Invalid file name" and suggestion_label.text() != "":
                file_name_input.setText(suggestion_label.text())
                suggestion_label.setText("")

        file_name_input.textChanged.connect(on_text_changed)
        file_name_input.editingFinished.connect(complete_text)

        # Onay butonu (beyaz renkte, basılıyken gri)
        create_button = QPushButton()
        confirm_icon_path = os.path.join(PathFromOS().icons_path, "confirm_icon.png")
        create_button.setIcon(QIcon(confirm_icon_path))
        create_button.setFixedSize(30, 30)
        create_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 15px;
                color: #FFFFFF; /* Beyaz */
            }
            QPushButton:hover {
                opacity: 0.8;
            }
        """)
        input_layout.addWidget(create_button)

        # Dosya adı doğrulama fonksiyonu
        def is_valid_file_name(file_name):
            # Dosya adı boşluk, özel karakter içeremez
            return re.match(r'^[\w-]+$', file_name) is not None

        # Onay butonuna tıklama işlevi
        def on_create_clicked():
            file_name = file_name_input.text().strip()
            if not is_valid_file_name(file_name):
                suggestion_label.setText("Invalid file name")
                suggestion_label.setStyleSheet(
                    "color: rgba(255, 0, 0, 0.5); border: none;")  # Hata rengi %50 transparan
            else:
                self.create_file(file_name, dialog)

        create_button.clicked.connect(on_create_clicked)

        # Pencereyi saydamdan görünür hale getirme animasyonu
        dialog.setWindowOpacity(0)
        fade_in = QPropertyAnimation(dialog, b"windowOpacity")
        fade_in.setDuration(400)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        fade_in.start()

        # Diyalog gösterimi
        dialog.exec_()

    def create_file(self, file_name, dialog):
        # Proje dizini kontrolü
        if not self.project_dir:
            QMessageBox.warning(self, "No Project Directory", "Please open or create a project before saving files.")
            return

        # Dosya adı Python kurallarına uygun mu kontrol etme
        if not file_name.endswith(".py"):
            file_name += ".py"

        if not self.is_valid_python_identifier(file_name[:-3]):
            QMessageBox.warning(self, "Invalid File Name", "The file name must follow Python naming conventions!")
            return

        full_path = os.path.join(self.project_dir, file_name)
        with open(full_path, 'w') as file:
            file.write("# New Python file\n")

        self.add_new_tab(full_path)  # Yeni dosya ile bir sekme aç
        print ("add_new_tab 1500")
        self.populate_workplace(self.project_dir)  # "Workplace" görünümünü güncelle
        dialog.close()

    def add_new_tab(self, file_path, initial_content=""):
        """Yeni bir sekme oluşturur ve dosyayı yükler."""
        editor = CodeEditor()  # QPlainTextEdit yerine CodeEditor kullanıyoruz
        print ("add_new tab 1001")
        editor.textChanged.connect(self.update_header_tree)  # Direkt editor widget'ine bağlama yaptık

        # Dosya içeriği eğer mevcutsa yüklüyoruz, yoksa varsayılan içerik ile açıyoruz
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                editor.setPlainText(content)
        else:
            editor.setPlainText(initial_content)

        editor.textChanged.connect(lambda: self.mark_as_modified(editor))

        self.tab_widget.addTab(editor, self.python_icon, os.path.basename(file_path))
        self.tab_widget.setCurrentWidget(editor)

        # Completer popup'ını kontrol etmeden önce niteliklerin var olup olmadığını kontrol ediyoruz
        if hasattr(editor, 'completer') and hasattr(editor.completer, 'completion_popup'):
            editor.completer.completion_popup.popup().hide()

    def mark_as_modified(self, editor):
        """Eğer sekmedeki dosya kaydedilmemişse, başlıkta '*' gösterir."""
        index = self.tab_widget.indexOf(editor)
        if index != -1:
            tab_title = self.tab_widget.tabText(index)
            if not tab_title.startswith("*"):
                self.tab_widget.setTabText(index, "*" + tab_title)


    def open_project(self):
        """Open an existing project and set self.project_dir to the selected directory."""
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            self.project_dir = project_path
            self.populate_workplace(project_path)
            self.setWindowTitle(self.empty_project_win_title + os.path.basename(project_path))

            # Projeyi recent_projects_list'e ekleyelim
            self.add_to_recent_projects(self.project_dir)

    def add_to_recent_projects(self, project_path):
        """Projeyi recent projects listesine ekler."""
        # Eğer proje zaten listede varsa çıkaralım
        if project_path in self.recent_projects_list:
            self.recent_projects_list.remove(project_path)

        # En başa ekleyelim
        self.recent_projects_list.insert(0, project_path)

        # Eğer 7'den fazla proje varsa, en son projeyi çıkaralım
        if len(self.recent_projects_list) > 7:
            self.recent_projects_list.pop()

        # Listeyi güncelle ve dosyaya kaydet
        self.save_recent_projects()
        self.update_recent_projects_menu()


    def save_recent_projects(self):
        """Recent Projects listesini JSON dosyasına düzenli bir formatta kaydeder ve tekrar eden yolları kaldırır."""
        try:
            # Platform bağımsız yollar için normalize et ve tekrar edenleri kaldır
            normalized_paths = list(dict.fromkeys(
                [os.path.normpath(path) for path in self.recent_projects_list]
            ))

            # Son eklenen yolu listenin en üstüne taşı
            if normalized_paths:
                most_recent = normalized_paths.pop()  # Son yolu al
                normalized_paths.insert(0, most_recent)  # En üste ekle

            # JSON dosyasına recent_paths anahtarı altında kaydet
            with open(self.recent_projects_path, 'w') as file:
                json.dump({"recent_paths": normalized_paths}, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving recent projects: {e}")

    def load_recent_projects(self):
        """Recent Projects listesini JSON dosyasından yükler."""
        if os.path.exists(self.recent_projects_path):
            try:
                with open(self.recent_projects_path, 'r') as file:
                    data = json.load(file)
                    self.recent_projects_list = data.get("recent_paths", [])
            except Exception as e:
                print(f"Error loading recent projects: {e}")
                self.recent_projects_list = []  # Hata durumunda boş listeye geç

        # Menüde göstermek için listeyi güncelle
        self.update_recent_projects_menu()

    def open_file(self):
        """Dosya açma işlemi."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "Python Dosyaları (*.py);;Tüm Dosyalar (*)")

        if file_name:
            # Öncelikle aynı dosya yoluna sahip bir sekmenin açık olup olmadığını kontrol edelim
            for index in range(self.tab_widget.count()):
                existing_editor = self.tab_widget.widget(index)
                if self.tab_widget.tabText(index) == os.path.basename(file_name):
                    # Eğer aynı isimde bir sekme açıksa, mevcut sekmeyi öne getir
                    self.tab_widget.setCurrentWidget(existing_editor)
                    return  # Yeni bir sekme açılmasını engelle ve çık

            # Aynı dosya açık değilse yeni bir sekme aç
            self.add_new_tab(file_name)
            print("add_new_tab 1625")

    def save_file(self):
        """Save the current file."""
        if self.project_dir is None:
            QMessageBox.warning(self, "Save projects",
                                "Please create and save the python file.\nThere is no opened project currently this project is empty\nIf you want to do nothing please discard.")
            return

        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            index = self.tab_widget.indexOf(current_editor)
            if index != -1:
                tab_title = self.tab_widget.tabText(index).replace("*", "")
                file_path = os.path.join(self.project_dir, tab_title)  # Ensure project_dir is not None
                with open(file_path, 'w') as file:
                    file.write(current_editor.toPlainText())
                self.tab_widget.setTabText(index, tab_title)

    def save_file_as(self):
        """Dosyayı farklı bir yola kaydeder."""
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            file_name, _ = QFileDialog.getSaveFileName(self, "Dosya Kaydet", "",
                                                       "Python Dosyaları (*.py);;Tüm Dosyalar (*)")
            if file_name:
                with open(file_name, 'w') as file:
                    file.write(current_editor.toPlainText())
                index = self.tab_widget.indexOf(current_editor)
                self.tab_widget.setTabText(index, os.path.basename(file_name))

    def close_tab(self, index):
        """Bir sekmeyi kapatmadan önce kontrol eder."""
        editor = self.tab_widget.widget(index)
        print ("istemci kapatildi")
        if editor.document().isModified():
            # Eğer sekmede kaydedilmemiş değişiklikler varsa kullanıcıya soralım
            response = self.prompt_save_changes(editor)
            if response == QMessageBox.Save:
                self.save_file()
                self.tab_widget.removeTab(index)  # Dosya kaydedildiyse tabı kapat
            elif response == QMessageBox.Discard:
                self.tab_widget.removeTab(index)  # Kaydetmeden kapat
            elif response == QMessageBox.Cancel:
                return  # İptal edildiğinde hiçbir işlem yapma

        else:
            self.tab_widget.removeTab(index)  # Değişiklik yoksa doğrudan kapat

    def closeEvent(self, event):
        """Uygulamayı kapatmadan önce kaydedilmemiş değişiklikleri kontrol eder."""
        response = self.prompt_save_changes()

        # Eğer kaydedilmemiş dosya yoksa, mesaj gösterilmez ve direkt kapatılır
        if response is None:
            event.accept()
            return

        # Kaydedilmemiş dosyalar varsa soruları soralım
        if response == QMessageBox.Save:
            self.save_all_files()
            event.accept()
        elif response == QMessageBox.Discard:
            event.accept()  # Exit without saving
        elif response == QMessageBox.Cancel:
            event.ignore()  # Çıkışı iptal et

    def prompt_save_changes(self, editor=None):
        """Kaydedilmemiş değişiklikler için bir uyarı gösterir ve kullanıcıdan giriş alır."""
        unsaved_files = []

        # Eğer belirli bir editördeki kaydedilmemiş değişiklik kontrol ediliyorsa, onun adını ekle
        if editor:
            if editor.document().isModified():
                unsaved_files.append(self.tab_widget.tabText(self.tab_widget.indexOf(editor)))
        else:
            # Tüm kaydedilmemiş dosyaların listesini alalım
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if editor.document().isModified():
                    tab_title = self.tab_widget.tabText(i)
                    unsaved_files.append(tab_title)

        # Eğer kaydedilmemiş dosya yoksa None döndür ve mesaj göstermeden devam et
        if not unsaved_files:
            return None

        # Kaydedilmemiş dosyalar varsa mesajı oluştur
        message = "You did not save the last changes made.\nUnsaved files:\n"
        message += "\n".join(f"- {file}" for file in unsaved_files)

        # Kaydetme, kaydetmeden çıkma ve iptal seçeneklerini sunalım
        response = QMessageBox.question(
            self,
            "Unsaved changes",
            message,
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        return response

    def file_exit(self):
        """File > Exit tıklandığında kaydedilmemiş dosyaları kontrol eder ve işlemi kapatır."""
        response = self.prompt_save_changes()

        # Eğer kaydedilmemiş dosya yoksa, uygulamayı kapat
        if response is None:
            self.close()
            return

        # Kaydedilmemiş dosyalar varsa kullanıcıya soralım
        if response == QMessageBox.Save:
            self.save_all_files()
            self.close()
        elif response == QMessageBox.Discard:
            self.close()  # Kaydetmeden çık
        elif response == QMessageBox.Cancel:
            pass  # İptal edildi, hiçbir şey yapma

    def save_all_files(self):
        """Tüm açık sekmelerdeki dosyaları kaydeder."""
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.document().isModified():
                self.save_file()

    def ensure_tab(self):
        if self.tab_widget.count() == 0:
            # Yeni bir sekme açıyoruz
            print("add_new_tab 1915")
            self.add_new_tab("untitled.py", initial_content=CodeEditorSettings().temp_codes)

            # Yeni tab açıldığında completer'ı gizleyelim
            current_editor = self.tab_widget.currentWidget()
            if isinstance(current_editor, CodeEditor):
                current_editor.completer.completion_popup.popup().hide()

    def close_app(self):
        """Programı kapatır."""
        reply = QMessageBox.question(self, 'Çıkış',
                                     "There are unsaved changes. Do you still want to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()

    def create_docks(self):
        """Sol tarafa dockable listeleri ekler."""
        # Workplace dock widget
        self.workplace_dock = QDockWidget("WORKPLACE", self)
        expand_icon_path = os.path.join(PathFromOS().icons_path, 'expand_icon.svg')
        collapse_icon_path = os.path.join(PathFromOS().icons_path, 'collapse_icon.svg')

        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderHidden(True)
        self.workplace_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.workplace_tree.customContextMenuRequested.connect(self.context_menu)
        self.workplace_tree.itemDoubleClicked.connect(self.on_workplace_item_double_clicked)
        self.workplace_dock.setWidget(self.workplace_tree)
        self.addDockWidget(self.settings.WORKPLACE_DOCK_POS, self.workplace_dock)
        self.workplace_dock.setVisible(self.settings.WORKPLACE_VISIBLE)
        self.workplace_tree.setAlternatingRowColors(True)

        # Başlık oluşturmaOUTPUT_DOCK_POS
        self.create_dock_title("WORKSPACE", self.workplace_dock, expand_icon_path, collapse_icon_path)

        # OUTLINER ve HEADER widget'larını oluşturma
        self.create_outliner_dock(expand_icon_path, collapse_icon_path)
        self.create_header_dock(expand_icon_path, collapse_icon_path)

    def create_dock_title(self, title, dock_widget, expand_icon_path, collapse_icon_path):
        """Dock widget başlığını özelleştirme ve collapse/expand işlevi ekleme."""
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(5, 5, 5, 5)

        # İkon ve toggle işlemi için QLabel
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(expand_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.mousePressEvent = lambda event: self.toggle_dock_widget(dock_widget, icon_label, expand_icon_path,
                                                                           collapse_icon_path)

        # Title text
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignVCenter)
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)

        # Layout ekleme
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_widget.setLayout(title_layout)

        dock_widget.setTitleBarWidget(title_widget)

    def toggle_dock_widget(self, dock_widget, icon_label, expand_icon_path, collapse_icon_path):
        """Dock widget'ı collapse/expand yapma fonksiyonu."""
        is_collapsed = dock_widget.maximumHeight() == 30
        if is_collapsed:
            dock_widget.setMinimumHeight(200)
            dock_widget.setMaximumHeight(16777215)
            icon_label.setPixmap(
                QPixmap(collapse_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            dock_widget.setMinimumHeight(30)
            dock_widget.setMaximumHeight(30)
            icon_label.setPixmap(QPixmap(expand_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def create_outliner_dock(self, expand_icon_path, collapse_icon_path):
        """OUTLINER dock widget'ını oluşturur ve başlığı özelleştirir."""
        self.outliner_dock = QDockWidget("OUTLINER", self)
        outliner_widget = QWidget()
        outliner_layout = QVBoxLayout(outliner_widget)
        outliner_layout.setContentsMargins(0, 0, 0, 0)  # Tüm kenarlardan sıfır boşluk
        outliner_layout.setSpacing(0)  # Öğeler arasında boşluk yok

        # PathFromOS sınıfının bir örneğini oluşturuyoruz
        path_from_os = PathFromOS()

        # İkon yolunu alıyoruz
        expand_icon = os.path.join(path_from_os.icons_path, 'expand_icon.svg')
        collapse_icon = os.path.join(path_from_os.icons_path, 'collapse_icon.svg')

        # OUTLINER QTreeWidget tanımla
        self.outliner_list = QTreeWidget()
        self.outliner_list.setHeaderHidden(True)  # Başlığı gizle
        self.outliner_list.setAlternatingRowColors(False)
        self.outliner_list.setStyleSheet("""
            QTreeWidget {
                background-color: #2B2B2B;
                border: none;
                font-size: 9pt;  /* Yazı boyutu */
            }
            
        """)

        self.outliner_list.setRootIsDecorated(False)  # Klasör simgeleri ve bağlantı çizgilerini gizler
        self.outliner_list.setStyleSheet(
            "QTreeWidget::branch { background-color: transparent; }")  # Dikey çizgileri kaldırır

        # Arama çubuğu için bir widget ve layout oluştur
        self.search_widget = QWidget()
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_widget.setFixedHeight(25)  # Arama çubuğu yüksekliği
        self.search_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(60, 60, 60, 0.8); /* Yarı saydam arka plan */
                border-radius: 8px;
            }
        """)
        self.search_widget.setVisible(False) # It will be hidden initially

        # Add SearchBar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 0.8); 
                border: none;
                color: #FFFFFF;
                padding-left: 5px;
                height: 20px;  
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)

        self.search_bar.textChanged.connect(self.filter_outliner)
        search_layout.addWidget(self.search_bar)

        # OUTLINER widget'ını layout'a ekleyin
        outliner_layout.addWidget(self.outliner_list)
        outliner_layout.addWidget(self.search_widget)  # Arama çubuğu alta ekleniyor

        # OUTLINER widget'ını Outliner dock'a bağla
        self.outliner_dock.setWidget(outliner_widget)
        self.addDockWidget(self.settings.OUTLINER_DOCK_POS, self.outliner_dock)
        self.outliner_dock.setVisible(self.settings.OUTLINER_VISIBLE)

        self.populate_outliner_with_functions()
        # Sağ tıklama menüsü ekle (Context Menu)
        self.outliner_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outliner_list.customContextMenuRequested.connect(self.context_menu_outliner)
        # OUTLINER başlık stilini oluştur ve arama ikonunu ekle
        self.create_custom_dock_title("OUTLINER", self.outliner_dock, expand_icon_path, collapse_icon_path)

        # Arama çubuğunu gösterme ve gizleme için animasyonlar
        self.search_animation_show = QPropertyAnimation(self.search_widget, b"maximumHeight")
        self.search_animation_hide = QPropertyAnimation(self.search_widget, b"maximumHeight")

        # Animasyon durumu kontrolü için bayrak
        self.search_bar_visible = False  # Çubuğun görünürlüğünü kontrol eden bayrak
        # Nuke fonksiyonlarını JSON'dan yükle ve OUTLINER'a ekle
        self.nuke_functions = load_nuke_functions()  # JSON'dan Nuke fonksiyonlarını yükle
        if self.nuke_functions:
            self.add_nuke_functions_to_outliner(self.nuke_functions)  # Eğer fonksiyonlar doluysa OUTLINER'a ekle

    def create_custom_dock_title(self, title, dock_widget, expand_icon_path, collapse_icon_path):
        """OUTLINER başlığını özelleştirir, simge ve arama ikonunu ekler."""
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Sol tarafa ikonu ekleyelim
        expand_icon_label = QLabel()
        expand_icon_label.setPixmap(QPixmap(expand_icon_path).scaled(25, 25, Qt.KeepAspectRatio,
                                                                     Qt.SmoothTransformation))  # İkonu 25x25 olarak büyüttük
        expand_icon_label.mousePressEvent = lambda event: self.toggle_dock_widget(dock_widget, expand_icon_label,
                                                                                  expand_icon_path, collapse_icon_path)
        title_layout.addSpacing(5)  # İkonu sağa kaydırıyoruz
        title_layout.addWidget(expand_icon_label)

        # OUTLINER başlık yazısı
        # Başlık metni
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignVCenter)
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)
        title_layout.addWidget(title_label)

        title_layout.addStretch(1)  # Başlığı sola yaslamak için araya boşluk ekle

        # Sağ tarafa arama ikonunu ekleyelim
        search_icon_label = QLabel()
        search_icon_label.setPixmap(
            QPixmap(os.path.join(PathFromOS().icons_path, "find.svg")).scaled(20, 20, Qt.KeepAspectRatio,
                                                                              Qt.SmoothTransformation))  # Arama simgesini de 20x20 olarak büyüttük
        search_icon_label.setStyleSheet("QLabel { padding: 5px; cursor: pointer; }")
        search_icon_label.mousePressEvent = self.toggle_search_bar  # İkona tıklandığında arama çubuğunu aç/kapa
        title_layout.addWidget(search_icon_label)

        # Özel başlık widget'ını dock'un başlığı olarak ayarla
        title_bar.setLayout(title_layout)
        dock_widget.setTitleBarWidget(title_bar)

    def toggle_search_bar(self, event):
        """Arama çubuğunu aç/kapa."""
        if not self.search_bar_visible:
            self.show_search_bar(event)
        else:
            self.hide_search_bar(event)

    def show_search_bar(self, event):
        """Arama çubuğunu kayarak göster."""
        if not self.search_bar_visible:
            # Arama çubuğunun açılması için animasyon ayarları
            self.search_animation_show.setDuration(300)
            self.search_animation_show.setStartValue(0)  # Gizli başlıyor
            self.search_animation_show.setEndValue(25)  # Arama çubuğunun tam yüksekliği
            self.search_animation_show.setEasingCurve(QEasingCurve.OutQuad)
            self.search_widget.setVisible(True)  # Arama widget'ını görünür yap
            self.search_animation_show.start()

            # Çubuğun şu an görünür olduğunu işaretleyelim
            self.search_bar_visible = True

    def hide_search_bar(self, event):
        """Arama çubuğunu kayarak gizle."""
        if self.search_bar_visible:
            # Arama çubuğunun kapanması için animasyon ayarları
            self.search_animation_hide.setDuration(300)
            self.search_animation_hide.setStartValue(25)  # Tam yükseklikten başlıyor
            self.search_animation_hide.setEndValue(0)  # Gizli sonlanıyor
            self.search_animation_hide.setEasingCurve(QEasingCurve.InQuad)
            self.search_animation_hide.start()
            self.search_animation_hide.finished.connect(
                lambda: self.search_widget.setVisible(False))  # Animasyon bitince gizle

            # Çubuğun şu an gizlendiğini işaretleyelim
            self.search_bar_visible = False

    def create_header_dock(self, expand_icon_path, collapse_icon_path):
        """HEADER dock widget'ını oluşturur."""
        self.header_dock = QDockWidget("HEADER", self)
        self.header_tree = QTreeWidget()

        # Apply the same stylesheet as OUTLINER to the HEADER's QTreeWidget
        self.header_tree.setHeaderHidden(True)  # Dikey çizgileri gizler

        # Copying the same style from OUTLINER to HEADER and hiding the +, -, and lines
        self.header_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                font-size: 9pt;  /* Yazı boyutu */
            }
        """)
        self.header_tree.setRootIsDecorated(False)
        self.header_dock.setWidget(self.header_tree)
        self.addDockWidget(self.settings.HEADER_DOCK_POS, self.header_dock)
        self.header_dock.setVisible(self.settings.HEADER_VISIBLE)

        self.header_tree.itemClicked.connect(self.go_to_line_from_header)

        # HEADER başlığı için özel widget
        self.create_dock_title("HEADER", self.header_dock, expand_icon_path, collapse_icon_path)

    def update_header_tree(self):
        """QPlainTextEdit içindeki metni analiz edip sınıf ve fonksiyonları HEADER'a ekler."""
        self.header_tree.clear()  # Eski öğeleri temizliyoruz

        current_editor = self.tab_widget.currentWidget()
        if current_editor is None:
            return  # Aktif bir düzenleyici yoksa fonksiyondan çıkın

        code = current_editor.toPlainText()  # Düzenleyicideki tüm metni alıyoruz

        try:
            tree = ast.parse(code)  # Python kodunu AST'ye çeviriyoruz
        except (SyntaxError, IndentationError):
            # Eğer kod geçerli değilse, HEADER'ı güncellemeyin
            return

        # Define the paths for the icons
        class_icon_path = os.path.join(PathFromOS().icons_path, "C_logo.svg")
        def_icon_path = os.path.join(PathFromOS().icons_path, "def.svg")
        project_icon_path = os.path.join(PathFromOS().icons_path, "python.svg")

        # Project header with an icon if a project is set
        if self.project_dir:
            project_item = QTreeWidgetItem(self.header_tree)
            project_item.setText(0, os.path.basename(self.project_dir))  # Project name
            project_item.setIcon(0, QIcon(project_icon_path))  # Project icon
            project_item.setFirstColumnSpanned(True)  # Span the project name across the header

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):  # Eğer sınıf tanımıysa
                class_item = QTreeWidgetItem(self.header_tree)
                class_item.setText(0, node.name)  # Sınıf ismi
                class_item.setText(1, "Class")  # Türü
                class_item.setIcon(0, QIcon(class_icon_path))  # Sınıf için ikon
                class_item.setData(0, Qt.UserRole, node.lineno)

                # Indentation for class items
                class_item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                class_item.setSizeHint(0, QSize(200, 20))  # Adjust size for better spacing

                # Sınıfın metodlarını ekleyelim
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        method_item = QTreeWidgetItem(class_item)
                        method_item.setText(0, sub_node.name)
                        method_item.setText(1, "Method")
                        method_item.setIcon(0, QIcon(def_icon_path))  # Metod için ikon
                        method_item.setData(0, Qt.UserRole, sub_node.lineno)

                        # Indentation for method items
                        method_item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                        method_item.setSizeHint(0, QSize(200, 20))  # Adjust size for better spacing

            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef):
                # Eğer sınıf dışı bir fonksiyon tanımıysa doğrudan ekleyelim
                func_item = QTreeWidgetItem(self.header_tree)
                func_item.setText(0, node.name)  # Fonksiyon ismi
                func_item.setText(1, "Function")
                func_item.setIcon(0, QIcon(def_icon_path))  # Fonksiyon için ikon
                func_item.setData(0, Qt.UserRole, node.lineno)

                # Indentation for function items
                func_item.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                func_item.setSizeHint(0, QSize(200, 20))  # Adjust size for better spacing

    def go_to_line_from_header(self, item, column):
        """HEADER'da bir öğeye tıklandığında ilgili satıra gitme işlemi."""
        line_number = item.data(0, Qt.UserRole)  # Satır numarası verisini alıyoruz
        if line_number is not None:
            cursor = self.tab_widget.currentWidget().textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)  # Satıra gitme
            self.tab_widget.currentWidget().setTextCursor(cursor)
            self.tab_widget.currentWidget().setFocus()

    def insert_into_editor(self, item, column):
        """OUTLINER'da çift tıklanan öğeyi aktif metin düzenleyiciye ekler."""
        # Seçilen sınıf ya da fonksiyon adını al
        selected_text = item.text(0)

        # Aktif düzenleyiciye eriş
        current_editor = self.tab_widget.currentWidget()

        if current_editor:  # Eğer düzenleyici varsa
            cursor = current_editor.textCursor()  # Düzenleyicinin imlecini al

            # Metni imlecin olduğu yere ekleyelim ve bir boşluk ekleyelim
            cursor.insertText(selected_text + ' ')  # Metni ekledikten sonra bir boşluk ekler

            # İmleci güncelle
            current_editor.setTextCursor(cursor)

    def context_menu_outliner(self, position):
        """OUTLINER'da sağ tıklama menüsü oluşturur."""
        item = self.outliner_list.itemAt(position)
        if item is None:
            return

        menu = QMenu()

        # "Insert the Code" seçeneği
        insert_action = QAction("Insert the Code", self)
        insert_action.triggered.connect(lambda: self.insert_into_editor(item, 0))

        # "Go to Information" seçeneği
        go_to_info_action = QAction("Search API Reference", self)
        go_to_info_action.triggered.connect(lambda: self.go_to_information(item))

        # Menü öğelerini ekleyin
        menu.addAction(insert_action)
        menu.addAction(go_to_info_action)

        # Ayraç ekleyin
        menu.addSeparator()

        # "Expand All" seçeneği
        expand_all_action = QAction("Expand All", self)
        expand_all_action.triggered.connect(self.expand_all_outliner_items)
        menu.addAction(expand_all_action)

        # "Collapse All" seçeneği
        collapse_all_action = QAction("Collapse All", self)
        collapse_all_action.triggered.connect(self.collapse_all_outliner_items)
        menu.addAction(collapse_all_action)

        # Ayraç ekleyin
        menu.addSeparator()

        # "Search QLineEdit'i Aç" seçeneği
        search_action = QAction("Open Search Bar", self)
        search_action.triggered.connect(self.toggle_search_bar)  # Daha önceki toggle_search_bar işlevine bağlandı
        menu.addAction(search_action)

        # Sağ tıklama menüsünü göster
        menu.exec_(self.outliner_list.viewport().mapToGlobal(position))

    def expand_all_outliner_items(self):
        """OUTLINER'daki tüm öğeleri genişletir."""
        self.outliner_list.expandAll()

    def collapse_all_outliner_items(self):
        """OUTLINER'daki tüm öğeleri kapatır."""
        self.outliner_list.collapseAll()

    def toggle_search_bar(self, event=None):
        """Search QLineEdit'i aç/kapa."""
        if not self.search_bar_visible:
            self.show_search_bar(event)  # Arama çubuğunu göster
        else:
            self.hide_search_bar(event)  # Arama çubuğunu gizle

    def go_to_information(self, item):
        """Seçilen öğeyi geliştirici kılavuzunda arar."""
        selected_text = item.text(0)  # Seçilen öğe

        # URL şablonu
        base_url = "https://learn.foundry.com/nuke/developers/15.0/pythondevguide/search.html"

        # Arama sorgusunu oluştur
        search_url = f"{base_url}?q={selected_text}&check_keywords=yes&area=default"

        # Tarayıcıda aç
        webbrowser.open(search_url)

    def custom_outliner_action(self, item):
        """OUTLINER'da özel bir işlem gerçekleştirir."""
        selected_text = item.text(0)
        QMessageBox.information(self, "Custom Action", f"You selected: {selected_text}")

    def filter_outliner(self, text):
        """Filters items in OUTLINER based on text in the search bar"""
        root = self.outliner_list.invisibleRootItem()  # OUTLINER'ın kök öğesi

        # Filtre metni boşsa tüm öğeleri göster
        if not text:
            for i in range(root.childCount()):
                item = root.child(i)
                item.setHidden(False)
                for j in range(item.childCount()):
                    sub_item = item.child(j)
                    sub_item.setHidden(False)
            return

        # Filter classes and methods based on search text
        for i in range(root.childCount()):  # Ana öğeler (sınıflar)
            item = root.child(i)
            match_found = False  # Ana öğeyi gösterip göstermeme durumu

            # Ana öğe metniyle arama metni eşleşiyor mu?
            if text.lower() in item.text(0).lower():
                item.setHidden(False)
                match_found = True
            else:
                item.setHidden(True)

            # Alt öğeleri kontrol et (metotlar)
            for j in range(item.childCount()):
                sub_item = item.child(j)

                if text.lower() in sub_item.text(0).lower():  # Arama metni alt öğeyle eşleşiyor mu?
                    sub_item.setHidden(False)
                    match_found = True  # Eğer bir alt öğe eşleşiyorsa ana öğeyi de göster
                else:
                    sub_item.setHidden(True)

            # Eğer alt öğelerden biri eşleştiyse ana öğeyi göster
            if match_found:
                item.setHidden(False)

    def update_completer_from_outliner(self):
        """OUTLINER'daki sınıf ve fonksiyon isimlerini QCompleter'e ekler."""
        outliner_items = []
        root = self.outliner_list.invisibleRootItem()  # OUTLINER'ın kök öğesi

        # OUTLINER'daki tüm öğeleri dolaşarak listeye ekle
        for i in range(root.childCount()):  # Ana öğeler (class'lar)
            item = root.child(i)
            outliner_items.append(item.text(0))  # Class ismini ekle

            for j in range(item.childCount()):  # Alt öğeler (methods'ler)
                sub_item = item.child(j)
                outliner_items.append(sub_item.text(0))  # Method ismini ekle

        # Tamamlama önerileri için QStringListModel kullanarak model oluşturuyoruz
        model = QStringListModel(outliner_items, self.completer)
        self.completer.setModel(model)

    def is_valid_python_identifier(self, name):
        """Python değişken adı kurallarına uygunluk kontrolü"""
        if not name.isidentifier():
            return False
        return True

    def show_python_naming_info(self):
        QMessageBox.information(self, "Python Naming Info",
                                "Python file names must:\n- Start with a letter or underscore\n- Contain only letters, numbers, or underscores\n- Not be a reserved keyword")

