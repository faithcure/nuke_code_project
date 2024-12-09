import os
import importlib
from PySide2.QtWidgets import QToolButton, QAction, QToolBar, QWidget, QSizePolicy, QMenu
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
import editor.core
import editor.nlink
import editor.settings.settings_ux as settings_ux
importlib.reload(editor.core)
importlib.reload(editor.nlink)
importlib.reload(settings_ux)
from editor.nlink import update_nuke_functions
from editor.core import PathFromOS, CodeEditorSettings


class MainToolbar:
    """
    MainToolbar is responsible for creating and managing the toolbar in the main application window.
    It provides a set of actions such as running code, saving files, searching within code, updating functions,
    and more.
    """

    @staticmethod
    def create_toolbar(parent):
        """
        Creates the main toolbar and adds necessary buttons and actions to it.
        Args:
            parent: The parent widget to which the toolbar is attached.
        """
        # Create the toolbar and set its properties
        toolbar = parent.addToolBar("MAIN TOOLBAR")
        parent.addToolBar(CodeEditorSettings().setToolbar_area, toolbar)  # Place toolbar on the left side of the window

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expands horizontally, not vertically

        # Set icon size for the toolbar
        toolbar.setIconSize(CodeEditorSettings().toolbar_icon_size)
        toolbar.setStyleSheet("QToolBar { spacing: 4px; }")
        toolbar.setMovable(True)
        parent.addToolBar(Qt.TopToolBarArea, toolbar)

        # 1. RUN Button (To execute code)
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), '', parent)
        run_action.setToolTip("Run Current Code")
        run_action.triggered.connect(parent.run_code)
        toolbar.addAction(run_action)

        # 2. SAVE Button (To save the current file)
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), '', parent)
        save_action.setToolTip("Save Current File")
        save_action.triggered.connect(parent.save_file)
        toolbar.addAction(save_action)

        # 3. SEARCH Button (To search within the code)
        search_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), '', parent)
        search_action.setToolTip("Search in Code")
        search_action.triggered.connect(parent.show_search_dialog)
        toolbar.addAction(search_action)

        # 4. UPDATE Button (NLink functionality to update functions)
        update_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'update.svg')), 'Update NLink', parent)
        update_action.setToolTip("Update Nuke Functions List (NLink!)")
        update_action.triggered.connect(update_nuke_functions)
        toolbar.addAction(update_action)
        toolbar.addSeparator()

        # 5. Spacer Widget (Pushes buttons to the right or bottom)
        toolbar.addWidget(spacer)

        # Function to create the UI mode switch menu
        def create_expand_menu():
            """
            Creates a dropdown menu for switching UI modes.
            Returns:
                QMenu: The constructed menu with UI mode options.
            """
            mode_menu = QMenu(parent)
            for mode_name, function in settings_ux.ui_modes.items():  # Use `ui_modes` from settings_ux
                action = mode_menu.addAction(mode_name)
                action.triggered.connect(lambda checked=False, func=function: func(parent))
            return mode_menu

        # Create the menu and link it to a button
        ui_menu = create_expand_menu()

        ui_button = QToolButton(toolbar)
        ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))
        ui_button.setToolTip("Switch Toolbar Modes")
        ui_button.setPopupMode(QToolButton.InstantPopup)
        ui_button.setMenu(ui_menu)
        toolbar.addWidget(ui_button)

        # Adjust the layout of the button based on toolbar orientation
        def adjust_expand_layout(orientation):
            """
            Adjusts the layout and icon of the UI button based on toolbar orientation.
            Args:
                orientation (Qt.Orientation): The orientation of the toolbar.
            """
            if orientation == Qt.Vertical:
                ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))
            else:
                ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))

        # Connect the orientation change signal to adjust the button layout
        toolbar.orientationChanged.connect(adjust_expand_layout)

        # 6. CLEAR Button (Clears the output panel)
        clear_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'clear.svg')), '', parent)
        clear_action.setToolTip("Clear Output")
        clear_action.triggered.connect(parent.clear_output)
        toolbar.addAction(clear_action)

        # 7. SETTINGS Button (Access to settings menu)
        settings_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'settings.png')), '', parent)
        settings_action.setToolTip("Settings")
        settings_action.triggered.connect(parent.open_settings)
        toolbar.addAction(settings_action)

        # Adjust the spacer widget based on toolbar orientation
        toolbar.orientationChanged.connect(lambda orientation: parent.update_toolbar_spacer(orientation, spacer))
