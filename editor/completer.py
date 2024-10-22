try:
    import nuke  # Nuke modülünü kullanıyoruz
except:
    pass
import builtins  # Python yerleşik fonksiyonlarını almak için
import keyword  # Python anahtar kelimelerini almak için
import types  # Veri tipleri ve diğer türler için
import sys  # Python modülleri almak için
from PySide2.QtWidgets import QCompleter, QListView, QStyledItemDelegate, QStyleOptionViewItem
from PySide2.QtCore import QStringListModel, Qt, QSize
from PySide2.QtGui import QTextCursor, QFont, QIcon, QPixmap, QColor, QPainter

class CustomDelegate(QStyledItemDelegate):
    """Her item'ı özel şekilde çizerek tür bilgisi ekleyen delegate"""
    def paint(self, painter, option: QStyleOptionViewItem, index):
        painter.save()

        # Öğeyi çizelim
        super().paint(painter, option, index)

        # Tür bilgisini çizmek için item'ı ve type bilgisini alalım
        item_text = index.data()
        item_type = self.get_item_type(item_text)

        # Tür bilgisini daha koyu gri (#808080), daha küçük yazı tipiyle çizelim
        painter.setPen(QColor("#808080"))  # Tür bilgisi için daha koyu gri
        font = painter.font()
        font.setPointSize(9)  # Daha küçük yazı boyutu
        painter.setFont(font)

        # Tür bilgisini item ile üst üste gelmeyecek şekilde sağ tarafa yaslayalım
        rect = option.rect
        text_width = painter.fontMetrics().width(item_text)
        type_width = painter.fontMetrics().width(item_type)
        padding = 10  # Ana metin ve tür metni arasına biraz boşluk

        # Tür bilgisini sağa yaslayarak çizelim
        painter.drawText(rect.right() - type_width - padding, rect.y() + rect.height() / 1.5, item_type)

        painter.restore()

    def get_item_type(self, item_text):
        """Öğenin türünü belirleyelim"""
        try:
            if hasattr(nuke, item_text):
                item = getattr(nuke, item_text)
                if callable(item):
                    return "Nuke Function"
                elif isinstance(item, (nuke.Knob, nuke.Node)):
                    return "Nuke Object"
            if hasattr(builtins, item_text):
                item = getattr(builtins, item_text)
                if callable(item):
                    return "Builtin Function"
                return "Builtin Object"
            if item_text in keyword.kwlist:
                return "Keyword"
            if item_text in sys.modules:
                return "Module"
        except Exception:
            return "Unknown"
        return "Variable"

