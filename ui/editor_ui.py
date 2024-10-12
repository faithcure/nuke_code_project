
from PySide2.QtWidgets import QMainWindow, QLabel, QTabWidget, QDockWidget, QTreeWidget, QTextEdit, QAction,     QInputDialog, QMessageBox, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidgetItem,     QLineEdit, QCompleter, QMenu, QColorDialog, QToolBar, QSizePolicy, QApplication, QSpacerItem
from PySide2.QtGui import QIcon, QFont, QColor, QTextCursor, QTextCharFormat, QBrush
from PySide2.QtCore import Qt, QSize
import os
import json

class EditorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Set up the main window
        self.empty_project_win_title = "Nuke Code Editor: "
        self.setWindowTitle("Nuke Code Editor: Empty Project**")
        self.setGeometry(100, 100, 1200, 800)
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Replace label on the right side of status bar
        self.replace_status_label = QLabel("Status")
        self.status_bar.addPermanentWidget(self.replace_status_label)

        # Tab widget setup
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.setCentralWidget(self.tab_widget)

        # Text output
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Consolas", 10))

        # Initial UI setup functions
        self.create_menu()
        self.create_toolbar()
        self.create_docks()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        edit_menu = menubar.addMenu('Edit')
        run_menu = menubar.addMenu('Run')
        help_menu = menubar.addMenu('Help')
        workspace_menu = menubar.addMenu('Workspace')

        new_project_action = QAction(QIcon('icons/new_project.png'), 'New Project', self)
        open_project_action = QAction(QIcon('icons/open_project.png'), 'Open Project', self)
        new_file_action = QAction(QIcon('icons/new_file.png'), 'New File', self)
        open_action = QAction(QIcon('icons/open.png'), 'Open File', self)
        save_action = QAction(QIcon('icons/save.png'), 'Save', self)
        save_as_action = QAction(QIcon('icons/save_as.png'), 'Save As', self)
        exit_action = QAction(QIcon('icons/exit.png'), 'Exit', self)

        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addSeparator()
        file_menu.addAction(new_file_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Additional Edit menu setup
        find_action = QAction(QIcon('icons/find.png'), 'Search', self)
        replace_action = QAction(QIcon('icons/replace.png'), 'Replace All', self)
        undo_action = QAction(QIcon('icons/undo.png'), 'Undo', self)
        redo_action = QAction(QIcon('icons/redo.png'), 'Redo', self)
        clear_action = QAction(QIcon('icons/clear.png'), 'Clear Output', self)

        edit_menu.addAction(find_action)
        edit_menu.addAction(replace_action)
        edit_menu.addSeparator()
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(clear_action)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(35, 35))
        self.addToolBar(toolbar)

        run_action = QAction(QIcon("icons/play.png"), "Run", self)
        save_action = QAction(QIcon("icons/save.png"), "Save", self)
        clear_action = QAction(QIcon("icons/clear.png"), "Clear Output", self)
        settings_action = QAction(QIcon("icons/settings.png"), "Settings", self)

        toolbar.addAction(run_action)
        toolbar.addAction(save_action)
        toolbar.addAction(clear_action)
        toolbar.addAction(settings_action)

    def create_docks(self):
        output_dock = QDockWidget("Output", self)
        output_dock.setWidget(self.output_text_edit)
        self.addDockWidget(Qt.BottomDockWidgetArea, output_dock)

        # WORKPLACE dock
        self.workplace_tree = QTreeWidget()
        workplace_dock = QDockWidget("WORKPLACE", self)
        workplace_dock.setWidget(self.workplace_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, workplace_dock)

        # OUTLINER dock
        outliner_dock = QDockWidget("OUTLINER", self)
        self.outliner_list = QTreeWidget()
        self.outliner_list.setHeaderLabels(["Class/Function", "Type"])
        outliner_dock.setWidget(self.outliner_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, outliner_dock)

        # HEADER dock
        header_dock = QDockWidget("HEADER", self)
        self.header_tree = QTreeWidget()
        self.header_tree.setHeaderLabels(["Element", "Type"])
        header_dock.setWidget(self.header_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, header_dock)
