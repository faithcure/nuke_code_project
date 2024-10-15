import sys

from editor.editor_window import EditorApp


def ide_start():
    try:
        import nuke
        import nukescripts
        nuke_integration = True
        print("Python code editor running successfully.")
    except ImportError:
        print("Running from source.")
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