class Completer(CustomDelegate):
    def __init__(self, editor):
        self.editor = editor
        self.completer_model = QStringListModel()  # Tamamlama önerileri için model
        self.completion_popup = QCompleter(self.completer_model)  # Popup'ı model ile bağla
        self.completion_popup.setWidget(self.editor)  # Editor'ü widget olarak ayarlıyoruz
        self.completion_popup.setCompletionMode(QCompleter.PopupCompletion)  # Popup tamamlama modu
        self.completion_popup.setCaseSensitivity(Qt.CaseInsensitive)  # Büyük/küçük harfe duyarsız
        self.completion_popup.popup().setItemDelegate(CustomDelegate())  # Özel delegate ekliyoruz
        self.completion_popup.popup().setStyleSheet(self.get_popup_styles())  # Stil şeması ekliyoruz
        self.completion_popup.popup().setFont(self.get_custom_font())  # Özel yazı tipi ekliyoruz
        self.completion_popup.activated[str].connect(self.insert_completion)  # Seçilen öneriyi yakala

    def insert_completion(self, completion: str):
        """Tamamlanan metni editöre yerleştir, mevcut kelimenin üzerine yaz"""
        cursor = self.editor.textCursor()

        # İmlecin bulunduğu yerden önceki kelimeyi bulalım
        cursor.select(QTextCursor.WordUnderCursor)
        selected_word = cursor.selectedText()

        # Eğer kelime varsa, mevcut kelimeyi tamamlayıcı öneriyle değiştirelim
        if selected_word:
            cursor.removeSelectedText()  # Mevcut kelimeyi sil
            cursor.insertText(completion)  # Tamamlama önerisini yerine yerleştir
        else:
            # Kelime bulunamadıysa sadece tamamlayıcı öneriyi ekleyelim
            cursor.insertText(completion)

        self.editor.setTextCursor(cursor)
        self.completion_popup.popup().hide()  # Tamamlama yapıldıktan sonra popup'ı gizle
        print(f"Completion: {completion}")

    def get_popup_styles(self):
        """Tamamlama popup'u için stil şeması"""
        return """
            QListView {
                background-color: #3a3a3a;  /* Açık gri arka plan */
                box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.5);  /* Gölge */
                padding: 5px;
                border: 1px solid #5a5a5a;  /* Kenarlık için daha açık bir gri */
                border-radius: 10px;
            }

            QListView::item {
                padding: 1px;
                border: none;
            }

            QListView::item:hover {
                background-color: #505050;  /* Hover için daha açık gri */
            }

            QListView::item:selected {
                background-color: #a0a0a0;  /* Seçili öğe için açık gri */
                color: black;
            }

            /* Scrollbar stilleri */
            QScrollBar:vertical {
                background: #505050;  /* Scrollbar arka planı açık gri */
                width: 12px;
                border-radius: 6px;  /* Oval kenarlar */
            }

            QScrollBar::handle:vertical {
                background: #b0b0b0;  /* Handle (tutamaç) açık gri */
                min-height: 20px;
                border-radius: 6px;  /* Oval handle */
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                border: none;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar::handle:vertical:hover {
                background: #c0c0c0;  /* Hover durumunda daha açık gri */
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

        # İmlecin bulunduğu yerden önceki kelimeyi al
        cursor.select(QTextCursor.WordUnderCursor)
        current_word = cursor.selectedText()

        # Eğer boşsa tamamlama yapma
        if not current_word:
            self.completion_popup.popup().hide()
            return

        # Nuke, Python yerleşik fonksiyonları ve diğer kategorileri al
        completions = self.get_all_python_completions()

        # Mevcut kelimeyle başlayan önerileri filtrele
        filtered_completions = [comp for comp in completions if comp.startswith(current_word)]

        if filtered_completions:
            self.completer_model.setStringList(filtered_completions)  # Modeli güncelle

            # Tür bilgisi için genişliği hesapla
            max_type_width = 0
            for item in filtered_completions:
                item_type = self.get_item_type(item)  # Tür bilgisini al
                type_width = self.completion_popup.popup().fontMetrics().boundingRect(item_type).width()
                max_type_width = max(max_type_width, type_width)

            cr = self.editor.cursorRect()
            cr.setWidth(self.completion_popup.popup().sizeHintForColumn(0)
                        + self.completion_popup.popup().verticalScrollBar().sizeHint().width()
                        + max_type_width + 20)  # Tür genişliğini ve fazladan boşluk ekle
            self.completion_popup.complete(cr)  # Popup'ı göster
        else:
            self.completion_popup.popup().hide()  # Eğer tamamlama önerisi yoksa popup'ı gizle

    def get_all_python_completions(self):
        """Nuke ve Python'daki tüm kategorilerden tamamlama önerilerini al"""
        completions = []

        # 1. Nuke modülündeki tüm fonksiyonları ve knob'ları al
        try:
            for item in dir(nuke):
                if callable(getattr(nuke, item)) or isinstance(getattr(nuke, item), (nuke.Knob, nuke.Node)):
                    completions.append(item)
        except Exception as e:
            print(f"Nuke tamamlama hatası: {e}")

        # 2. Python yerleşik fonksiyonlarını ekle
        try:
            completions.extend(dir(builtins))
        except Exception as e:
            print(f"Python yerleşik fonksiyon hatası: {e}")

        # 3. Python anahtar kelimeleri
        try:
            completions.extend(keyword.kwlist)
        except Exception as e:
            print(f"Python anahtar kelime hatası: {e}")

        # 4. Python veri türleri ve özel türler
        try:
            completions.extend(dir(types))
        except Exception as e:
            print(f"Python tür hatası: {e}")

        # 5. Python özel metodlar (__init__, __str__ vs.)
        try:
            for item in dir(object):
                if item.startswith('__') and item.endswith('__'):
                    completions.append(item)
        except Exception as e:
            print(f"Özel metod hatası: {e}")

        # 6. Python dekoratörler ve async yapılar
        try:
            async_decorators = ['@staticmethod', '@classmethod', '@property', 'async def', 'await']
            completions.extend(async_decorators)
        except Exception as e:
            print(f"Dekoratör hatası: {e}")

        # 7. Python modülleri (os, sys, json, etc.)
        try:
            completions.extend(sys.modules.keys())
        except Exception as e:
            print(f"Python modül hatası: {e}")

        # 8. Python istisnaları (exceptions)
        try:
            exceptions = [exc for exc in dir(builtins) if 'Error' in exc or 'Exception' in exc]
            completions.extend(exceptions)
        except Exception as e:
            print(f"Python istisna hatası: {e}")

        return completions
