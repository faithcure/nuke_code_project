import importlib
import os.path
from PySide2.QtGui import QFont, QTextCursor, QColor
from PySide2.QtWidgets import QPlainTextEdit, QCompleter, QStyledItemDelegate, QStyleOptionViewItem, QListView, QDialog, \
    QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QGroupBox, QHBoxLayout, QListWidget
from PySide2.QtCore import QStringListModel, Qt, QObject, QModelIndex

from editor.core import PathFromOS
import json
import re
from editor.core import CodeEditorSettings
from editor.dialogs.crtNodeDialogs import show_nuke_node_creator


class RightAlignedDelegate(QStyledItemDelegate):
    def __init__(self, category_colors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_colors = category_colors  # Kategoriye göre renkleri içeren sözlük

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex):
        super().initStyleOption(option, index)
        node_name, category = index.data().split("  ")
        formatted_text = f"{node_name:<20} {category}"  # Node ismi 20 karaktere sabitlenir
        option.text = formatted_text

        # Kategoriye göre renk bilgilerini ayarla
        category_color = self.category_colors.get(category, "#ffffff")  # Renk bilgisi yoksa varsayılan beyaz
        option.palette.setColor(option.palette.Text, QColor(category_color))  # Öğeye özel renk ayarı

    def paint(self, painter, option, index):
        # Öğenin rengine göre metni çiz
        _, category = index.data().split("  ")
        color = self.category_colors.get(category, "#ffffff")
        option.palette.setColor(option.palette.Text, QColor(color))
        super().paint(painter, option, index)

