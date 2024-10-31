try:
    import nuke  # Nuke modülünü içe aktarmayı deniyoruz
except ImportError:
    nuke = None  # Eğer bulunamazsa, nuke değişkenini None olarak ayarla

# Standart kütüphaneler
import webbrowser  # Web tarayıcısını açmak için gerekli
import builtins  # Python yerleşik fonksiyonlarına erişim için
import keyword  # Python anahtar kelimelerini kullanmak için
import types  # Python tür bilgilerini almak için
import sys  # Python sistem modülü, modüllere erişim için
import json  # JSON dosyalarıyla çalışmak için
import os  # İşletim sistemi işlemleri için
import re  # Düzenli ifadelerle çalışmak için
from collections import deque  # Çift uçlu kuyruk yapısı (deque) için
from difflib import get_close_matches  # Yakın eşleşmeleri bulmak için

# PySide2 GUI (grafik arayüz) bileşenlerini içe aktarıyoruz
from PySide2.QtWidgets import QCompleter, QListView, QStyledItemDelegate, QStyleOptionViewItem, QLabel, QVBoxLayout, \
    QShortcut
from PySide2.QtCore import QStringListModel, Qt, QSize, QPoint
from PySide2.QtGui import QTextCursor, QFont, QColor, QPainter
from editor.core import CodeEditorSettings  # Özelleştirilmiş ayarları almak için
from PySide2.QtGui import QColor, QFont, QPainter
from PySide2.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from PySide2.QtCore import Qt
from PySide2.QtGui import QPainter, QColor


# Öğelerin tür bilgisini göstererek özel şekilde çizen delegate sınıfı
class CustomDelegate(QStyledItemDelegate):
    """Her item'ı özel şekilde çizerek tür bilgisi ekleyen delegate"""

    def __init__(self, parent=None):
        super().__init__(parent)  # Üst sınıfın (QStyledItemDelegate) init metodunu çağır

    def paint(self, painter, option: QStyleOptionViewItem, index):
        painter.save()  # Painter'in mevcut durumunu kaydet
        item_text = index.data()  # Öğenin metnini al
        item_type = self.get_item_type(item_text)  # Öğenin türünü al

        # Öğenin arka plan ve yazı rengini türüne göre belirleyelim
        painter.setPen(self.get_type_color(item_type))  # Yazı rengini belirle
        font = painter.font()
        font.setPointSize(9)  # Yazı boyutunu 9 olarak ayarla
        painter.setFont(font)  # Fontu uygula

        rect = option.rect  # Öğenin çizileceği dikdörtgen alanı al
        padding = 10  # Sağ boşluk için dolgu miktarı
        type_width = painter.fontMetrics().width(item_type)  # Tür metninin genişliğini hesapla

        # Öğeyi ve tür bilgisini çizelim
        super().paint(painter, option, index)  # Ana metni çiz
        painter.drawText(rect.right() - type_width - padding, rect.y() + rect.height() / 1.5,
                         item_type)  # Tür bilgisini sağa çiz
        painter.restore()  # Painter'in kaydedilen durumuna geri dön

    def get_popup_styles(self):
        """Tamamlama popup'u için stil şeması ve scroll bar tasarımı"""
        return """
            QListView {
                background-color: #f7f7f7;  /* Açık gri arka plan */
                box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.5);  /* Gölge */
                padding: 5px;
                border: 1px solid #cfcfcf;  /* Kenarlık için gri */
                border-radius: 10px;
            }
            QListView::item {
                padding: 2px;
                border: none;
            }
            QListView::item:hover {
                background-color: #e0e0e0;  /* Hover için açık gri */
            }
            QListView::item:selected {
                background-color: #d0d0d0;  /* Seçili öğe için daha koyu gri */
                color: black;
            }
        """

    def get_item_type(self, item_text):
        """Öğenin türünü belirleyelim"""
        try:
            # Nuke modülünde bu isimde bir öğe varsa türünü belirle
            if nuke and hasattr(nuke, item_text):
                item = getattr(nuke, item_text)
                if callable(item):
                    return "Nuke Function"  # Eğer çağrılabilirse, Nuke fonksiyonu
                elif isinstance(item, (nuke.Knob, nuke.Node)):
                    return "Nuke Object"  # Eğer düğüm veya knob ise, Nuke nesnesi
            if hasattr(builtins, item_text):  # Python yerleşik modüllerinde bu isim varsa
                item = getattr(builtins, item_text)
                if callable(item):
                    return "Builtin Function"  # Çağrılabilirse yerleşik fonksiyon
                return "Builtin Object"  # Değilse yerleşik nesne
            if item_text in keyword.kwlist:
                return "Keyword"  # Python anahtar kelimesi
            if item_text in sys.modules:
                return "Module"  # Python modülü
        except Exception:
            return "Unknown"  # Eğer hata oluşursa bilinmeyen olarak belirle
        return "Variable"  # Hiçbiri değilse değişken olarak döndür

    def get_type_color(self, item_type):
        """Türlere göre pastel renk ataması"""
        color_map = {
            "Builtin Function": QColor("#A2D9A5"),  # Pastel Yeşil
            "Builtin Object": QColor("#FFD1A9"),  # Pastel Turuncu
            "Keyword": QColor("#A9CCE3"),  # Pastel Mavi
            "Module": QColor("#D7BDE2"),  # Pastel Mor
            "Nuke Function": QColor("#F5B7B1"),  # Pastel Kırmızı
            "Nuke Object": QColor("#D5BDAC"),  # Pastel Kahverengi
            "Variable": QColor("#D5DBDB"),  # Gri
            "Unknown": QColor("#CACFD2")  # Açık Gri
        }
        return color_map.get(item_type, QColor("#FFFFFF"))  # Varsayılan olarak beyaz renk


