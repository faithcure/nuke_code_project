from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# Örnek Python kodu
code = """
# Bu bir yorum
class Merhaba:
    def __init__(self, isim):
        self.isim = isim

    def selamla(self):
        return f"Merhaba {self.isim}!"
"""

# Syntax Highlighting işlemi
highlighted_code = highlight(code, PythonLexer(), HtmlFormatter(full=True, style="monokai"))

# HTML çıktısını kaydet
with open("highlighted_code.html", "w", encoding="utf-8") as file:
    file.write(highlighted_code)

print("Renklendirilmiş kod HTML dosyasına yazıldı.")
