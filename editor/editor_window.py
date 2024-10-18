import ast
import json
import shutil
import sys
import os
import re
import webbrowser
import importlib
from functools import partial
from PySide2.QtCore import QStringListModel
from PySide2.QtGui import  QTextCharFormat, QTextCursor, QGuiApplication
from PySide2.QtGui import  QFont
from editor.code_editor import CodeEditor
from PySide2.QtWidgets import *
from editor.core import PythonHighlighter, OutputCatcher
from PySide2.QtCore import  QPropertyAnimation, QEasingCurve, Qt, QSize, QRect
from PySide2.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGraphicsDropShadowEffect, QFrame
from PySide2.QtGui import  QIcon, QColor, QPixmap, QPainter, QPainterPath, QBrush
import editor.core
importlib.reload(editor.core)
from editor.core import PathFromOS
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtCore import QPropertyAnimation, QRect, QEasingCurve, QEvent, QTimer
from PySide2.QtGui import QColor
from PySide2.QtGui import QKeyEvent

class EditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Proje kök dizinini bulmak (relative path)
        # self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Bir üst dizine çıkıyoruz
        # PathFromOS().icons_path = os.path.join(self.project_root, 'ui', 'icons')  # Proje kök dizininden 'ui/icons' klasörüne göreli yol
        # self.json_path = os.path.join(self.project_root, 'assets')  # Proje kök dizininden 'ui/icons' klasörüne göreli yol

        # Window başlık değişkeni
        self.empty_project_win_title = "Nuke Code Editor: "  # Boş ise bu isim döner
        self.setWindowTitle("Nuke Code Editor: Empty Project**")  # Open ve New project'den isim çeker
        self.setGeometry(100, 100, 1200, 800)
        qr = self.frameGeometry()
        screen = QGuiApplication.primaryScreen()
        cp = screen.availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Yeni proje ve dosya işlemleri için dizin ve dosya değişkenleri
        self.project_dir = None  # Proje dizini
        self.current_file_path = None  # Mevcut dosya

        # Status bar oluşturma
        self.status_bar = self.statusBar()  # Status bar oluşturma
        self.status_bar.showMessage("Hazır")  # İlk mesajı göster

        # Sağ tarafa replace işlemi için bir label ekleyelim
        self.replace_status_label = QLabel()
        self.status_bar.addPermanentWidget(self.replace_status_label)  # Sağ köşeye ekle
        self.replace_status_label.setText("Status")  # İlk mesaj

        # Renkleri kaydetmek için bir dictionary
        self.item_colors = {}
        self.color_settings_path = os.path.join(os.getcwd(), "assets", "item_colors.json")

        # Sekmeli düzenleyici (Tab Widget) oluşturma
        self.tab_widget = QTabWidget()
        self.python_icon = QIcon(os.path.join(PathFromOS().icons_path, 'python_tab.svg'))
        self.tab_widget.setIconSize(QSize(15, 15))

        # Kapatma butonu ve ikon ayarları
        self.close_icon = os.path.join(PathFromOS().icons_path, 'new_file.png')  # Doğru yolda olduğundan emin olun
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
            }}

            QTabBar::tab {{
                background-color: #2B2B2B;
                color: #B0B0B0;
                padding: 5px 10px;
                border: none;
                font-size: 10pt;
                padding: 5px 10px 5px 10px;  /* Üst, sağ, alt ve sol padding */
            }}

            QTabBar::tab:selected {{
                background-color: #3C3C3C;
                color: #FFFFFF;
                border-bottom: 2px solid #3C88E3;
            }}
            
            QTabBar::tab:!selected {{
                background-color: #323232;
            }}
            QTabBar::tab:hover {{
                background-color: #3C3C3C;
                color: #E0E0E0;
            }}
            
        """)

        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.ensure_tab)
        self.setCentralWidget(self.tab_widget)

        # Output kısmı
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Consolas", 10))

        # Output bölmesini alta ekleyelim
        self.create_output_dock()

        # Üst menüyü oluşturma
        self.create_menu()

        # Dockable listeler
        self.create_docks()

        # Başlangıçta boş bir "untitled.py" sekmesi açılıyor
        self.add_new_tab("untitled.py", initial_content="import nuke\nimport nukescripts")

        def add_new_tab(self, file_path, initial_content=""):
            """Yeni bir sekme oluşturur ve dosyayı yükler."""
            editor = CodeEditor()  # QPlainTextEdit yerine CodeEditor kullanıyoruz
            editor.setFont(QFont("Consolas", 12))

            # PythonHighlighter kullanarak sözdizimi renklendirme ekliyoruz
            self.highlighter = PythonHighlighter(editor.document())

            # Düzenleyicideki değişiklikler olduğunda HEADER panelini güncelle
            editor.textChanged.connect(self.update_header_tree)

            # Dosya içeriği eğer mevcutsa yüklüyoruz, yoksa varsayılan içerik ile açıyoruz
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    content = file.read()
                    editor.setPlainText(content)
            else:
                editor.setPlainText(initial_content)

            # QDockWidget içinde düzenleyiciyi oluştur
            dock = QDockWidget(os.path.basename(file_path), self)
            dock.setWidget(editor)
            dock.setFloating(True)  # Yüzer pencereli olarak ayarla
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)  # Her yöne taşınabilir

            # Ana pencereye dock widget'ı ekleyin
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)

            # dock_widgets sözlüğüne yeni dock widget'ı ekleyin
            self.dock_widgets[file_path] = dock

            # Tab başlığını "*" ile işaretleyin (eğer kaydedilmemişse)
            editor.textChanged.connect(lambda: self.mark_as_modified(dock, file_path))

        def mark_as_modified(self, dock, file_path):
            """Dosya değişiklik yapıldığında başlıkta '*' gösterir."""
            if dock.windowTitle()[-1] != '*':
                dock.setWindowTitle(f"{os.path.basename(file_path)}*")
        # Program başlarken renkleri yükle
        self.load_colors_from_file()
        # Son açılan projeler bu listeye JSON olarak atanır
        # Recent Projects ile ilgili değişkenler
        self.recent_projects_list = []  # Projeleri listelemek için boş bir liste
        self.recent_projects_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "./",  "assets", "recent_projects.json")  # Dosya yolu
        # Program başlarken recent projects listesini yükleyelim
        self.load_recent_projects()
        self.create_toolbar()  # Toolbar ekleme fonksiyonunu çağırıyoruz

    def run_code(self):
        """Aktif sekmedeki tüm kodu çalıştırır ve çıktıyı Output penceresinde gösterir."""
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            code = current_editor.toPlainText()
            self.execute_code(code)

    def run_selected_code(self, selected_code):
        """Sadece seçili olan kodu çalıştırır ve çıktıyı Output penceresinde gösterir."""
        self.execute_code(selected_code)

    def execute_code(self, code):
        """Verilen kodu çalıştırır ve çıktıyı Output penceresinde gösterir."""
        self.output_text_edit.clear()  # Önce Output penceresini temizleyelim

        try:
            # Standart çıktıyı ve hata mesajlarını yakalamak için
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = OutputCatcher(self.output_text_edit)
            sys.stderr = OutputCatcher(self.output_text_edit)

            exec(code, globals())  # Kodu çalıştır

        except Exception as e:
            self.output_text_edit.append(f"Hata: {str(e)}\n")

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def create_toolbar(self):
        """Toolbar'ı oluşturur ve gerekli butonları ekler."""

        toolbar = self.addToolBar("Main Toolbar")
        self.addToolBar(Qt.LeftToolBarArea, toolbar)  # Araç çubuğunu pencerenin sol tarafına yerleştir

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Yatay için genişler, dikey için değil

        # İkon boyutunu 60x60 piksel olarak ayarlıyoruz
        toolbar.setIconSize(QSize(30, 30))
        toolbar.setStyleSheet("QToolBar { spacing: 3px; }")
        # toolbar.setFixedHeight(40)
        # 1. RUN Butonu (Kod çalıştırmak için)
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), '', self)  # İkon ile boş bir buton
        run_action.setToolTip("Run Current Code")  # Butona tooltip ekliyoruz
        run_action.triggered.connect(self.run_code)  # Fonksiyon bağlama
        toolbar.addAction(run_action)  # Butonu toolbara ekle


        # 2. SAVE Butonu (Kod kaydetmek için)
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), '', self)  # İkon ile boş bir buton
        save_action.setToolTip("Save Current File")  # Tooltip ekliyoruz
        save_action.triggered.connect(self.save_file)  # Fonksiyon bağlama
        toolbar.addAction(save_action)  # Butonu toolbara ekle

        # 3. ARAMA Butonu (Kod içinde arama yapmak için)
        search_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), '', self)  # İkon ile boş bir buton
        search_action.setToolTip("Search in Code")  # Tooltip ekliyoruz
        search_action.triggered.connect(self.show_search_dialog)  # Fonksiyon bağlama
        toolbar.addAction(search_action)  # Butonu toolbara ekle

        # Boş widget ekleyerek butonları sağa veya alta iteceğiz (spacer)


        toolbar.addWidget(spacer)

        # 4. CLEAR Butonu (Output panelini temizlemek için)
        clear_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'clear.svg')), '', self)  # İkon ile boş bir buton
        clear_action.setToolTip("Clear Output")  # Tooltip ekliyoruz
        clear_action.triggered.connect(self.clear_output)  # Fonksiyon bağlama
        toolbar.addAction(clear_action)  # Butonu toolbara ekle

        # 5. SETTINGS Butonu (Ayarlar menüsüne erişim)
        settings_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'settings.png')), '', self)  # İkon ile boş bir buton
        settings_action.setToolTip("Settings")  # Tooltip ekliyoruz
        settings_action.triggered.connect(self.show_settings_dialog)  # Fonksiyon bağlama
        toolbar.addAction(settings_action)  # Butonu toolbara ekle

        # Toolbar yönü değiştiğinde spacer widget'inin genişlik/yükseklik politikasını değiştireceğiz
        toolbar.orientationChanged.connect(lambda orientation: self.update_toolbar_spacer(orientation, spacer))

    def clear_output(self):
        """Output panelini temizlemek için kullanılır."""
        self.output_text_edit.clear()  # Output panelindeki tüm metni temizler

    def update_toolbar_spacer(self, orientation, spacer):
        """Toolbar'ın yönüne göre spacer widget'inin genişlik/yükseklik ayarlarını değiştirir."""
        if orientation == Qt.Horizontal:
            # Yatay durumda genişliği genişletiyoruz
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        else:
            # Dikey durumda yüksekliği genişletiyoruz
            spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def show_search_dialog(self):
        """Arama diyalogu oluşturur ve sonuçları vurgular."""
        text, ok = QInputDialog.getText(self, 'Arama', 'Aranacak kelimeyi girin:')
        if ok and text:
            self.find_and_highlight(text)

    def show_settings_dialog(self):
        """Ayarlar diyalogu açılır."""
        QMessageBox.information(self, 'Ayarlar', 'Ayarlar henüz eklenmedi.')

    def find_and_highlight(self, search_term):
        """Kod düzenleyicide arama terimiyle eşleşen kelimeleri vurgular."""
        current_editor = self.tab_widget.currentWidget()  # Aktif sekmedeki düzenleyiciyi alıyoruz
        if current_editor is None:
            return  # Eğer düzenleyici yoksa fonksiyondan çık

        cursor = current_editor.textCursor()  # Düzenleyicideki imleci al
        document = current_editor.document()  # Metin belgesini al

        # Mevcut tüm vurgulamaları temizle
        current_editor.setExtraSelections([])

        # Arama sonuçlarını saklayacak bir liste oluştur
        extra_selections = []

        # Metin içinde arama yapmak için QTextCursor kullanıyoruz
        cursor.beginEditBlock()  # Düzenleyici içinde toplu değişikliklere başla

        # Arama işlemi sırasında ilerlemek için imleci en başa alıyoruz
        cursor.movePosition(QTextCursor.Start)

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))  # Vurgulama rengini sarı yapıyoruz

        # Metin içinde arama yap
        while not cursor.isNull() and not cursor.atEnd():
            cursor = document.find(search_term, cursor)
            if not cursor.isNull():
                # Arama terimi bulunduğunda vurgulama için ekstra seçim yapıyoruz
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = highlight_format
                extra_selections.append(selection)

        # Toplu değişiklikleri bitiriyoruz
        cursor.endEditBlock()

        # Sonuçları vurgulamak için düzenleyiciye setExtraSelections ile ayarlıyoruz
        current_editor.setExtraSelections(extra_selections)

    def populate_outliner_with_functions(self):
        """OUTLINER'a yalnızca sınıf ve fonksiyonları ekler, nuke.py ve nukescripts.py başlıklarını hariç tutar."""
        # Dosya yollarını belirtiyoruz
        nuke_file_path = PathFromOS().nuke_ref_path
        nukescripts_file_path = PathFromOS().nukescripts_ref_path

        # Nuke dosyalarındaki sınıf ve fonksiyonları alıyoruz
        nuke_classes = self.list_classes_from_file(nuke_file_path)
        nukescripts_classes = self.list_classes_from_file(nukescripts_file_path)

        # nuke.py ve nukescripts.py başlıkları olmadan sınıf ve metodları doğrudan Outliner'a ekliyoruz
        self.add_classes_and_functions_to_tree(nuke_classes)
        self.add_classes_and_functions_to_tree(nukescripts_classes)

    def add_classes_and_functions_to_tree(self, classes):
        """Sınıf ve fonksiyonları doğrudan Outliner'a ekler."""
        for class_name, methods in classes:
            # Sınıfı Outliner'a ekliyoruz
            class_item = QTreeWidgetItem(self.outliner_list)
            class_item.setText(0, class_name)
            class_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'C_logo.svg')))  # Sınıf ikonunu ayarlayın

            # Her sınıfın metotlarını ekliyoruz
            for method in methods:
                method_item = QTreeWidgetItem(class_item)
                method_item.setText(0, method)
                method_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'M_logo.svg')))  # Metot ikonunu ayarlayın

        # Outliner içindeki tüm öğeleri genişletiyoruz
        self.outliner_list.expandAll()

    def list_classes_from_file(self, file_path):
        """Verilen dosyadaki sınıfları ve metotları bulur, özel metotları filtreler."""
        if not os.path.exists(file_path):
            print(f"Error: {file_path} dosyası bulunamadı!")
            return []

        # Dosya içeriğini okuyor ve AST'ye dönüştürüyoruz
        with open(file_path, 'r') as file:
            file_content = file.read()
        tree = ast.parse(file_content)
        classes = []

        # AST üzerinde gezinerek sınıf ve metodları buluyoruz
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                # Sınıf içinde, __init__ gibi özel metodları filtreliyoruz
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('__')]
                classes.append((class_name, methods))

        return classes

    def create_menu(self):
        """Genişletilmiş ve yeniden düzenlenmiş menü çubuğunu oluşturur."""
        menubar = self.menuBar()
        menubar.setStyleSheet("QMenuBar { padding: 4px 4px; font-size: 8pt; }")  # Eski boyutlara geri döndürüldü

        # 1. File Menüsü
        file_menu = menubar.addMenu('File')
        self.new_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'new_project.png')),
                                          'New Project', self)
        self.new_project_action.setShortcut(QKeySequence("Ctrl+N"))
        open_project_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'open_project.png')), 'Open Project',
                                      self)
        new_file_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'new_file.png')), 'New File', self)
        new_file_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        open_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'open.png')), 'Open File', self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), 'Save', self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_as_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save_as.png')), 'Save As', self)
        exit_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'exit.png')), 'Exit', self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))

        # Preferences menü öğesini ekle
        preferences_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'settings.png')), 'Preferences', self)

        # File menüsüne eklemeler
        file_menu.addAction(self.new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addSeparator()
        file_menu.addAction(new_file_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(preferences_action)  # Preferences öğesi eklendi
        file_menu.addSeparator()
        self.recent_projects = file_menu.addMenu('Recent Projects')
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # 2. Edit Menüsü
        edit_menu = menubar.addMenu('Edit')
        undo_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'undo.png')), 'Undo', self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        redo_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'redo.png')), 'Redo', self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        find_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), 'Find', self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        replace_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'replace.png')), 'Replace', self)
        clear_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'clear.svg')), 'Clear Output', self)

        cut_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'cut.png')), 'Cut', self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        copy_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'copy.png')), 'Copy', self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        paste_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'paste.png')), 'Paste', self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))

        # Edit menüsüne eklemeler
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(find_action)
        edit_menu.addAction(replace_action)
        edit_menu.addSeparator()
        edit_menu.addAction(clear_action)

        # 3. View Menüsü (Görünüm yönetim işlemleri)
        view_menu = menubar.addMenu('View')
        zoom_in_action = QAction('Zoom In', self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_out_action = QAction('Zoom Out', self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        reset_ui_action = QAction('Reset UI', self)
        set_default_ui_action = QAction('Set Default UI', self)

        # View menüsüne eklemeler
        view_menu.addAction(zoom_in_action)
        view_menu.addAction(zoom_out_action)
        view_menu.addSeparator()
        view_menu.addAction(reset_ui_action)
        view_menu.addAction(set_default_ui_action)

        # 4. Run Menüsü
        run_menu = menubar.addMenu('Run')
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), 'Run Current Code', self)
        run_action.setShortcut(QKeySequence("F5"))
        stop_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'stop.png')), 'Stop Execution', self)
        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

        # 5. Tools Menüsü (GitHub İşlemleri ve PyCharm Bağlantısı ile)
        tools_menu = menubar.addMenu('Tools')
        live_connection_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'pycharm.png')), 'LCV PyCharm',
                                         self)

        # GitHub alt menüsü
        github_menu = tools_menu.addMenu(QIcon(os.path.join(PathFromOS().icons_path, 'github.svg')), 'GitHub')
        git_commit_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'commit.png')), 'Commit', self)
        git_push_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'push.png')), 'Push', self)
        git_pull_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'pull.png')), 'Pull', self)
        git_status_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'status.png')), 'Status', self)

        # GitHub menüsüne eklemeler
        github_menu.addAction(git_commit_action)
        github_menu.addAction(git_push_action)
        github_menu.addAction(git_pull_action)
        github_menu.addAction(git_status_action)

        tools_menu.addAction(live_connection_action)

        # 6. Help Menüsü
        help_menu = menubar.addMenu('Help')
        documentation_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'documentation.png')),
                                       'Documentation', self)
        licence_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'licence.png')), 'Licence', self)
        about_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'about.png')), 'About', self)
        update_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'update.png')), 'Update', self)

        # Help menüsüne eklemeler
        help_menu.addAction(documentation_action)
        help_menu.addAction(licence_action)
        help_menu.addAction(about_action)
        help_menu.addSeparator()  # Update üstüne ayraç eklendi
        help_menu.addAction(update_action)

        # İşlevleri Fonksiyonlara Bağlama
        self.new_project_action.triggered.connect(self.new_project_dialog)
        self.new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        new_file_action.triggered.connect(self.create_new_file_dialog)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        exit_action.triggered.connect(self.file_exit)
        find_action.triggered.connect(self.show_search_dialog)
        replace_action.triggered.connect(self.trigger_replace_in_active_editor)
        cut_action.triggered.connect(self.cut_text)
        copy_action.triggered.connect(self.copy_text)
        paste_action.triggered.connect(self.paste_text)
        clear_action.triggered.connect(self.clear_output)
        run_action.triggered.connect(self.run_code)
        stop_action.triggered.connect(self.stop_code)
        reset_ui_action.triggered.connect(self.reset_ui)
        set_default_ui_action.triggered.connect(self.set_default_ui)
        preferences_action.triggered.connect(self.open_settings)  # Settings işlevi Preferences altında

    def stop_code(self):
        # Kodun çalışmasını durdurmak için işlemleri buraya yazın
        print("Execution stopped.")

    def open_settings(self):
        # Ayarlar penceresi açılacaksa buraya kod ekleyin
        print("Settings opened.")

    def switch_theme(self):
        # Ayarlar penceresi açılacaksa buraya kod ekleyin
        print("Settings opened.")

    def new_project_dialog(self):
        self.allowed_pattern = r'^[a-zA-Z0-9_ ]+$'
        """Yeni proje oluşturmak için diyalog kutusu."""
        bg_image_path = os.path.join(PathFromOS().project_root, 'ui', 'icons', 'nuke_logo_bg_01.png')
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        new_project_dialog_size = QSize(500, 300)  # Yüksekliği artırıldı
        dialog.resize(new_project_dialog_size)

        # Gölge efekti
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(40)
        shadow_effect.setOffset(0, 12)  # Gölge aşağı kaydırıldı
        shadow_effect.setColor(QColor(0, 0, 0, 100))
        dialog.setGraphicsEffect(shadow_effect)

        # Ana layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Arka plan çerçevesi
        background_frame = QFrame(dialog)
        background_frame.setStyleSheet("""
            QFrame {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 9px;
            }
        """)

        # İçerik yerleşimi
        inner_layout = QVBoxLayout(background_frame)
        inner_layout.setContentsMargins(30, 30, 30, 20)
        layout.addWidget(background_frame)

        # İmajı yükle ve yuvarlak köşeli bir pixmap oluştur
        pixmap = QPixmap(bg_image_path)
        rounded_pixmap = QPixmap(pixmap.size())
        rounded_pixmap.fill(Qt.transparent)

        # Yuvarlak köşe maskesi uygulama
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, pixmap.width(), pixmap.height()), 9, 9)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        # Yuvarlatılmış pixmap'i image_label içinde göster
        image_label = QLabel(background_frame)
        image_label.setPixmap(rounded_pixmap)
        image_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        image_label.setFixedSize(dialog.size())

        # Başlık
        title_label = QLabel("Create New Project", background_frame)
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setStyleSheet("""
            color: #CFCFCF;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Myriad';
            border: none;
            background-color: transparent;
        """)
        inner_layout.addWidget(title_label)

        # Başlık altındaki boşluk
        inner_layout.addSpacing(20)

        # Proje ismi giriş alanı
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Enter Project Name")
        self.project_name_input.setMaxLength(20)  # Maksimum 20 karakter
        self.project_name_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E0E0E0;
                padding: 10px;
                padding-right: 40px;  /* Sağ tarafta karakter sayacı için boşluk */
                border: 1px solid #5A5A5A;
                border-radius: 8px;
            }
        """)
        inner_layout.addWidget(self.project_name_input)

        # Giriş doğrulama işlevi
        def validate_project_name():
            # İzin verilen karakterler

            if re.match(self.allowed_pattern, self.project_name_input.text()) and self.project_name_input.text() != "":
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_name_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        padding-right: 40px;
                        border: 1px solid #5A5A5A;
                        border-radius: 8px;
                    }
                """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçersiz giriş olduğunda kırmızı çerçeve
                self.project_name_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 100, 100, 0.08);
                        color: #ff9991;
                        padding: 10px;
                        padding-right: 40px;
                        border: 1px solid red;
                        border-radius: 8px;
                    }
                """)
                self.project_desc.setText("Incorrect file name!")

        self.project_name_input.textChanged.connect(validate_project_name)
        # Karakter sayacı
        char_count_label = QLabel("0/20", self.project_name_input)
        if self.project_name_input.text() == "":
            char_count_label.setText("")
        char_count_label.setStyleSheet("""
            color: rgba(160, 160, 160, 0.6);  /* %60 opaklık */
            font-size: 12px;
            border: none;
            background: transparent;
        """)
        char_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        char_count_label.setFixedSize(60, 30)

        # Karakter sayacını güncelleyen işlev
        def update_char_count():
            current_length = str(len(self.project_name_input.text()))
            current_length_count = current_length + "/20"

            char_count_label.setText(current_length_count)
            char_count_label.move(self.project_name_input.width() - 75,
                                  (self.project_name_input.height() - char_count_label.height()) // 2)

        # `textChanged` sinyali ile sayaç güncellemesi
        self.project_name_input.textChanged.connect(update_char_count)

        # QLineEdit'ler arasında ve title ile boşluk bırak
        inner_layout.addSpacing(20)

        # Proje dizini giriş alanı ve "Browse" butonu
        self.project_dir_input = QLineEdit()
        self.project_dir_input.setPlaceholderText("Select Project Directory")
        self.project_dir_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E0E0E0;
                padding: 10px;  /* Orijinal kalınlık */
                border: 1px solid #5A5A5A;
                border-radius: 8px;
            }
        """)

        # Dizin doğrulama işlevi
        def validate_project_directory():
            if not self.project_dir_input.text():
                # Dizin seçilmezse kırmızı çerçeve
                self.project_dir_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        border: 1px solid red;
                        border-radius: 8px;
                    }
                """)
            else:
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_dir_input.setStyleSheet("""
                    QLineEdit {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #E0E0E0;
                        padding: 10px;
                        border: 1px solid #5A5A5A;
                        border-radius: 8px;
                    }
                """)

        # Dizin seçimi için layout
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.project_dir_input)

        # Browse butonu
        project_dir_button = QPushButton("Browse")
        project_dir_button.setFixedHeight(self.project_dir_input.sizeHint().height())  # QLineEdit ile aynı yükseklik
        project_dir_button.setStyleSheet("""
            QPushButton {
                background-color: #4E4E4E;
                color: #FFFFFF;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6E6E6E;
            }
        """)
        dir_layout.addWidget(project_dir_button)
        inner_layout.addLayout(dir_layout)

        # Bilgilendirme metni
        self.project_desc = QLabel("Please ensure the correct information!")
        self.project_desc.setStyleSheet("""
            color: #A0A0A0;
            font-size: 11px;
            border: none;
            text-align: left;
            margin-top: 10px;
        """)
        inner_layout.addWidget(self.project_desc)

        # OK ve Cancel butonları
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # OK butonu
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #808080; /* Gri renk */
                color: #FFFFFF;
                font-family: 'Myriad';
                border-radius: 10px;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #A9A9A9; /* Daha açık gri */
            }
        """)
        button_layout.addWidget(ok_button)

        # Cancel butonu
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(80, 30)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #808080; /* Gri renk */
                color: #FFFFFF;
                font-family: 'Myriad';
                border-radius: 10px;
                font-size: 14px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #A9A9A9; /* Daha açık gri */
            }
        """)
        button_layout.addWidget(cancel_button)

        # Label ile butonlar arasında boşluk ekleyin
        inner_layout.addSpacing(20)  # Label ile buton grubu arasında boşluk
        inner_layout.addLayout(button_layout)

        # Proje dizini seçiminde "Browse" butonuna tıklama işlemi
        project_dir_button.clicked.connect(lambda: self.browse_directory(self.project_dir_input))

        # OK butonuna tıklandığında proje oluşturma işlemi
        ok_button.clicked.connect(
            lambda: self.create_new_project(self.project_name_input.text(), self.project_dir_input.text(), dialog))

        # Cancel butonuna tıklanınca dialogu kapatma işlemi
        cancel_button.clicked.connect(dialog.close)
        dialog.exec_()

    def create_new_project(self, project_name, project_directory, dialog):
        """Create a new project directory and set project_dir to the new path."""
        if not project_name.strip():
            if re.match(self.allowed_pattern, self.project_name_input.text()) and self.project_name_input.text() != "":
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_name_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 255, 255, 0.08);
                            color: #E0E0E0;
                            padding: 10px;
                            padding-right: 40px;
                            border: 1px solid #5A5A5A;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçersiz giriş olduğunda kırmızı çerçeve
                self.project_name_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 100, 100, 0.08);
                            color: #ff9991;
                            padding: 10px;
                            padding-right: 40px;
                            border: 1px solid red;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Incorrect file name!")
            return

        # Directory denetleme OK'a basıldığında
        if not project_directory.strip():
            if not self.project_dir_input.text():
                # Dizin seçilmezse kırmızı çerçeve
                self.project_dir_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 255, 255, 0.08);
                            color: #E0E0E0;
                            padding: 10px;
                            border: 1px solid red;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please ensure the correct information!")
            else:
                # Geçerli giriş olduğunda orijinal stile dön
                self.project_dir_input.setStyleSheet("""
                        QLineEdit {
                            background-color: rgba(255, 100, 100, 0.08);
                            color: #ff9991;
                            padding: 10px;
                            border: 1px solid #5A5A5A;
                            border-radius: 8px;
                        }
                    """)
                self.project_desc.setText("Please set a directory!")
            return

        # Create the new project directory
        project_path = os.path.join(project_directory, project_name)

        if os.path.exists(project_path):
            self.project_desc.setText("Project directory already exists.")
            return
        else:
            os.makedirs(project_path)

        # Set self.project_dir to the newly created project directory
        self.project_dir = project_path
        self.populate_workplace(self.project_dir)
        self.setWindowTitle(self.empty_project_win_title + os.path.basename(self.project_dir))

        # Projeyi recent_projects_list'e ekleyelim
        self.add_to_recent_projects(self.project_dir)

        # Close the dialog
        dialog.close()
    # Add the methods for Workspace menu actions


    def reset_ui(self):
        """Resets the UI layout."""
        QMessageBox.information(self, "Reset UI", "UI has been reset.")

    def set_default_ui(self):
        """Sets the default UI layout."""
        QMessageBox.information(self, "Set Default UI", "UI has been set to default.")

    def cut_text(self):
        """Aktif düzenleyicideki seçili metni keser."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.cut()

    def copy_text(self):
        """Aktif düzenleyicideki seçili metni kopyalar."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.copy()

    def paste_text(self):
        """Aktif düzenleyiciye panodaki metni yapıştırır."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.paste()

    def trigger_replace_in_active_editor(self):
        # Mevcut aktif sekmedeki editor'ü alalım
        current_editor = self.tab_widget.currentWidget()

        # Eğer aktif düzenleyici bir CodeEditor ise, onun 'replace_selected_word' fonksiyonunu çağırıyoruz
        if isinstance(current_editor, CodeEditor):
            current_editor.replace_selected_word()
        else:
            # Eğer geçerli düzenleyici CodeEditor değilse hata mesajı göster
            self.status_bar.showMessage("Lütfen bir düzenleyici sekmesi açın.", 5000)

    def update_recent_projects_menu(self):
        """Recent Projects menüsünü günceller."""
        self.recent_projects.clear()  # Menü öğelerini temizleyelim

        # Her proje için menüye bir eylem ekleyelim
        for project_path in self.recent_projects_list:
            action = QAction(project_path, self)
            # 'checked' argümanını ekleyin ve path'i lambda'ya gönderin
            action.triggered.connect(partial(self.open_project_from_path, project_path))
            self.recent_projects.addAction(action)

    def open_project_from_path(self, project_path):
        """Verilen dosya yoluna göre bir projeyi açar."""
        if os.path.exists(project_path):
            self.project_dir = project_path  # Proje dizinini güncelle
            self.populate_workplace(project_path)  # Workspace'i proje ile doldur
            self.setWindowTitle(
                self.empty_project_win_title + os.path.basename(project_path))  # Pencere başlığını güncelle
        else:
            QMessageBox.warning(self, "Hata", f"Proje dizini {project_path} mevcut değil.")

    from PySide2.QtWidgets import QGraphicsDropShadowEffect
    from PySide2.QtGui import QColor

    from PySide2.QtGui import QPixmap, QPainter, QPainterPath, QBrush
    from PySide2.QtCore import Qt, QSize, QRect


    def browse_directory(self, input_field):
        """Proje dizini seçmek için bir dizin tarayıcı aç."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            input_field.setText(directory)

    def create_output_dock(self):
        """Output bölmesini oluşturur ve alt tarafa ekler."""
        output_dock = QDockWidget("Output", self)
        output_dock.setWidget(self.output_text_edit)
        self.addDockWidget(Qt.BottomDockWidgetArea, output_dock)

    def new_project(self):
        """Yeni bir proje dizini seçer ve doğrudan dosya sistemine yansıtır."""
        # self.project_dir = QFileDialog.getExistingDirectory(self, "Proje Dizini Seç")
        if self.project_dir:
            self.populate_workplace(self.project_dir)

    def populate_workplace(self, directory):
        """Workplace'ı proje dizini ile doldurur."""
        self.workplace_tree.clear()  # Önceki dizini temizle
        root_item = QTreeWidgetItem(self.workplace_tree)
        root_item.setText(0, os.path.basename(directory))
        self.add_items_to_tree(root_item, directory)
        self.workplace_tree.expandAll()

    def add_items_to_tree(self, parent_item, directory):
        """Belirli uzantılara sahip dosyaları tree'ye ekler."""
        # İzin verilen uzantılar
        allowed_extensions = {'.py', '.txt', '.sh', '.cpp', '.png', '.jpg', '.jpeg'}

        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)

            # Eğer bir klasörse, içine girip tekrar `add_items_to_tree` çağır
            if os.path.isdir(file_path):
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, file_name)
                folder_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'folder_tree.svg')))
                self.add_items_to_tree(folder_item, file_path)
            else:
                # Dosya uzantısını kontrol et ve sadece izin verilenleri ekle
                _, extension = os.path.splitext(file_name)
                if extension.lower() in allowed_extensions:
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, file_name)
                    file_item.setData(0, Qt.UserRole, file_path)  # Sağ tık menüsü için yol bilgisi ekle

                    # Dosya tipine göre ikon ekle
                    if extension.lower() == '.py':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'python_tab.svg')))
                    elif extension.lower() == '.txt':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'text_icon.svg')))
                    elif extension.lower() == '.sh':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'shell_icon.svg')))
                    elif extension.lower() == '.cpp':
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'cpp_icon.svg')))
                    elif extension.lower() in {'.png', '.jpg', '.jpeg'}:
                        file_item.setIcon(0, QIcon(os.path.join(PathFromOS().icons_path, 'image_icon.svg')))

    def on_workplace_item_double_clicked(self, item, column):
        """Workplace'deki bir dosya çift tıklanınca dosyayı aç."""
        file_path = item.data(0, Qt.UserRole)
        if file_path and file_path.endswith(".py"):
            self.add_new_tab(file_path)

    def context_menu(self, position):
        """Sağ tıklama menüsünü oluştur."""
        menu = QMenu()
        if self.workplace_tree.topLevelItemCount() == 0:
            return None
        # 1. Explore file
        explore_file_action = QAction('Explore file', self)
        explore_file_action.triggered.connect(lambda: self.explore_file(self.workplace_tree.itemAt(position)))
        menu.addAction(explore_file_action)

        # 2. Open file
        open_file_action = QAction('Open file', self)
        open_file_action.triggered.connect(lambda: self.open_file_item(self.workplace_tree.itemAt(position)))
        menu.addAction(open_file_action)

        # 3. Set Color
        set_color_action = QAction('Set Color', self)
        set_color_action.triggered.connect(lambda: self.set_item_color(self.workplace_tree.itemAt(position)))
        menu.addAction(set_color_action)

        # Ayraç
        menu.addSeparator()

        # 4. Copy
        copy_action = QAction('Copy', self)
        copy_action.triggered.connect(lambda: self.copy_item(self.workplace_tree.itemAt(position)))
        menu.addAction(copy_action)

        # 5. Paste
        paste_action = QAction('Paste', self)

        paste_action.triggered.connect(self.paste_item)
        menu.addAction(paste_action)

        # 6. Delete file
        delete_file_action = QAction('Delete file', self)
        delete_file_action.triggered.connect(lambda: self.delete_file_item(self.workplace_tree.itemAt(position)))
        menu.addAction(delete_file_action)

        # Ayraç
        menu.addSeparator()

        # Expand All
        expand_all_action = QAction('Expand All', self)
        expand_all_action.triggered.connect(self.expand_all_items)
        menu.addAction(expand_all_action)

        # Collapse All
        collapse_all_action = QAction('Collapse All', self)
        collapse_all_action.triggered.connect(self.collapse_all_items)
        menu.addAction(collapse_all_action)

        menu.exec_(self.workplace_tree.viewport().mapToGlobal(position))

    def expand_all_items(self):
        """Workplace'daki tüm öğeleri genişletir."""
        self.workplace_tree.expandAll()

    def collapse_all_items(self):
        """Workplace'daki tüm öğeleri daraltır."""
        self.workplace_tree.collapseAll()

    def explore_file(self, item):
        # item'dan Qt.UserRole verisini alıyoruz
        file_path = item.data(0, Qt.UserRole)

        # file_path'in geçerli olup olmadığını kontrol et
        if file_path and os.path.exists(file_path):
            os.startfile(os.path.dirname(file_path))
        else:
            QMessageBox.warning(self, "Hata", "Please select sub dir or file.")


    def open_file_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.add_new_tab(file_path)
        else:
            QMessageBox.warning(self, "Hata", "Dosya mevcut değil.")

    def copy_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
        else:
            QMessageBox.warning(self, "Hata", "Kopyalanacak dosya mevcut değil.")

    def paste_item(self):
        clipboard = QApplication.clipboard()
        file_path = clipboard.text()
        if os.path.exists(file_path):
            dest_dir = self.project_dir  # Yapıştırma dizinini burada belirtin
            dest_file = os.path.join(dest_dir, os.path.basename(file_path))
            try:
                shutil.copy(file_path, dest_file)
                self.populate_workplace(self.project_dir)  # Yüklemeyi yenile
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Dosya yapıştırılamadı: {str(e)}")
        else:
            QMessageBox.warning(self, "Hata", "Yapıştırılacak dosya mevcut değil.")

    def delete_file_item(self, item):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            confirm = QMessageBox.question(self, "Sil", f"Dosya '{os.path.basename(file_path)}' silinsin mi?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    os.remove(file_path)
                    self.populate_workplace(self.project_dir)  # Workspace'i güncelle
                except Exception as e:
                    QMessageBox.warning(self, "Hata", f"Dosya silinemedi: {str(e)}")
        else:
            QMessageBox.warning(self, "Hata", "Silinecek dosya mevcut değil.")

    def set_item_color(self, item):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_item_color(item, color)  # Bu satırı kullanarak rengi güncelle ve kaydet

    def save_colors_to_file(self):
        """Renkleri JSON dosyasına kaydet."""
        try:
            with open(self.color_settings_path, 'w') as file:
                json.dump(self.item_colors, file)
        except Exception as e:
            print(f"Error saving colors: {e}")

    def load_colors_from_file(self):
        """Item renklerini JSON dosyasından yükler."""
        if os.path.exists(self.color_settings_path):
            with open(self.color_settings_path, 'r') as file:
                self.item_colors = json.load(file)

            # Ağaçtaki renkleri geri yüklemek için
            def apply_color_to_item(item):
                file_path = item.data(0, Qt.UserRole)
                if file_path in self.item_colors:
                    color = QColor(self.item_colors[file_path])
                    item.setBackground(0, QBrush(color))

            # Tüm öğeleri dolaşarak renkleri uygula
            def iterate_tree_items(item):
                apply_color_to_item(item)
                for i in range(item.childCount()):
                    iterate_tree_items(item.child(i))

            iterate_tree_items(self.workplace_tree.invisibleRootItem())

    def update_item_color(self, item, color):
        file_path = item.data(0, Qt.UserRole)  # Dosya yolunu al
        if file_path:  # Eğer dosya yolu geçerliyse
            # Rengi kaydet
            self.item_colors[file_path] = color.name()  # Renk bilgisini kaydet (örn. '#RRGGBB')
            # Öğenin arka plan rengini değiştir
            item.setBackground(0, QBrush(color))
            # Değişiklikleri hemen kaydet
            self.save_colors_to_file()

    def new_file(self):
        """Yeni Python dosyası oluşturur."""
        if not self.project_dir:
            QMessageBox.warning(self, "Save Error", "Project directory is not set.")
            return
        self.add_new_tab("untitled.py")

    def load_suggestions(self):
        # suggestions.json'dan önerileri yükler
        with open(PathFromOS().json_path + "/suggestions.json", "r") as file:
            data = json.load(file)
        return data.get("suggestions", [])
        print (PathFromOS().json_path + "/suggestions.json")

    def create_new_file_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setAttribute(Qt.WA_TranslucentBackground)
        dialog.setModal(True)
        dialog.resize(500, 80)

        # Pencereyi ortalamak
        qr = dialog.frameGeometry()
        qr.moveCenter(self.frameGeometry().center())
        dialog.move(qr.topLeft())

        # Gölge efekti
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(30)
        shadow_effect.setOffset(0, 8)
        shadow_effect.setColor(QColor(0, 0, 0, 150))
        dialog.setGraphicsEffect(shadow_effect)

        # Ana layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        # Ana pencere çerçevesine (input_frame) sadece stroke ekliyoruz
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(48, 48, 48, 230); /* Saydam koyu arka plan */
                border: 1px solid rgba(80, 80, 80, 200); /* Kenarlık sadece çerçevede */
                border-radius: 10px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(input_frame)

        # Python logosu (Kenarlık olmadan, saydamlık ile)
        icon_label = QLabel()
        python_icon_path = os.path.join(PathFromOS().icons_path, "python_logo.png")
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.5)
        python_icon = QPixmap(python_icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(python_icon)
        icon_label.setGraphicsEffect(opacity_effect)
        icon_label.setFixedSize(30, 30)
        icon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        input_layout.addWidget(icon_label)

        # Dosya adı giriş alanı ve stil ayarları
        file_name_input = QLineEdit()
        file_name_input.setPlaceholderText("Enter file name (e.g., example)")
        file_name_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: rgba(128, 128, 128, 1); /* Normal yazı rengi gri */
                border: none;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5); /* Placeholder %50 saydam beyaz */
            }
        """)
        input_layout.addWidget(file_name_input)

        # Öneriler veya hata mesajı için dinamik alan (sağa yaslanmış, ortalanmış, %50 transparan)
        suggestion_label = QLabel("No suggestions.")
        suggestion_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Sağa yasla ve yukarıdan/aşağıdan ortala
        suggestion_label.setStyleSheet(
            "color: rgba(255, 165, 0, 0.5); border: none;")  # Turuncu ve %50 transparan, kenar çizgisi yok
        suggestion_label.setFixedWidth(200)  # Genişliği ayarla
        input_layout.addWidget(suggestion_label)

        # JSON'dan önerileri yükle
        suggestions = self.load_suggestions()

        # Dinamik öneri ve hata mesajı işlevi
        def on_text_changed():
            text = file_name_input.text()
            suggestion_label.setStyleSheet(
                "color: rgba(255, 165, 0, 0.5); border: none;")  # Öneri için turuncu %50 transparan

            # Uygun bir öneri bul
            found_suggestion = None
            for suggestion in suggestions:
                if suggestion.lower().startswith(text.lower()) and suggestion.lower() != text.lower():
                    found_suggestion = suggestion
                    break

            # Öneri veya hata mesajını güncelle
            if found_suggestion:
                suggestion_label.setText(found_suggestion)
            elif not is_valid_file_name(text):
                suggestion_label.setText("Invalid file name")
                suggestion_label.setStyleSheet(
                    "color: rgba(255, 94, 94, 1); border: none;")  # Hata mesajı için kırmızı %50 transparan
            else:
                suggestion_label.setText("")

        # Tamamlama için Tab tuşuna basıldığında öneriyi kabul et
        def complete_text():
            if suggestion_label.text() != "Invalid file name" and suggestion_label.text() != "":
                file_name_input.setText(suggestion_label.text())
                suggestion_label.setText("")

        file_name_input.textChanged.connect(on_text_changed)
        file_name_input.editingFinished.connect(complete_text)

        # Onay butonu (beyaz renkte, basılıyken gri)
        create_button = QPushButton()
        confirm_icon_path = os.path.join(PathFromOS().icons_path, "confirm_icon.png")
        create_button.setIcon(QIcon(confirm_icon_path))
        create_button.setFixedSize(30, 30)
        create_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 15px;
                color: #FFFFFF; /* Beyaz */
            }
            QPushButton:hover {
                opacity: 0.8;
            }
        """)
        input_layout.addWidget(create_button)

        # Dosya adı doğrulama fonksiyonu
        def is_valid_file_name(file_name):
            # Dosya adı boşluk, özel karakter içeremez
            return re.match(r'^[\w-]+$', file_name) is not None

        # Onay butonuna tıklama işlevi
        def on_create_clicked():
            file_name = file_name_input.text().strip()
            if not is_valid_file_name(file_name):
                suggestion_label.setText("Invalid file name")
                suggestion_label.setStyleSheet(
                    "color: rgba(255, 0, 0, 0.5); border: none;")  # Hata rengi %50 transparan
            else:
                self.create_file(file_name, dialog)

        create_button.clicked.connect(on_create_clicked)

        # Pencereyi saydamdan görünür hale getirme animasyonu
        dialog.setWindowOpacity(0)
        fade_in = QPropertyAnimation(dialog, b"windowOpacity")
        fade_in.setDuration(400)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        fade_in.start()

        # Diyalog gösterimi
        dialog.exec_()

    def create_file(self, file_name, dialog):
        # Proje dizini kontrolü
        if not self.project_dir:
            QMessageBox.warning(self, "No Project Directory", "Please open or create a project before saving files.")
            return

        # Dosya adı Python kurallarına uygun mu kontrol etme
        if not file_name.endswith(".py"):
            file_name += ".py"

        if not self.is_valid_python_identifier(file_name[:-3]):
            QMessageBox.warning(self, "Invalid File Name", "The file name must follow Python naming conventions!")
            return

        full_path = os.path.join(self.project_dir, file_name)
        with open(full_path, 'w') as file:
            file.write("# New Python file\n")

        self.add_new_tab(full_path)  # Yeni dosya ile bir sekme aç
        self.populate_workplace(self.project_dir)  # "Workplace" görünümünü güncelle
        dialog.close()

    def add_new_tab(self, file_path, initial_content=""):
        """Yeni bir sekme oluşturur ve dosyayı yükler."""
        editor = CodeEditor()  # QPlainTextEdit yerine CodeEditor kullanıyoruz
        editor.setFont(QFont("Consolas", 12))

        # PythonHighlighter kullanarak sözdizimi renklendirme ekliyoruz
        self.highlighter = PythonHighlighter(editor.document())

        # Düzenleyicideki değişiklikler olduğunda HEADER panelini güncelle
        editor.textChanged.connect(self.update_header_tree)  # Direkt editor widget'ine bağlama yaptık

        # Dosya içeriği eğer mevcutsa yüklüyoruz, yoksa varsayılan içerik ile açıyoruz
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                editor.setPlainText(content)
        else:
            editor.setPlainText(initial_content)

        editor.textChanged.connect(lambda: self.mark_as_modified(editor))

        self.tab_widget.addTab(editor, self.python_icon, os.path.basename(file_path))
        self.tab_widget.setCurrentWidget(editor)

    def mark_as_modified(self, editor):
        """Eğer sekmedeki dosya kaydedilmemişse, başlıkta '*' gösterir."""
        index = self.tab_widget.indexOf(editor)
        if index != -1:
            tab_title = self.tab_widget.tabText(index)
            if not tab_title.startswith("*"):
                self.tab_widget.setTabText(index, "*" + tab_title)

    def run_code(self):
        """Aktif sekmedeki kodu çalıştırır ve çıktıyı Output penceresinde gösterir."""
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            code = current_editor.toPlainText()
            try:
                exec(code)  # Bu basit bir şekilde Python kodunu çalıştırır
                self.output_text_edit.append("Kod başarıyla çalıştırıldı.\n")
            except Exception as e:
                self.output_text_edit.append(f"Hata: {str(e)}\n")

    def open_project(self):
        """Open an existing project and set self.project_dir to the selected directory."""
        project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if project_path:
            self.project_dir = project_path
            self.populate_workplace(project_path)
            self.setWindowTitle(self.empty_project_win_title + os.path.basename(project_path))

            # Projeyi recent_projects_list'e ekleyelim
            self.add_to_recent_projects(self.project_dir)

    def add_to_recent_projects(self, project_path):
        """Projeyi recent projects listesine ekler."""
        # Eğer proje zaten listede varsa çıkaralım
        if project_path in self.recent_projects_list:
            self.recent_projects_list.remove(project_path)

        # En başa ekleyelim
        self.recent_projects_list.insert(0, project_path)

        # Eğer 7'den fazla proje varsa, en son projeyi çıkaralım
        if len(self.recent_projects_list) > 7:
            self.recent_projects_list.pop()

        # Listeyi güncelle ve dosyaya kaydet
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def add_to_recent_projects(self, project_path):
        """Projeyi recent projects listesine ekler."""
        # Eğer proje zaten listede varsa çıkaralım
        if project_path in self.recent_projects_list:
            self.recent_projects_list.remove(project_path)

        # En başa ekleyelim
        self.recent_projects_list.insert(0, project_path)

        # Eğer 7'den fazla proje varsa, en son projeyi çıkaralım
        if len(self.recent_projects_list) > 7:
            self.recent_projects_list.pop()

        # Listeyi güncelle ve dosyaya kaydet
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def open_project_from_path(self, project_path):
        """Verilen dosya yoluna göre bir projeyi açar."""
        if os.path.exists(project_path):
            self.project_dir = project_path
            self.populate_workplace(project_path)
            self.setWindowTitle(self.empty_project_win_title + os.path.basename(project_path))
        else:
            QMessageBox.warning(self, "Error", f"Project directory {project_path} does not exist.")

    def save_recent_projects(self):
        """Recent Projects listesini JSON dosyasına kaydeder."""
        try:
            with open(self.recent_projects_path, 'w') as file:
                json.dump(self.recent_projects_list, file)
        except Exception as e:
            print(f"Error saving recent projects: {e}")

    def load_recent_projects(self):
        """Recent Projects listesini JSON dosyasından yükler."""
        if os.path.exists(self.recent_projects_path):
            try:
                with open(self.recent_projects_path, 'r') as file:
                    self.recent_projects_list = json.load(file)
            except Exception as e:
                print(f"Error loading recent projects: {e}")

        # Menüde göstermek için listeyi güncelle
        self.update_recent_projects_menu()

    def open_file(self):
        """Dosya açma işlemi."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "Python Dosyaları (*.py);;Tüm Dosyalar (*)")
        if file_name:
            self.add_new_tab(file_name)

    def save_file(self):
        """Save the current file."""
        if self.project_dir is None:
            QMessageBox.warning(self, "Save projects",
                                "Please create and save the python file.\nThere is no opened project currently this project is empty\nIf you want to do nothing please discard.")
            return

        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            index = self.tab_widget.indexOf(current_editor)
            if index != -1:
                tab_title = self.tab_widget.tabText(index).replace("*", "")
                file_path = os.path.join(self.project_dir, tab_title)  # Ensure project_dir is not None
                with open(file_path, 'w') as file:
                    file.write(current_editor.toPlainText())
                self.tab_widget.setTabText(index, tab_title)

    def save_file_as(self):
        """Dosyayı farklı bir yola kaydeder."""
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            file_name, _ = QFileDialog.getSaveFileName(self, "Dosya Kaydet", "",
                                                       "Python Dosyaları (*.py);;Tüm Dosyalar (*)")
            if file_name:
                with open(file_name, 'w') as file:
                    file.write(current_editor.toPlainText())
                index = self.tab_widget.indexOf(current_editor)
                self.tab_widget.setTabText(index, os.path.basename(file_name))

    def close_tab(self, index):
        """Bir sekmeyi kapatmadan önce kontrol eder."""
        editor = self.tab_widget.widget(index)

        if editor.document().isModified():
            # Eğer sekmede kaydedilmemiş değişiklikler varsa kullanıcıya soralım
            response = self.prompt_save_changes(editor)

            if response == QMessageBox.Save:
                self.save_file()
                self.tab_widget.removeTab(index)  # Dosya kaydedildiyse tabı kapat
            elif response == QMessageBox.Discard:
                self.tab_widget.removeTab(index)  # Kaydetmeden kapat
            elif response == QMessageBox.Cancel:
                return  # İptal edildiğinde hiçbir işlem yapma

        else:
            self.tab_widget.removeTab(index)  # Değişiklik yoksa doğrudan kapat

    def closeEvent(self, event):
        """Uygulamayı kapatmadan önce kaydedilmemiş değişiklikleri kontrol eder."""
        response = self.prompt_save_changes()

        # Eğer kaydedilmemiş dosya yoksa, mesaj gösterilmez ve direkt kapatılır
        if response is None:
            event.accept()
            return

        # Kaydedilmemiş dosyalar varsa soruları soralım
        if response == QMessageBox.Save:
            self.save_all_files()
            event.accept()
        elif response == QMessageBox.Discard:
            event.accept()  # Kaydetmeden çık
        elif response == QMessageBox.Cancel:
            event.ignore()  # Çıkışı iptal et

    def prompt_save_changes(self, editor=None):
        """Kaydedilmemiş değişiklikler için bir uyarı gösterir ve kullanıcıdan giriş alır."""
        unsaved_files = []

        # Eğer belirli bir editördeki kaydedilmemiş değişiklik kontrol ediliyorsa, onun adını ekle
        if editor:
            if editor.document().isModified():
                unsaved_files.append(self.tab_widget.tabText(self.tab_widget.indexOf(editor)))
        else:
            # Tüm kaydedilmemiş dosyaların listesini alalım
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if editor.document().isModified():
                    tab_title = self.tab_widget.tabText(i)
                    unsaved_files.append(tab_title)

        # Eğer kaydedilmemiş dosya yoksa None döndür ve mesaj göstermeden devam et
        if not unsaved_files:
            return None

        # Kaydedilmemiş dosyalar varsa mesajı oluştur
        message = "Yapılan son değişiklikleri kaydetmediniz.\nKaydedilmemiş dosyalar:\n"
        message += "\n".join(f"- {file}" for file in unsaved_files)

        # Kaydetme, kaydetmeden çıkma ve iptal seçeneklerini sunalım
        response = QMessageBox.question(
            self,
            "Kaydedilmemiş Değişiklikler",
            message,
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        return response

    def file_exit(self):
        """File > Exit tıklandığında kaydedilmemiş dosyaları kontrol eder ve işlemi kapatır."""
        response = self.prompt_save_changes()

        # Eğer kaydedilmemiş dosya yoksa, uygulamayı kapat
        if response is None:
            self.close()
            return

        # Kaydedilmemiş dosyalar varsa kullanıcıya soralım
        if response == QMessageBox.Save:
            self.save_all_files()
            self.close()
        elif response == QMessageBox.Discard:
            self.close()  # Kaydetmeden çık
        elif response == QMessageBox.Cancel:
            pass  # İptal edildi, hiçbir şey yapma

    def save_all_files(self):
        """Tüm açık sekmelerdeki dosyaları kaydeder."""
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.document().isModified():
                self.save_file()

    def ensure_tab(self):
        """Eğer tüm tablar kapanmışsa, yeni bir 'untitled.py' tabı aç."""
        if self.tab_widget.count() == 0:
            self.add_new_tab("untitled.py", initial_content="import nuke\nimport nukescripts")

    def close_app(self):
        """Programı kapatır."""
        reply = QMessageBox.question(self, 'Çıkış',
                                     "Kaydedilmemiş değişiklikler mevcut. Yine de çıkmak istiyor musunuz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()

    from PySide2.QtWidgets import QDockWidget, QLabel, QTreeWidget, QVBoxLayout, QHBoxLayout, QWidget
    from PySide2.QtGui import QFont, QPixmap
    from PySide2.QtCore import Qt

    def create_docks(self):
        """Sol tarafa dockable listeleri ekler."""
        # Workplace dock widget
        self.workplace_dock = QDockWidget("", self)
        expand_icon_path = os.path.join(PathFromOS().icons_path, 'expand_icon.svg')
        collapse_icon_path = os.path.join(PathFromOS().icons_path, 'collapse_icon.svg')

        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderHidden(True)
        self.workplace_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.workplace_tree.customContextMenuRequested.connect(self.context_menu)
        self.workplace_tree.itemDoubleClicked.connect(self.on_workplace_item_double_clicked)
        self.workplace_dock.setWidget(self.workplace_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.workplace_dock)
        self.workplace_tree.setAlternatingRowColors(True)

        # Başlık oluşturma
        self.create_dock_title("WORKSPACE", self.workplace_dock, expand_icon_path, collapse_icon_path)

        # OUTLINER ve HEADER widget'larını oluşturma
        self.create_outliner_dock(expand_icon_path, collapse_icon_path)
        self.create_header_dock(expand_icon_path, collapse_icon_path)

    def create_dock_title(self, title, dock_widget, expand_icon_path, collapse_icon_path):
        """Dock widget başlığını özelleştirme ve collapse/expand işlevi ekleme."""
        title_widget = QWidget()
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(5, 5, 5, 5)

        # İkon ve toggle işlemi için QLabel
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(expand_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.mousePressEvent = lambda event: self.toggle_dock_widget(dock_widget, icon_label, expand_icon_path,
                                                                           collapse_icon_path)

        # Başlık metni
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignVCenter)
        font = QFont("Arial", 10, QFont.Bold)
        title_label.setFont(font)

        # Layout ekleme
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_widget.setLayout(title_layout)

        dock_widget.setTitleBarWidget(title_widget)

    def toggle_dock_widget(self, dock_widget, icon_label, expand_icon_path, collapse_icon_path):
        """Dock widget'ı collapse/expand yapma fonksiyonu."""
        is_collapsed = dock_widget.maximumHeight() == 30
        if is_collapsed:
            dock_widget.setMinimumHeight(200)
            dock_widget.setMaximumHeight(16777215)
            icon_label.setPixmap(
                QPixmap(collapse_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            dock_widget.setMinimumHeight(30)
            dock_widget.setMaximumHeight(30)
            icon_label.setPixmap(QPixmap(expand_icon_path).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def create_outliner_dock(self, expand_icon_path, collapse_icon_path):
        """OUTLINER dock widget'ını oluşturur ve başlığı özelleştirir."""
        self.outliner_dock = QDockWidget("", self)
        outliner_widget = QWidget()
        outliner_layout = QVBoxLayout(outliner_widget)

        # OUTLINER QTreeWidget tanımla
        self.outliner_list = QTreeWidget()
        self.outliner_list.setHeaderHidden(True)  # Başlığı gizle
        self.outliner_list.setAlternatingRowColors(False)
        self.outliner_list.setStyleSheet("""
            QTreeWidget {
                background-color: #2B2B2B;
                border: none;
            }
        """)

        # Arama çubuğu için bir widget ve layout oluştur
        self.search_widget = QWidget()
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_widget.setFixedHeight(25)  # Arama çubuğu yüksekliği
        self.search_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(60, 60, 60, 0.8); /* Yarı saydam arka plan */
                border-radius: 8px;
            }
        """)
        self.search_widget.setVisible(False)  # Başlangıçta gizli olacak

        # Arama çubuğunu ekleyelim
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 60, 60, 0.8); /* Yarı saydam arka plan */
                border: none;
                color: #FFFFFF;
                padding-left: 5px;
                height: 20px;  /* QLineEdit yüksekliği */
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5); /* Yarı saydam placeholder */
            }
        """)
        self.search_bar.textChanged.connect(self.filter_outliner)
        search_layout.addWidget(self.search_bar)

        # OUTLINER widget'ını layout'a ekleyin
        outliner_layout.addWidget(self.outliner_list)
        outliner_layout.addWidget(self.search_widget)  # Arama çubuğu alta ekleniyor

        # OUTLINER widget'ını Outliner dock'a bağla
        self.outliner_dock.setWidget(outliner_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.outliner_dock)
        self.populate_outliner_with_functions()
        # Sağ tıklama menüsü ekle (Context Menu)
        self.outliner_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outliner_list.customContextMenuRequested.connect(self.context_menu_outliner)
        # OUTLINER başlık stilini oluştur ve arama ikonunu ekle
        self.create_custom_dock_title("OUTLINER", self.outliner_dock, expand_icon_path, collapse_icon_path)

        # Arama çubuğunu gösterme ve gizleme için animasyonlar
        self.search_animation_show = QPropertyAnimation(self.search_widget, b"maximumHeight")
        self.search_animation_hide = QPropertyAnimation(self.search_widget, b"maximumHeight")

        # Animasyon durumu kontrolü için bayrak
        self.search_bar_visible = False  # Çubuğun görünürlüğünü kontrol eden bayrak

    def create_custom_dock_title(self, title, dock_widget, expand_icon_path, collapse_icon_path):
        """OUTLINER başlığını özelleştirir, simge ve arama ikonunu ekler."""
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Sol tarafa ikonu ekleyelim
        expand_icon_label = QLabel()
        expand_icon_label.setPixmap(QPixmap(expand_icon_path).scaled(16, 16, Qt.KeepAspectRatio,
                                                                     Qt.SmoothTransformation))
        title_layout.addWidget(expand_icon_label)

        # OUTLINER başlık yazısı
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        title_layout.addWidget(title_label)

        title_layout.addStretch(1)  # Başlığı sola yaslamak için araya boşluk ekle

        # Sağ tarafa arama ikonunu ekleyelim
        search_icon_label = QLabel()
        search_icon_label.setPixmap(
            QPixmap(os.path.join(PathFromOS().icons_path, "find.svg")).scaled(16, 16, Qt.KeepAspectRatio,
                                                                                Qt.SmoothTransformation))
        search_icon_label.setStyleSheet("QLabel { padding: 5px; cursor: pointer; }")
        search_icon_label.mousePressEvent = self.toggle_search_bar  # İkona tıklandığında arama çubuğunu aç/kapa
        title_layout.addWidget(search_icon_label)

        # Özel başlık widget'ını dock'un başlığı olarak ayarla
        title_bar.setLayout(title_layout)
        dock_widget.setTitleBarWidget(title_bar)

    def toggle_search_bar(self, event):
        """Arama çubuğunu aç/kapa."""
        if not self.search_bar_visible:
            self.show_search_bar(event)
        else:
            self.hide_search_bar(event)

    def show_search_bar(self, event):
        """Arama çubuğunu kayarak göster."""
        if not self.search_bar_visible:
            # Arama çubuğunun açılması için animasyon ayarları
            self.search_animation_show.setDuration(300)
            self.search_animation_show.setStartValue(0)  # Gizli başlıyor
            self.search_animation_show.setEndValue(25)  # Arama çubuğunun tam yüksekliği
            self.search_animation_show.setEasingCurve(QEasingCurve.OutQuad)
            self.search_widget.setVisible(True)  # Arama widget'ını görünür yap
            self.search_animation_show.start()

            # Çubuğun şu an görünür olduğunu işaretleyelim
            self.search_bar_visible = True

    def hide_search_bar(self, event):
        """Arama çubuğunu kayarak gizle."""
        if self.search_bar_visible:
            # Arama çubuğunun kapanması için animasyon ayarları
            self.search_animation_hide.setDuration(300)
            self.search_animation_hide.setStartValue(25)  # Tam yükseklikten başlıyor
            self.search_animation_hide.setEndValue(0)  # Gizli sonlanıyor
            self.search_animation_hide.setEasingCurve(QEasingCurve.InQuad)
            self.search_animation_hide.start()
            self.search_animation_hide.finished.connect(
                lambda: self.search_widget.setVisible(False))  # Animasyon bitince gizle

            # Çubuğun şu an gizlendiğini işaretleyelim
            self.search_bar_visible = False

    def create_header_dock(self, expand_icon_path, collapse_icon_path):
        """HEADER dock widget'ını oluşturur."""
        self.header_dock = QDockWidget("HEADER", self)
        self.header_tree = QTreeWidget()
        self.header_tree.setHeaderLabels(["Element", "Type"])
        self.header_dock.setWidget(self.header_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.header_dock)

        self.header_tree.itemClicked.connect(self.go_to_line_from_header)

        # HEADER başlığı için özel widget
        self.create_dock_title("HEADER", self.header_dock, expand_icon_path, collapse_icon_path)

    def update_header_tree(self):
        """QPlainTextEdit içindeki metni analiz edip sınıf ve fonksiyonları HEADER'a ekler."""
        self.header_tree.clear()  # Eski öğeleri temizliyoruz

        current_editor = self.tab_widget.currentWidget()
        if current_editor is None:
            return  # Aktif bir düzenleyici yoksa fonksiyondan çıkın

        code = current_editor.toPlainText()  # Düzenleyicideki tüm metni alıyoruz

        try:
            tree = ast.parse(code)  # Python kodunu AST'ye çeviriyoruz
        except (SyntaxError, IndentationError):
            # Eğer kod geçerli değilse, HEADER'ı güncellemeyin
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):  # Eğer sınıf tanımıysa
                class_item = QTreeWidgetItem(self.header_tree)
                class_item.setText(0, node.name)  # Sınıf ismi
                class_item.setText(1, "Class")  # Türü
                class_item.setIcon(0, QIcon("icons/class_icon.png"))  # Sınıf için ikon

                # Sınıfın satır numarasını tutuyoruz
                class_item.setData(0, Qt.UserRole, node.lineno)

                # Sınıfın metodlarını ekleyelim
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        method_item = QTreeWidgetItem(class_item)
                        method_item.setText(0, sub_node.name)
                        method_item.setText(1, "Method")
                        method_item.setIcon(0, QIcon("icons/method_icon.png"))  # Fonksiyon için ikon
                        method_item.setData(0, Qt.UserRole, sub_node.lineno)

            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.ClassDef):
                # Eğer sınıf dışı bir fonksiyon tanımıysa doğrudan ekleyelim
                func_item = QTreeWidgetItem(self.header_tree)
                func_item.setText(0, node.name)  # Fonksiyon ismi
                func_item.setText(1, "Function")
                func_item.setIcon(0, QIcon("icons/function_icon.png"))  # Fonksiyon için ikon
                func_item.setData(0, Qt.UserRole, node.lineno)

    def go_to_line_from_header(self, item, column):
        """HEADER'da bir öğeye tıklandığında ilgili satıra gitme işlemi."""
        line_number = item.data(0, Qt.UserRole)  # Satır numarası verisini alıyoruz
        if line_number is not None:
            cursor = self.tab_widget.currentWidget().textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)  # Satıra gitme
            self.tab_widget.currentWidget().setTextCursor(cursor)
            self.tab_widget.currentWidget().setFocus()

    def insert_into_editor(self, item, column):
        """OUTLINER'da çift tıklanan öğeyi aktif metin düzenleyiciye ekler."""
        # Seçilen sınıf ya da fonksiyon adını al
        selected_text = item.text(0)

        # Aktif düzenleyiciye eriş
        current_editor = self.tab_widget.currentWidget()

        if current_editor:  # Eğer düzenleyici varsa
            cursor = current_editor.textCursor()  # Düzenleyicinin imlecini al

            # Metni imlecin olduğu yere ekleyelim ve bir boşluk ekleyelim
            cursor.insertText(selected_text + ' ')  # Metni ekledikten sonra bir boşluk ekler

            # İmleci güncelle
            current_editor.setTextCursor(cursor)

    def context_menu_outliner(self, position):
        """OUTLINER'da sağ tıklama menüsü oluşturur."""
        item = self.outliner_list.itemAt(position)
        if item is None:
            return

        menu = QMenu()

        # "Insert the Code" seçeneği
        insert_action = QAction("Insert the Code", self)
        insert_action.triggered.connect(lambda: self.insert_into_editor(item, 0))

        # "Go to Information" seçeneği
        go_to_info_action = QAction("Search API Reference", self)
        go_to_info_action.triggered.connect(lambda: self.go_to_information(item))

        # Menü öğelerini ekleyin
        menu.addAction(insert_action)
        menu.addAction(go_to_info_action)

        # Ayraç ekleyin
        menu.addSeparator()

        # "Expand All" seçeneği
        expand_all_action = QAction("Expand All", self)
        expand_all_action.triggered.connect(self.expand_all_outliner_items)
        menu.addAction(expand_all_action)

        # "Collapse All" seçeneği
        collapse_all_action = QAction("Collapse All", self)
        collapse_all_action.triggered.connect(self.collapse_all_outliner_items)
        menu.addAction(collapse_all_action)

        # Ayraç ekleyin
        menu.addSeparator()

        # "Search QLineEdit'i Aç" seçeneği
        search_action = QAction("Open Search Bar", self)
        search_action.triggered.connect(self.toggle_search_bar)  # Daha önceki toggle_search_bar işlevine bağlandı
        menu.addAction(search_action)

        # Sağ tıklama menüsünü göster
        menu.exec_(self.outliner_list.viewport().mapToGlobal(position))

    def expand_all_outliner_items(self):
        """OUTLINER'daki tüm öğeleri genişletir."""
        self.outliner_list.expandAll()

    def collapse_all_outliner_items(self):
        """OUTLINER'daki tüm öğeleri kapatır."""
        self.outliner_list.collapseAll()

    def toggle_search_bar(self, event=None):
        """Search QLineEdit'i aç/kapa."""
        if not self.search_bar_visible:
            self.show_search_bar(event)  # Arama çubuğunu göster
        else:
            self.hide_search_bar(event)  # Arama çubuğunu gizle

    def go_to_information(self, item):
        """Seçilen öğeyi geliştirici kılavuzunda arar."""
        selected_text = item.text(0)  # Seçilen öğe

        # URL şablonu
        base_url = "https://learn.foundry.com/nuke/developers/15.0/pythondevguide/search.html"

        # Arama sorgusunu oluştur
        search_url = f"{base_url}?q={selected_text}&check_keywords=yes&area=default"

        # Tarayıcıda aç
        webbrowser.open(search_url)

    def custom_outliner_action(self, item):
        """OUTLINER'da özel bir işlem gerçekleştirir."""
        selected_text = item.text(0)
        QMessageBox.information(self, "Custom Action", f"You selected: {selected_text}")

    def filter_outliner(self, text):
        """OUTLINER içindeki öğeleri arama çubuğundaki metne göre filtreler."""
        root = self.outliner_list.invisibleRootItem()  # OUTLINER'ın kök öğesi

        # Filtre metni boşsa tüm öğeleri göster
        if not text:
            for i in range(root.childCount()):
                item = root.child(i)
                item.setHidden(False)
                for j in range(item.childCount()):
                    sub_item = item.child(j)
                    sub_item.setHidden(False)
            return

        # Arama metnine göre sınıf ve metotları filtrele
        for i in range(root.childCount()):  # Ana öğeler (sınıflar)
            item = root.child(i)
            match_found = False  # Ana öğeyi gösterip göstermeme durumu

            # Ana öğe metniyle arama metni eşleşiyor mu?
            if text.lower() in item.text(0).lower():
                item.setHidden(False)
                match_found = True
            else:
                item.setHidden(True)

            # Alt öğeleri kontrol et (metotlar)
            for j in range(item.childCount()):
                sub_item = item.child(j)

                if text.lower() in sub_item.text(0).lower():  # Arama metni alt öğeyle eşleşiyor mu?
                    sub_item.setHidden(False)
                    match_found = True  # Eğer bir alt öğe eşleşiyorsa ana öğeyi de göster
                else:
                    sub_item.setHidden(True)

            # Eğer alt öğelerden biri eşleştiyse ana öğeyi göster
            if match_found:
                item.setHidden(False)

    def update_completer_from_outliner(self):
        """OUTLINER'daki sınıf ve fonksiyon isimlerini QCompleter'e ekler."""
        outliner_items = []
        root = self.outliner_list.invisibleRootItem()  # OUTLINER'ın kök öğesi

        # OUTLINER'daki tüm öğeleri dolaşarak listeye ekle
        for i in range(root.childCount()):  # Ana öğeler (class'lar)
            item = root.child(i)
            outliner_items.append(item.text(0))  # Class ismini ekle

            for j in range(item.childCount()):  # Alt öğeler (methods'ler)
                sub_item = item.child(j)
                outliner_items.append(sub_item.text(0))  # Method ismini ekle

        # Tamamlama önerileri için QStringListModel kullanarak model oluşturuyoruz
        model = QStringListModel(outliner_items, self.completer)
        self.completer.setModel(model)

    def is_valid_python_identifier(self, name):
        """Python değişken adı kurallarına uygunluk kontrolü"""
        if not name.isidentifier():
            return False
        return True

    def show_python_naming_info(self):
        QMessageBox.information(self, "Python Naming Info",
                                "Python file names must:\n- Start with a letter or underscore\n- Contain only letters, numbers, or underscores\n- Not be a reserved keyword")
