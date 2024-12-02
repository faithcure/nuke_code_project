import os
import sys
import json
import importlib
from PySide2.QtWidgets import QApplication

# Paths
project_dir = os.path.expanduser("~/.nuke/nuke_code_project")
modules_path = os.path.join(project_dir, "editor", "settings", "modules")
settings_path = os.path.join(project_dir, "editor", "settings", "settings.json")
sys.path.append(modules_path)  # Modules path added to sys.path

def ide_start_reload():
    """
    Start or reload the Python code editor.
    """
    from editor import editor_window
    importlib.reload(editor_window)

    EditorApp = editor_window.EditorApp
    app = QApplication.instance() or QApplication(sys.argv)

    # Bring existing editor to front or create a new one
    for widget in app.topLevelWidgets():
        if isinstance(widget, EditorApp):
            widget.raise_()
            widget.activateWindow()
            return

    window = EditorApp()
    window.show()
    window.raise_()
    window.activateWindow()

def check_startup_settings():
    """
    Check if startup_checkbox in settings.json is true and start IDE if enabled.
    """
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as file:
                settings = json.load(file)
            if settings.get("General", {}).get("startup_checkbox", False):
                print("Startup check is true")
                ide_start_reload()
            else:
                print("Startup check is disabled")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON file: {e}")
        except Exception as e:
            print(f"Error loading settings: {e}")
    else:
        print(f"Settings file not found at: {settings_path}")

def add_menu_command():
    """
    Add Python IDE command to Nuke menu.
    """
    import nuke
    my_tools_menu = nuke.menu("Nuke").addMenu("Python")
    my_tools_menu.addCommand("Python IDE", ide_start_reload)

# Run startup check
check_startup_settings()

# Automatically added modules path
import sys
sys.path.append('C:\\Users\\User\\.nuke\\nuke_code_project\\editor\\settings\\modules')
