import sys

from editor.editor_window import EditorApp

import sys
import os

def ide_start():
    try:
        import nuke
        import nukescripts
        nuke_integration = True
        print("Nuke integration enabled.")
    except ImportError:
        print("Runing from source.")
        nuke_integration = False

    if nuke_integration:
        window = EditorApp()
        window.show()
    else:
        # Uygulama başlatma işlemi
        from PySide2.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = EditorApp()
        window.show()
        sys.exit(app.exec_())


ide_start()