class Completer(CustomDelegate):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor  # Tamamlama yapılacak metin editörü
        self.completer_model = QStringListModel()  # Tamamlama verisi için model
        self.completion_popup = QCompleter(self.completer_model)  # Tamamlama popup'u
        self.completion_popup.popup().setStyleSheet(self.get_popup_styles())  # Popup stilini ayarla
        self.completion_popup.setWidget(self.editor)
        self.completion_popup.setCompletionMode(QCompleter.PopupCompletion)
        self.completion_popup.setCaseSensitivity(Qt.CaseInsensitive)
        self.completion_popup.popup().setItemDelegate(CustomDelegate())  # Her öğe için özel delegate
        self.completion_popup.popup().setFont(self.get_custom_font())  # Yazı tipi
        self.completion_popup.activated[str].connect(self.insert_completion)
        self.recent_completions = deque(maxlen=10)  # Son 10 tamamlama için bir deque

        # Durum çubuğu tanımlama
        self.status_bar = QLabel("Description will appear here.")
        self.status_bar.setFixedHeight(27)
        self.status_bar.setAlignment(Qt.AlignLeft)
        self.status_bar.setStyleSheet("background-color: #4a4a4a; color: #fff; padding: 5px; font-size: 24;")

        self.current_source = None
        popup_height = self.completion_popup.popup().sizeHint().height()

        self.status_bar.mousePressEvent = self.open_help_link
        layout = QVBoxLayout(self.completion_popup.popup())
        layout.setContentsMargins(0, popup_height - self.status_bar.height(), 0, 0)
        layout.addWidget(self.completion_popup.popup())
        layout.addWidget(self.status_bar)

        self.completion_popup.popup().setMouseTracking(True)
        self.completion_popup.popup().entered.connect(self.show_item_description)



    def show_item_description(self, index):
        """Popup üzerindeki öneri metni üzerine gelindiğinde açıklamayı günceller"""
        item_text = index.data()  # Seçilen öğenin metnini al
        description = self.get_description(item_text)  # Açıklamayı al
        self.status_bar.setText(description)  # Durum çubuğuna yaz

        # Her açıklamanın kaynağını belirle
        if item_text in keyword.kwlist:
            self.current_source = "https://docs.python.org/3/reference/lexical_analysis.html#keywords"
        elif item_text in sys.modules:
            self.current_source = f"https://docs.python.org/3/library/{item_text}.html"
        else:
            self.current_source = None  # Bilinmeyen bir öğe ise kaynak yok

    def open_help_link(self, event):
        """Status bar'a tıklandığında kaynağa gitmek için bağlantıyı açar"""
        if self.current_source:
            webbrowser.open(self.current_source)

    def get_description(self, item_text):
        """Öneri için açıklama alır"""
        from editor.code_editor import PathFromOS
        # JSON dosyasından anahtar kelime açıklamalarını yükleme
        keyword_file_path = os.path.join(PathFromOS().json_path, "keywords.json")

        try:
            with open(keyword_file_path, "r", encoding="utf-8") as file:
                keyword_descriptions = json.load(file)
        except Exception as e:
            print(f"Keyword file could not be loaded: {e}")
            keyword_descriptions = {}

        try:
            # Nuke fonksiyonu veya knob kontrolü
            if hasattr(nuke, item_text):
                return getattr(nuke, item_text).__doc__ or "Nuke function or knob."

            # Yerleşik Python fonksiyonu veya nesnesi kontrolü
            elif hasattr(builtins, item_text):
                return getattr(builtins, item_text).__doc__ or "Python keyword."

            # Python anahtar kelimesi kontrolü
            elif item_text in keyword.kwlist:
                return keyword_descriptions.get(item_text, "Python anahtar kelimesi.")

            # Python modülü kontrolü
            elif item_text in sys.modules:
                module = sys.modules[item_text]
                return module.__doc__ or "No information available about the Python module."

        except Exception:
            pass

        return "Description not found."

    def insert_completion(self, completion: str):
        """Tamamlanan metni editöre yerleştir, mevcut kelimenin üzerine yaz ve geçmişi güncelle"""
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        selected_word = cursor.selectedText()

        if selected_word:
            cursor.removeSelectedText()
            cursor.insertText(completion)
        else:
            cursor.insertText(completion)

        self.editor.setTextCursor(cursor)
        self.completion_popup.popup().hide()

        if completion not in self.recent_completions:
            self.recent_completions.appendleft(completion)

    def get_popup_styles(self):
        """Tamamlama popup'u için stil şeması"""
        return """
            QListView {
                background-color: #3a3a3a;
                box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.5);
                padding: 5px;
                border: 1px solid #5a5a5a;
                border-radius: 10px;
            }
            QListView::item {
                padding: 1px;
                border: none;
            }
            QListView::item:hover {
                background-color: #505050;
            }
            QListView::item:selected {
                background-color: #a0a0a0;
                color: black;
            }/* Scrollbar stilleri */
            QScrollBar:vertical {
                background: #909090;  /* Scrollbar arka planı */
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #b0b0b0;  /* Tutamaç rengi */
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar::handle:vertical:hover {
                background: #909090;  /* Hover durumunda tutamaç rengi */
            }
        """

    def get_custom_font(self):
        """Tamamlama popup'u için özel yazı tipi"""
        custom_font = QFont()
        custom_font.setFamily("JetBrains Mono")
        custom_font.setPointSize(12)
        return custom_font



    def update_completions(self):
        """Editördeki metne göre tamamlama önerilerini al ve popup göster"""
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        current_word = cursor.selectedText()


        if not current_word or self.editor.toPlainText().strip() == "":
            self.completion_popup.popup().hide()
            return

        completions = self.get_all_python_completions()

        exact_matches = [comp for comp in completions if comp.startswith(current_word)]

        if CodeEditorSettings().ENABLE_FUZZY_COMPLETION:
            fuzzy_matches = get_close_matches(current_word, completions, n=10, cutoff=0.5)
        else:
            fuzzy_matches = []

        combined_completions = sorted(set(exact_matches + fuzzy_matches),
                                      key=lambda comp: (comp not in self.recent_completions, comp))

        if combined_completions:
            self.completer_model.setStringList(combined_completions)
            max_type_width = 0
            for item in combined_completions:
                item_type = self.get_item_type(item)
                type_width = self.completion_popup.popup().fontMetrics().boundingRect(item_type).width()
                max_type_width = max(max_type_width, type_width)

            cr = self.editor.cursorRect()
            cr.translate(35,5) # Öneri popup pozisyonu xy bazından!
            cr.setWidth(self.completion_popup.popup().sizeHintForColumn(0)
                        + self.completion_popup.popup().verticalScrollBar().sizeHint().width()
                        + max_type_width + 20)
            self.completion_popup.complete(cr)
        else:
            self.completion_popup.popup().hide()

    def extract_existing_variables(self):
        """Editördeki mevcut metinden değişkenleri, fonksiyonları ve sınıf adlarını çıkarır"""
        text = self.editor.toPlainText()

        variable_pattern = r'\b([a-zA-Z_][a-zA-Z_0-9]*)\b'
        function_pattern = r'\bdef\s+([a-zA-Z_][a-zA-Z_0-9]*)\b'
        class_pattern = r'\bclass\s+([a-zA-Z_][a-zA-Z_0-9]*)\b'

        variables = set(re.findall(variable_pattern, text))
        functions = set(re.findall(function_pattern, text))
        classes = set(re.findall(class_pattern, text))

        all_identifiers = variables.union(functions).union(classes)
        return list(all_identifiers)

    def get_all_python_completions(self):
        """Nuke ve Python'daki tüm kategorilerden ve editördeki mevcut tanımlamalardan tamamlama önerilerini al"""
        completions = []

        if nuke:
            try:
                for item in dir(nuke):
                    if callable(getattr(nuke, item)) or isinstance(getattr(nuke, item), (nuke.Knob, nuke.Node)):
                        completions.append(item)
            except Exception as e:
                print(f"Nuke tamamlama hatası: {e}")

        try:
            completions.extend(dir(builtins))
        except Exception as e:
            print(f"Python yerleşik fonksiyon hatası: {e}")

        try:
            completions.extend(keyword.kwlist)
        except Exception as e:
            print(f"Python anahtar kelime hatası: {e}")

        try:
            completions.extend(dir(types))
        except Exception as e:
            print(f"Python tür hatası: {e}")

        try:
            for item in dir(object):
                if item.startswith('__') and item.endswith('__'):
                    completions.append(item)
        except Exception as e:
            print(f"Özel metod hatası: {e}")

        try:
            async_decorators = ['@staticmethod', '@classmethod', '@property', 'async def', 'await']
            completions.extend(async_decorators)
        except Exception as e:
            print(f"Dekoratör hatası: {e}")

        try:
            completions.extend(sys.modules.keys())
        except Exception as e:
            print(f"Python modül hatası: {e}")

        try:
            exceptions = [exc for exc in dir(builtins) if 'Error' in exc or 'Exception' in exc]
            completions.extend(exceptions)
        except Exception as e:
            print(f"Python istisna hatası: {e}")

        completions.extend(self.extract_existing_variables())
        return completions
