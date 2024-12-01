import sys
import traceback
import io
import os
from PySide2.QtWidgets import QTextEdit
from PySide2.QtGui import QFontDatabase, QFont
from editor.core import PathFromOS
import logging

try:
    import nuke
    import nukescripts
except ImportError:
    print("Please open this codes with NUKE_ENV.")
    nuke = None

class DebugLogger:
    def __init__(self, log_file="debug_log.txt"):
        self.logger = logging.getLogger("DebugLogger")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message, level="info"):
        if level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)
def validate_code(code):
    try:
        compile(code, "<string>", "exec")
        return None
    except SyntaxError as e:
        return str(e)
class SysOutputRedirector:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, message):
        if message.strip():
            self.output_widget.append_output(message)

    def flush(self):
        pass

def execute_python_code(code, output_widget, debug_mode=False):
    validation_error = validate_code(code)
    if validation_error:
        output_widget.append_error_output(f"Syntax Hatası: {validation_error}")
        return

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, {'__builtins__': __builtins__}, {})
        output = sys.stdout.getvalue()
        output_widget.append_output(output)
    except Exception as e:
        error_message = traceback.format_exc()
        output_widget.append_error_output(error_message)
    finally:
        sys.stdout = old_stdout

def execute_nuke_code(code, output_widget):
    """
    Verilen Nuke kodunu çalıştırır ve sonucu output_widget'a yönlendirir.
    """
    sys.stdout = SysOutputRedirector(output_widget)
    sys.stderr = SysOutputRedirector(output_widget)

    try:
        # Nuke kodunu çalıştır
        result = nuke.executeInMainThreadWithResult(lambda: exec(code))
        if result is not None:
            print(result)
    except Exception as e:
        # Hata varsa Traceback ile Output'a yazdır
        error_message = traceback.format_exc()
        output_widget.append_error_output(error_message)
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class OutputWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_custom_font()

    def load_custom_font(self):
        font_path = os.path.join(PathFromOS().jet_fonts, 'JetBrainsMono-Regular.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Font yüklenemedi.")
        else:
            self.setFont(QFont("JetBrains Mono"))

    def append_output(self, message):
        formatted_message = f'<pre style="color: white; font-family: \'JetBrains Mono\';">{self.add_padding(message)}</pre>'
        self.append(formatted_message)
        self.ensureCursorVisible()

    def append_error_output(self, message):
        formatted_error = "".join(
            f"<pre style='color: #fe8c86; font-family: \"JetBrains Mono\";'>{self.add_padding(line)}</pre>"
            for line in message.split("\n")
        )
        self.append(formatted_error)
        self.ensureCursorVisible()

    def append_info_output(self, message):
        formatted_info = f'<pre style="color: grey; font-family: \'JetBrains Mono\';">{self.add_padding(message)}</pre>'
        self.append(formatted_info)
        self.ensureCursorVisible()

    def add_padding(self, message, spaces=2):
        padding = '&nbsp;' * spaces
        return padding + message