import os
import sys
import json
import shutil
import ast
import webbrowser
from functools import partial
from PySide2.QtWidgets import *
from PySide2.QtGui import QIcon, QFont, QBrush, QColor, QSyntaxHighlighter, QTextCharFormat, QPainter, QTextFormat, QTextCursor, QGuiApplication
from PySide2.QtCore import Qt, QEvent, QRegExp, QStringListModel, QSize, QRect
from code_editor import CodeEditor
from core import PythonHighlighter, OutputCatcher


class EditorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window başlık değişkeni
        self.empty_project_win_title = "Nuke Code Editor: " # Boş ise bu isim döner
        self.setWindowTitle("Nuke Code Editor: Empty Project**") # Open ve New project'den isim çeker
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
        self.color_settings_path = os.path.join(os.getcwd(),"assets", "item_colors.json")

        # Sekmeli düzenleyici (Tab Widget) oluşturma
        self.tab_widget = QTabWidget()
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

        # Program başlarken renkleri yükle
        self.load_colors_from_file()
        # Son açılan projeler bu listeye JSON olarak atanır
        # Recent Projects ile ilgili değişkenler
        self.recent_projects_list = []  # Projeleri listelemek için boş bir liste
        self.recent_projects_path = os.path.join(os.getcwd(),"assets", "recent_projects.json")  # Dosya yolu
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

        # İkon boyutunu 60x60 piksel olarak ayarlıyoruz
        toolbar.setIconSize(QSize(35, 35))

        # Proje kök dizinini bulmak (relative path)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Bir üst dizine çıkıyoruz
        icons_path = os.path.join(project_root, 'ui', 'icons')  # Proje kök dizininden 'ui/icons' klasörüne göreli yol

        # 1. RUN Butonu (Kod çalıştırmak için)
        run_action = QAction(QIcon(os.path.join(icons_path, 'play.png')), '', self)  # İkon ile boş bir buton
        run_action.setToolTip("Run Current Code")  # Butona tooltip ekliyoruz
        run_action.triggered.connect(self.run_code)  # Fonksiyon bağlama
        toolbar.addAction(run_action)  # Butonu toolbara ekle

        # 2. SAVE Butonu (Kod kaydetmek için)
        save_action = QAction(QIcon(os.path.join(icons_path, 'save.png')), '', self)  # İkon ile boş bir buton
        save_action.setToolTip("Save Current File")  # Tooltip ekliyoruz
        save_action.triggered.connect(self.save_file)  # Fonksiyon bağlama
        toolbar.addAction(save_action)  # Butonu toolbara ekle

        # 3. ARAMA Butonu (Kod içinde arama yapmak için)
        search_action = QAction(QIcon(os.path.join(icons_path, 'search.png')), '', self)  # İkon ile boş bir buton
        search_action.setToolTip("Search in Code")  # Tooltip ekliyoruz
        search_action.triggered.connect(self.show_search_dialog)  # Fonksiyon bağlama
        toolbar.addAction(search_action)  # Butonu toolbara ekle

        # Boş widget ekleyerek butonları sağa veya alta iteceğiz (spacer)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Yatay için genişler, dikey için değil
        toolbar.addWidget(spacer)

        # 4. CLEAR Butonu (Output panelini temizlemek için)
        clear_action = QAction(QIcon(os.path.join(icons_path, 'clear.png')), '', self)  # İkon ile boş bir buton
        clear_action.setToolTip("Clear Output")  # Tooltip ekliyoruz
        clear_action.triggered.connect(self.clear_output)  # Fonksiyon bağlama
        toolbar.addAction(clear_action)  # Butonu toolbara ekle

        # 5. SETTINGS Butonu (Ayarlar menüsüne erişim)
        settings_action = QAction(QIcon(os.path.join(icons_path, 'settings.png')), '', self)  # İkon ile boş bir buton
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
        """OUTLINER'a sınıf ve fonksiyonları ekle, nuke.py ve nukescripts.py başlıklarını hariç tut."""

        # assets klasörüne bir önceki dizine geçerek ulaşmak
        nuke_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'nuke.py')
        nukescripts_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'nukescripts.py')

        # Nuke dosyalarındaki sınıf ve fonksiyonları alalım:
        nuke_classes = self.list_classes_from_file(nuke_file_path)
        nukescripts_classes = self.list_classes_from_file(nukescripts_file_path)

        # nuke.py ve nukescripts.py başlıklarını göstermeden, sadece sınıf ve metodları ekleyelim
        # Nuke.py içindeki sınıf ve fonksiyonları doğrudan ekleyelim
        self.add_classes_and_functions_to_tree(nuke_classes, self.outliner_list)

        # Nukescripts.py içindeki sınıf ve fonksiyonları doğrudan ekleyelim
        self.add_classes_and_functions_to_tree(nukescripts_classes, self.outliner_list)

        # Nuke.py dosyasını OUTLINER'a ekle:
        nuke_root_item = QTreeWidgetItem(self.outliner_list)
        nuke_root_item.setText(0, "nuke.py")
        self.add_classes_and_functions_to_tree(nuke_classes, nuke_root_item)

        # Nukescripts.py dosyasını OUTLINER'a ekle:
        nukescripts_root_item = QTreeWidgetItem(self.outliner_list)
        nukescripts_root_item.setText(0, "nukescripts.py")
        self.add_classes_and_functions_to_tree(nukescripts_classes, nukescripts_root_item)

    def list_classes_from_file(self, file_path):
        """Verilen dosyadaki sınıfları ve fonksiyonları bul ve döndür."""
        full_path = os.path.abspath(file_path)

        if not os.path.exists(full_path):
            print(f"Error: {full_path} dosyası bulunamadı!")
            return []

        with open(full_path, 'r') as file:
            file_content = file.read()

        tree = ast.parse(file_content)  # Python kodunu AST'ye dönüştür
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):  # Eğer sınıf tanımıysa
                class_name = node.name  # Sınıfın adı
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]  # Sınıfın metodları
                classes.append((class_name, methods))  # Sınıf ve metodları listeye ekle

        return classes  # Sınıf ve metod listesini döndür

    def add_classes_and_functions_to_tree(self, classes, root_item):
        """Sınıf ve fonksiyonları ağaç yapısına ekler."""
        for class_name, methods in classes:
            class_item = QTreeWidgetItem(root_item)
            class_item.setText(0, class_name)
            class_item.setText(1, "Class")  # "Class" olarak tipini ayarla

            for method in methods:
                method_item = QTreeWidgetItem(class_item)
                method_item.setText(0, method)
                method_item.setText(1, "Method")  # "Method" olarak tipini ayarla

    def create_menu(self):
        """Menü çubuğunu oluşturur."""
        menubar = self.menuBar()

        # 1. File Menüsü
        file_menu = menubar.addMenu('File')
        # Recent Projects menüsünü tanımla ve File menüsüne ekle

        new_project_action = QAction(QIcon('icons/new_project.png'), 'New Project', self)
        open_project_action = QAction(QIcon('icons/new_project.png'), 'Open Project', self)
        new_file_action = QAction(QIcon('icons/new_file.png'), 'New File', self)
        open_action = QAction(QIcon('icons/open.png'), 'Open File', self)
        save_action = QAction(QIcon('../ui/icons/save.png'), 'Save', self)
        save_as_action = QAction(QIcon('icons/save_as.png'), 'Save As', self)
        exit_action = QAction(QIcon('icons/exit.png'), 'Exit', self)

        file_menu.addAction(new_project_action)
        file_menu.addAction(open_project_action)
        file_menu.addSeparator()
        file_menu.addAction(new_file_action)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        self.recent_projects = file_menu.addMenu('Recent Projects')
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # "New Project" tıklandığında bir fonksiyon çalıştır
        new_project_action.triggered.connect(self.new_project_dialog)

        # 2. Edit Menüsü
        edit_menu = menubar.addMenu('Edit')
        find_action = QAction(QIcon('icons/find.png'), 'Search', self)
        # Edit Menüsünde "Find" işlemini arama fonksiyonuna bağlama
        find_action.triggered.connect(self.show_search_dialog)
        replace_action = QAction(QIcon('icons/replace.png'), 'Replace All', self)
        undo_action = QAction(QIcon('icons/undo.png'), 'Undo', self)
        redo_action = QAction(QIcon('icons/redo.png'), 'Redo', self)
        clear_action = QAction(QIcon('../ui/icons/clear.png'), 'Clear Output', self)
        clear_action.triggered.connect(self.clear_output)

        # Cut, Copy, Paste işlemleri
        cut_action = QAction(QIcon('icons/cut.png'), 'Cut', self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut_text)
        copy_action = QAction(QIcon('icons/copy.png'), 'Copy', self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_text)
        paste_action = QAction(QIcon('icons/paste.png'), 'Paste', self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_text)

        edit_menu.addAction(find_action)
        edit_menu.addAction(replace_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(clear_action)

        # 3. Run Menüsü
        run_menu = menubar.addMenu('Run')
        rn = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icons', 'play.png')
        run_action = QAction(QIcon(rn), 'Run Current Code', self)
        run_menu.addAction(run_action)

        # 4. Help Menüsü
        help_menu = menubar.addMenu('Help')
        documentation_action = QAction(QIcon('icons/documentation.png'), 'Documentation', self)
        licence_action = QAction(QIcon('icons/licence.png'), 'Licence', self)
        about_action = QAction(QIcon('icons/about.png'), 'About', self)
        help_menu.addAction(documentation_action)
        help_menu.addAction(licence_action)
        help_menu.addAction(about_action)

        # 5. Workspace Menüsü - New Menu Addition
        workspace_menu = menubar.addMenu('Workspace')
        reset_ui_action = QAction('Reset UI', self)
        set_default_ui_action = QAction('Set Default UI', self)

        reset_ui_action.triggered.connect(self.reset_ui)
        set_default_ui_action.triggered.connect(self.set_default_ui)

        workspace_menu.addAction(reset_ui_action)
        workspace_menu.addAction(set_default_ui_action)

        # Bind menu items to methods for File and Edit menus
        new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        new_file_action.triggered.connect(self.create_new_file_dialog)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        save_as_action.triggered.connect(self.save_file_as)
        exit_action.triggered.connect(self.file_exit)
        replace_action.triggered.connect(self.trigger_replace_in_active_editor)

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

    def new_project_dialog(self):
        """Yeni proje oluşturmak için diyalog kutusu."""
        # Bu işlemi yalnızca bir kez çalıştırmamız gerekiyor
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        dialog.setGeometry(200, 200, 400, 150)
        dialog.move(self.frameGeometry().center() - dialog.rect().center())

        layout = QVBoxLayout()

        # Proje ismi giriş alanı (placeholder text ile)
        project_name_input = QLineEdit()
        project_name_input.setPlaceholderText("Enter Project Name")
        layout.addWidget(project_name_input)

        # Proje dizini giriş alanı ve "Browse" butonu
        project_dir_input = QLineEdit()
        project_dir_input.setPlaceholderText("Select Project Directory")
        layout.addWidget(project_dir_input)

        project_dir_button = QPushButton("Browse")
        layout.addWidget(project_dir_button)
        project_desc = QLabel("Please be shure the correct information!")

        # Dizin seçimi için layout
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(project_dir_input)
        dir_layout.addWidget(project_dir_button)
        layout.addLayout(dir_layout)
        layout.addWidget(project_desc)

        # OK ve Cancel butonları
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        # Proje dizini seçiminde "Browse" butonuna tıklama işlemi
        project_dir_button.clicked.connect(lambda: self.browse_directory(project_dir_input))

        # OK butonuna tıklandığında proje oluşturma işlemi
        ok_button.clicked.connect(
            lambda: self.create_new_project(project_name_input.text(), project_dir_input.text(), dialog)
        )

        # Cancel butonuna tıklanınca dialogu kapatma işlemi
        cancel_button.clicked.connect(dialog.close)

        dialog.exec_()

    def create_new_project(self, project_name, project_directory, dialog):
        """Create a new project directory and set project_dir to the new path."""
        if not project_name.strip():
            QMessageBox.warning(self, "Error", "Please enter a valid project name.")
            return

        if not project_directory.strip():
            QMessageBox.warning(self, "Error", "Please select a project directory.")
            return

        # Create the new project directory
        project_path = os.path.join(project_directory, project_name)

        if os.path.exists(project_path):
            QMessageBox.warning(self, "Error", "Project directory already exists.")
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
        #self.project_dir = QFileDialog.getExistingDirectory(self, "Proje Dizini Seç")
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
        """Dizindeki tüm dosya ve klasörleri tree'ye ekler."""
        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)
            item = QTreeWidgetItem(parent_item)
            item.setText(0, file_name)

            if os.path.isdir(file_path):
                self.add_items_to_tree(item, file_path)
            else:
                # Eğer dosya .py uzantılıysa italic yapalım
                if file_name.endswith(".py"):
                    font = item.font(0)
                    font.setItalic(True)
                    item.setFont(0, font)

            # Sağ tık menüsü için öğeye sağ tıklama sinyali bağlama
            item.setData(0, Qt.UserRole, file_path)

    def on_workplace_item_double_clicked(self, item, column):
        """Workplace'deki bir dosya çift tıklanınca dosyayı aç."""
        file_path = item.data(0, Qt.UserRole)
        if file_path and file_path.endswith(".py"):
            self.add_new_tab(file_path)

    def context_menu(self, position):
        """Sağ tıklama menüsünü oluştur."""
        menu = QMenu()

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
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            os.startfile(os.path.dirname(file_path))
        else:
            QMessageBox.warning(self, "Hata", "Dosya mevcut değil.")

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

    def create_new_file_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Python File")
        dialog.setGeometry(200, 200, 300, 150)
        dialog.move(self.frameGeometry().center() - dialog.rect().center())
        layout = QVBoxLayout()

        # Dosya adı girişi
        file_name_input = QLineEdit()
        file_name_input.setPlaceholderText("Enter Python file name (e.g., example.py)")
        layout.addWidget(file_name_input)

        # Yazım kuralları ile ilgili açıklama metni
        instructions_label = QLabel("Please follow the naming conventions. For more info, press the Info button.")
        layout.addWidget(instructions_label)

        # Buton düzeni: Info butonunu Create'in soluna alıyoruz ve genişliğini 50px yapıyoruz
        button_layout = QHBoxLayout()
        info_button = QPushButton("Info")
        info_button.setMaximumWidth(50)  # Info butonunun genişliği 50px yapılıyor
        button_layout.addWidget(info_button)
        create_button = QPushButton("Create")
        button_layout.addWidget(create_button)
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Diyalog Layout
        dialog.setLayout(layout)

        # Create ve Cancel butonlarına fonksiyon ekleme
        create_button.clicked.connect(lambda: self.create_file(file_name_input.text(), dialog))
        cancel_button.clicked.connect(dialog.close)
        info_button.clicked.connect(
        self.show_python_naming_info)  # Info butonuna show_python_naming_info fonksiyonunu bağlıyoruz

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

        self.tab_widget.addTab(editor, os.path.basename(file_path))
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

    def save_recent_projects(self):
        """Recent Projects listesini JSON dosyasına kaydeder."""
        try:
            with open(self.recent_projects_path, 'w') as file:
                json.dump(self.recent_projects_list, file)
        except Exception as e:
            print(f"Error saving recent projects: {e}")

    def open_file(self):
        """Dosya açma işlemi."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "Python Dosyaları (*.py);;Tüm Dosyalar (*)")
        if file_name:
            self.add_new_tab(file_name)

    def save_file(self):
        """Save the current file."""
        if self.project_dir is None:
            QMessageBox.warning(self, "Save projects", "Please create and save the python file.\nThere is no opened project currently this project is empty\nIf you want to do nothing please discard.")
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
            file_name, _ = QFileDialog.getSaveFileName(self, "Dosya Kaydet", "", "Python Dosyaları (*.py);;Tüm Dosyalar (*)")
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
        reply = QMessageBox.question(self, 'Çıkış', "Kaydedilmemiş değişiklikler mevcut. Yine de çıkmak istiyor musunuz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()

    def create_docks(self):
        """Sol tarafa dockable listeleri ekler."""
        workplace_dock = QDockWidget("WORKPLACE", self)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderHidden(True)
        self.workplace_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.workplace_tree.customContextMenuRequested.connect(self.context_menu)  # Sağ tıklama menüsü ekleme
        self.workplace_tree.itemDoubleClicked.connect(self.on_workplace_item_double_clicked)
        workplace_dock.setWidget(self.workplace_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, workplace_dock)
        self.workplace_tree.setAlternatingRowColors(True)

        # OUTLINER
        outliner_dock = QDockWidget("OUTLINER", self)

        # OUTLINER içeriği için bir widget ve layout oluşturuyoruz
        outliner_widget = QWidget()  # OUTLINER'ın ana widget'ı
        outliner_layout = QVBoxLayout(outliner_widget)  # OUTLINER widget'ına dikey layout ekliyoruz

        # QTreeWidget (OUTLINER) ekliyoruz
        self.outliner_list = QTreeWidget()  # OUTLINER QTreeWidget'ini oluştur
        self.outliner_list.setAlternatingRowColors(True)
        self.outliner_list.setHeaderLabels(["Class/Function", "Type"])  # OUTLINER başlıkları
        outliner_layout.addWidget(self.outliner_list)  # OUTLINER'ı layout'a ekliyoruz

        # QLineEdit (Arama Çubuğu) ekliyoruz
        self.search_bar = QLineEdit()  # Arama çubuğunu oluştur
        self.search_bar.setPlaceholderText("Search...")  # Placeholder text
        outliner_layout.addWidget(self.search_bar)  # Arama çubuğunu layout'a ekliyoruz

        # QLineEdit üzerindeki metin değiştiğinde filter_outliner fonksiyonunu çağırıyoruz
        self.search_bar.textChanged.connect(self.filter_outliner)

        # QCompleter tanımlıyoruz
        self.completer = QCompleter(self)  # QCompleter'i oluştur
        self.search_bar.setCompleter(self.completer)  # Arama çubuğu ile ilişkilendiriyoruz

        # Layout'u OUTLINER dock widget'ına yerleştiriyoruz
        outliner_dock.setWidget(outliner_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, outliner_dock)

        # OUTLINER'a sınıf ve fonksiyonları ekleyelim
        self.populate_outliner_with_functions()

        # OUTLINER tamamlandıktan sonra QCompleter'i güncelle
        self.update_completer_from_outliner()

        # OUTLINER'a sınıf ve fonksiyonları ekleyelim
        self.populate_outliner_with_functions()
        self.outliner_list.itemDoubleClicked.connect(self.insert_into_editor)
        # OUTLINER sağ tıklama menüsü
        self.outliner_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outliner_list.customContextMenuRequested.connect(self.context_menu_outliner)

        # HEADER Listesi için QTreeWidget kullanıyoruz
        header_dock = QDockWidget("HEADER", self)
        self.header_tree = QTreeWidget()
        self.header_tree.setHeaderLabels(["Element", "Type"])  # İki sütun ekliyoruz
        header_dock.setWidget(self.header_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, header_dock)

        # Öğeye tıklama sinyalini bağla
        self.header_tree.itemClicked.connect(self.go_to_line_from_header)  # Bu satırı burada ekliyoruz

    import ast

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
        """OUTLINER'da çift tıklanan öğeyi aktif metin düzenleyiciye, imlecin olduğu yere ekler."""
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
        """OUTLINER'da sağ tıklama menüsü."""
        menu = QMenu()

        # "Insert the Code" seçeneği
        insert_action = QAction("Insert the Code", self)
        insert_action.triggered.connect(lambda: self.insert_into_editor(self.outliner_list.currentItem(), 0))

        # "Go to Information" seçeneği
        go_to_info_action = QAction("Search API Reference", self)
        go_to_info_action.triggered.connect(lambda: self.go_to_information(self.outliner_list.currentItem()))

        # Menünün öğelerini ekleyelim
        menu.addAction(insert_action)
        menu.addAction(go_to_info_action)

        # Sağ tık menüsünü göster
        menu.exec_(self.outliner_list.viewport().mapToGlobal(position))

    def go_to_information(self, item):
        """Seçilen öğeyi geliştirici kılavuzunda arar."""
        selected_text = item.text(0)  # Seçilen öğe

        # URL şablonu
        base_url = "https://learn.foundry.com/nuke/developers/15.0/pythondevguide/search.html"

        # Arama sorgusunu oluştur
        search_url = f"{base_url}?q={selected_text}&check_keywords=yes&area=default"

        # Tarayıcıda aç
        webbrowser.open(search_url)

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