class createNodeCompleter(QObject):
    def __init__(self, editor: QPlainTextEdit):
        super().__init__()

        self.editor = editor
        self.createNodeRegex = r"\bnuke\.createNode\(\s*['\"]?"  # nuke.createNode() ifadesi için REGEX

        # JSON'dan tam node listesini yükle ve kategori renklerini tanımla
        self.fullNodeList = self.load_list_nodes()
        self.category_colors = {
            "Transform": "#a57aaa",  # Örnek renkler
            "Color": "#7aa9ff",
            "Filter": "#cc804e",
            "Merge": "#4b5ec6",
            "Other": "#FFD700",
            "3D":    "#4fa15e",
        }

        # Completer ayarları
        self.completerModel = QStringListModel()
        self.completerModel.setStringList(self.fullNodeList)
        if not CodeEditorSettings().CREATE_NODE_COMPLETER:
            self.completer = None
            return  # Eğer ayar kapalıysa, sınıfı pasif hale getir
        else:
            self.completer = QCompleter(self.completerModel, self.editor)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.popup().setFont(QFont(CodeEditorSettings().main_default_font, CodeEditorSettings().main_font_size))
        self.completer.setWidget(editor)
        self.completer.activated.connect(self.insert_selected_to_cursor)
        # `CREATE_NODE_COMPLETER` ayarını kontrol et


        # Sağa yaslı kategori ve renkli item görünümü için delegate ayarlama
        delegate = RightAlignedDelegate(self.category_colors, self.completer.popup())
        self.completer.popup().setItemDelegate(delegate)

        # Popup için stil
        popup = self.completer.popup()
        popup.setStyleSheet("""
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
            }
            QScrollBar:vertical {
                background: #909090;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #b0b0b0;
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
                background: #909090;
            }
        """)

        # `textChanged` sinyalini dinle ve `check_for_create_node` fonksiyonunu çağır
        self.editor.textChanged.connect(self.check_for_create_node)

        # İlk başta tüm listeyi göstermek için bayrak
        self.show_all_nodes = False

    def load_list_nodes(self):
        """Node listesini JSON dosyasından yükle ve kategorileri ayır."""
        json_path = os.path.join(PathFromOS().json_dynamic_path, "nodeList.json")
        node_names = []
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as file:
                node_data = json.load(file)
                for node in node_data:
                    if "name" in node and "category" in node:
                        item_text = f"{node['name']}  {node['category']}"
                        node_names.append(item_text)
        return node_names

    def check_for_create_node(self):
        """nuke.createNode() ifadesini kontrol eder ve eşleşirse, girilen harfleri baz alarak filtreleme yapar."""
        cursor = self.editor.textCursor()
        line_text = cursor.block().text()

        # Eğer `nuke.createNode()` ifadesi algılandıysa
        match = re.search(self.createNodeRegex, line_text)
        if match:
            # Tüm listeyi göstermek için `rect`'i tanımla
            rect = self.editor.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0))

            # İlk defa `nuke.createNode()` ifadesi algılandığında tüm listeyi göster
            if not self.show_all_nodes:
                self.completerModel.setStringList(self.fullNodeList)  # Tüm node listesini yükle
                self.completer.setCompletionPrefix("")  # Boş prefix ile tamamlayıcıyı göster
                self.completer.complete(rect)  # Tüm listeyi göster
                self.show_all_nodes = True  # Bayrağı ayarla

            # Kullanıcı yazmaya devam ettikçe filtreleme yap
            start_pos = match.end()  # `nuke.createNode()` ifadesinin bitiş pozisyonunu al
            cursor.setPosition(cursor.block().position() + start_pos)
            cursor.select(QTextCursor.WordUnderCursor)
            current_text = cursor.selectedText().strip()

            # Eğer kullanıcı bir şey yazıyorsa, listeyi filtrele
            if current_text:
                filtered_list = [node for node in self.fullNodeList if node.lower().startswith(current_text.lower())]
                self.completerModel.setStringList(filtered_list)  # Filtrelenmiş listeyi modele yükle
                self.completer.setCompletionPrefix(current_text)
                self.completer.complete(rect)
            else:
                # Kullanıcı girişi silerse tam listeyi tekrar göster
                self.completerModel.setStringList(self.fullNodeList)
                self.completer.complete(rect)

        else:
            # `nuke.createNode()` ifadesi yoksa, bayrağı sıfırla ve popup'u kapat

            try:
                self.show_all_nodes = False
                self.completer.popup().hide()
            except:
                pass

    def insert_selected_to_cursor(self, selected_item):
        """Seçili öğeyi imlecin en yakınındaki `nuke.createNode(...)` ifadesini güncelleyerek ekler."""
        node_name = selected_item.split(" ")[0]  # Yalnızca node ismini al
        cursor = self.editor.textCursor()
        current_line_text = cursor.block().text()  # Mevcut satırdaki tüm metni al
        cursor_position = cursor.positionInBlock()  # İmlecin satırdaki pozisyonunu al

        # Tüm `nuke.createNode(...)` ifadelerini ara
        matches = list(re.finditer(self.createNodeRegex + r"[^\)]*\)", current_line_text))

        # İmlece en yakın `nuke.createNode(...)` ifadesini bul
        closest_match = None
        min_distance = float('inf')
        for match in matches:
            match_start = match.start()
            match_end = match.end()
            # İmleç pozisyonu ile ifade pozisyonu arasındaki mesafeyi hesapla
            distance = abs(cursor_position - match_start)
            if distance < min_distance:
                min_distance = distance
                closest_match = match

        if closest_match:
            # En yakın `nuke.createNode(...)` ifadesinin başlangıç ve bitiş pozisyonlarını al
            start_pos = closest_match.start()
            end_pos = closest_match.end()

            # Imleci en yakın `nuke.createNode(...)` ifadesine yerleştir ve seçili hale getir
            cursor.setPosition(cursor.block().position() + start_pos)
            cursor.setPosition(cursor.block().position() + end_pos, QTextCursor.KeepAnchor)

            # Yeni metni `nuke.createNode("Seçilen Node")` formatında ekle
            new_text = f'nuke.createNode("{node_name}")'
            cursor.insertText(new_text)  # `nuke.createNode(...)` ifadesini güncelle
        else:
            # Eğer `nuke.createNode` ifadesi yoksa, mevcut imleç konumuna yeni metin ekle
            cursor.insertText(f'nuke.createNode("{node_name}")')
            self.completer.popup().hide()

        # İmleci yeni eklenen metnin sonuna getir ve tamamlama popup'unu gizle
        self.editor.setTextCursor(cursor)
        self.completer.popup().hide()

class createNodesCode(QObject):
    def __init__(self):
        super().__init__()

        self.createNodesMenu = {
            "Create Node": lambda: self.createNodeMenu(),
            "Select All Nodes": lambda: self.selectAllNodes(),
            "Count 'by' Nodes": lambda: self.countByNodes(),
            "Change 'by' Knob(s)": lambda: self.changeByKnob(),
            "Expand Menu": lambda: self.expandMenu(),
        }

    def createNodeMenu(self):
        """
        Opens a UI for creating nodes with advanced options.
        source: dialogs/crtNodeDialogs.py
        """
        import editor.dialogs.crtNodeDialogs
        importlib.reload(editor.dialogs.crtNodeDialogs)
        from editor.dialogs.crtNodeDialogs import NukeNodeCreatorDialog
        show_nuke_node_creator()

    def selectAllNodes(self):
        print("select all")

    def countByNodes(self):
        print("count by nodes")

    def changeByKnob(self):
        print("change by knobs")

    def expandMenu(self):
        print("Expand Menu")