import sys
import traceback
import io
import os
from PySide2.QtWidgets import QTextEdit
from PySide2.QtGui import QFontDatabase, QFont
from editor.core import PathFromOS

class SysOutputRedirector:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, message):
        if message.strip():  # Boş mesajları eklememek için kontrol
            self.output_widget.append_output(message)

    def flush(self):
        pass  # flush metodu sys.stdout ve sys.stderr için gerekli, ancak burada bir işlem yapmıyoruz.

def execute_python_code(code, output_widget):
    """Girilen Python kodunu çalıştır ve çıktıyı Output sekmesine yazdır."""
    old_stdout = sys.stdout  # Mevcut stdout'u kaydet
    sys.stdout = io.StringIO()  # Geçici bir StringIO nesnesi stdout olarak ayarlanır

    try:
        exec(code, {'__builtins__': __builtins__}, {})  # Kodu çalıştır
        output = sys.stdout.getvalue()  # Çıktıyı yakalar
        output_widget.append_output(output)  # Yakalanan çıktıyı Output widget'ına ekler
    except Exception as e:
        # Traceback ile hatayı yakala ve kırmızı renkte göster
        error_message = traceback.format_exc()  # Traceback'i al
        output_widget.append_error_output(error_message)  # Hata çıktısını kırmızı olarak ekle
    finally:
        sys.stdout = old_stdout  # stdout'u eski haline getir

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

        # JetBrains Mono fontunu proje dizininden yüklüyoruz
        self.load_custom_font()

    def load_custom_font(self):
        """JetBrains Mono fontunu belirlenen dizinden yükler."""
        font_path = os.path.join(PathFromOS().jet_fonts, 'JetBrainsMono-Regular.ttf')  # Font yolunu güncelledik
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Font yüklenemedi.")
        else:
            self.setFont(QFont("JetBrains Mono"))  # JetBrains Mono fontunu ayarla

    def append_output(self, message):
        """Normal çıktı mesajlarını beyaz renkte ve JetBrains Mono fontu ile ekler."""
        formatted_message = f'<pre style="color: white; font-family: \'JetBrains Mono\';">{self.add_padding(message)}</pre>'
        self.append(formatted_message)
        self.ensureCursorVisible()  # İmleci görünür yap

    def append_error_output(self, message):
        """Hata mesajlarını istediğiniz renkte (#fe8c86) ve JetBrains Mono fontu ile ekler."""
        formatted_error = "".join(
            f"<pre style='color: #fe8c86; line-height: 1.0; font-family: \"JetBrains Mono\"; margin: 0;'>{self.add_padding(line)}</pre>"
            for line in message.split("\n")
        )
        self.append(formatted_error)
        self.ensureCursorVisible()  # İmleci görünür yap

    def append_info_output(self, message):
        """Bilgi mesajlarını gri renkte ve JetBrains Mono fontu ile ekler."""
        formatted_info = f'<pre style="color: grey; font-family: \'JetBrains Mono\';">{self.add_padding(message)}</pre>'
        self.append(formatted_info)
        self.ensureCursorVisible()  # İmleci görünür yap

    def append_warning_output(self, message):
        """Uyarı mesajlarını sarı renkte ve JetBrains Mono fontu ile ekler."""
        formatted_warning = f'<pre style="color: yellow; font-family: \'JetBrains Mono\';">{self.add_padding(message)}</pre>'
        self.append(formatted_warning)
        self.ensureCursorVisible()  # İmleci görünür yap

    def add_padding(self, message, spaces=2):
        """Mesajın başına boşluk (padding) ekler."""
        padding = '&nbsp;' * spaces
        return padding + message
