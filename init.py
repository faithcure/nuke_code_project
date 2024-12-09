import nuke
import os

# nuke_code_project yollarını dinamik olarak tanımla
project_path = os.path.join(os.path.expanduser("~"), ".nuke", "nuke_code_project")
editor_path = os.path.join(project_path, "editor")

# Nuke plugin yolunu ayarla
nuke.pluginAddPath(editor_path)
nuke.pluginAddPath(project_path)


# Import init_ide.py
import os
exec(open(os.path.join(os.path.dirname(__file__), 'init_ide.py')).read())


# COLLECT PROJECT
nuke.pluginAddPath(os.path.join('nuke_collect_project'))