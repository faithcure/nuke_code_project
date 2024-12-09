import os
import importlib.util
import nuke_collect_project

# SET PATH: nuke_code_project init_ide.py
project_dir = os.path.join(os.path.dirname(__file__), "nuke_code_project")
ide_init_path = os.path.join(project_dir, "init_ide.py")

if os.path.exists(ide_init_path):
    # init_ide.py dosyasını bir modül olarak yükle
    spec = importlib.util.spec_from_file_location("init_ide", ide_init_path)
    init_ide = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(init_ide)  # Modülü çalıştır
        # add_menu_command fonksiyonunu çağır
        if hasattr(init_ide, "add_menu_command"):
            init_ide.add_menu_command()
        else:
            print("add_menu_command function not found in init_ide.py.")
    except Exception as e:
        print(f"Error while loading init_ide.py: {e}")
else:
    print(f"init_ide.py not found in {project_dir}. Please ensure it is placed correctly.")


# NUKE COLLECT PROJECTS
menu = nuke.menu("Nuke")
tools_menu = menu.addMenu("My Tools")
def start_Collector():
    importlib.reload(nuke_collect_project)
    nuke_collect_project.start()
tools_menu.addCommand("Collect Project", "start_Collector()")
