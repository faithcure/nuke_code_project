import os
import importlib
from PySide2.QtWidgets import QToolButton, QAction, QToolBar, QWidget, QSizePolicy, QMenu
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
import editor.core
import editor.nlink
import editor.settings.settings_ux as settings_ux
importlib.reload(editor.core)
importlib.reload(editor.nlink)
importlib.reload(settings_ux)
from editor.nlink import update_nuke_functions
from editor.core import PathFromOS, CodeEditorSettings


class MainToolbar:
    @staticmethod
    def create_toolbar(parent):
        """Toolbar'ı oluşturur ve gerekli butonları ekler."""
        toolbar = parent.addToolBar("MAIN TOOLBAR")
        parent.addToolBar(CodeEditorSettings().setToolbar_area, toolbar)  # Araç çubuğunu pencerenin sol tarafına yerleştir

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Yatay için genişler, dikey için değil

        # İkon boyutunu 60x60 piksel olarak ayarlıyoruz
        toolbar.setIconSize(CodeEditorSettings().toolbar_icon_size)
        toolbar.setStyleSheet("QToolBar { spacing: 4px;}")
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(True)
        parent.addToolBar(Qt.TopToolBarArea, toolbar)

        # 1. RUN Butonu (Kod çalıştırmak için)
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), '', parent)
        run_action.setToolTip("Run Current Code")
        run_action.triggered.connect(parent.run_code)
        toolbar.addAction(run_action)

        # 2. SAVE Butonu (Kod kaydetmek için)
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), '', parent)
        save_action.setToolTip("Save Current File")
        save_action.triggered.connect(parent.save_file)
        toolbar.addAction(save_action)

        # 3. ARAMA Butonu (Kod içinde arama yapmak için)
        search_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), '', parent)
        search_action.setToolTip("Search in Code")
        search_action.triggered.connect(parent.show_search_dialog)
        toolbar.addAction(search_action)

        # 4. Update (NLink)
        update_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'update.svg')), 'Update NLink', parent)
        update_action.setToolTip("Update Nuke Functions List (NLink!)")
        update_action.triggered.connect(update_nuke_functions)
        toolbar.addAction(update_action)
        toolbar.addSeparator()

        # 5. Boş widget ekleyerek butonları sağa veya alta iteceğiz (spacer)
        toolbar.addWidget(spacer)


        # Menü oluşturma fonksiyonu
        def create_expand_menu():
            mode_menu = QMenu(parent)
            for mode_name, function in settings_ux.ui_modes.items():  # settings_ux içinden ui_modes kullanılıyor
                action = mode_menu.addAction(mode_name)
                action.triggered.connect(lambda checked=False, func=function: func(parent))
            return mode_menu

        # Menü ve buton bağlama
        ui_menu = create_expand_menu()

        ui_button = QToolButton(toolbar)
        ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))
        ui_button.setToolTip("Switch Toolbar Modes")
        ui_button.setPopupMode(QToolButton.InstantPopup)
        ui_button.setMenu(ui_menu)
        toolbar.addWidget(ui_button)

        # Dikey ve yatay değişim için adaptasyon
        def adjust_expand_layout(orientation):
            if orientation == Qt.Vertical:
                ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))
            else:
                ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))

        # Sinyal bağlantısı
        toolbar.orientationChanged.connect(adjust_expand_layout)

        # 6. CLEAR Butonu (Output panelini temizlemek için)
        clear_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'clear.svg')), '', parent)  # İkon ile boş bir buton
        clear_action.setToolTip("Clear Output")  # Tooltip ekliyoruz
        clear_action.triggered.connect(parent.clear_output)  # Fonksiyon bağlama
        toolbar.addAction(clear_action)  # Butonu toolbara ekle

        # 7. SETTINGS Butonu (Ayarlar menüsüne erişim)
        settings_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'settings.png')), '', parent)  # İkon ile boş bir buton
        settings_action.setToolTip("Settings")  # Tooltip ekliyoruz
        settings_action.triggered.connect(parent.open_settings)  # Fonksiyon bağlama
        toolbar.addAction(settings_action)  # Butonu toolbara ekle

        # Toolbar yönü değiştiğinde spacer widget'inin genişlik/yükseklik politikasını değiştireceğiz
        toolbar.orientationChanged.connect(lambda orientation: parent.update_toolbar_spacer(orientation, spacer))
