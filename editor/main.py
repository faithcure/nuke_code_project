# main.py
import sys
import os

# Yol ekleme - modülleri doğru bulması için projenizin ana dizinini sys.path'e ekleyin
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

try:
    import nuke
    nuke_integration = True
except ImportError:
    nuke_integration = False

# PySide2 veya Nuke içindeki Qt modüllerini doğru şekilde kullanma
if nuke_integration:
    import assets.nuke
    import assets.nukescripts
    from nuke.internal.qt.QtWidgets import QApplication
else:
    from PySide2.QtWidgets import QApplication

# Kendi modüllerinizi ekleyin
from editor.editor_window import EditorApp

def run():
    # Uygulama başlatma işlemi
    app = QApplication(sys.argv)
    window = EditorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
