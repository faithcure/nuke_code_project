import os
import importlib
from PySide2.QtWidgets import QToolButton
from PySide2.QtCore import QSize, Qt
from PySide2.QtWidgets import QAction, QToolBar, QWidget, QSizePolicy, QMenu
from PySide2.QtGui import QIcon
import editor.core
import editor.nlink
import editor.settings.settings_ux
importlib.reload(editor.core)
importlib.reload(editor.nlink)
importlib.reload(editor.settings.settings_ux)
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
        parent.addToolBar(Qt.TopToolBarArea, toolbar) # Default position

        # 1. RUN Butonu (Kod çalıştırmak için)
        run_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'play.svg')), '', parent)  # İkon ile boş bir buton
        run_action.setToolTip("Run Current Code")  # Butona tooltip ekliyoruz
        run_action.triggered.connect(parent.run_code)  # Fonksiyon bağlama
        toolbar.addAction(run_action)  # Butonu toolbara ekle

        # 2. SAVE Butonu (Kod kaydetmek için)
        save_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'save.svg')), '', parent)  # İkon ile boş bir buton
        save_action.setToolTip("Save Current File")  # Tooltip ekliyoruz
        save_action.triggered.connect(parent.save_file)  # Fonksiyon bağlama
        toolbar.addAction(save_action)  # Butonu toolbara ekle

        # 3. ARAMA Butonu (Kod içinde arama yapmak için)
        search_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'search.svg')), '', parent)  # İkon ile boş bir buton
        search_action.setToolTip("Search in Code")  # Tooltip ekliyoruz
        search_action.triggered.connect(parent.show_search_dialog)  # Fonksiyon bağlama
        toolbar.addAction(search_action)  # Butonu toolbara ekle

        # 4. Update (NLink)
        update_action = QAction(QIcon(os.path.join(PathFromOS().icons_path, 'update.svg')), 'Update NLink', parent)
        update_action.setToolTip("Update Nuke Functions List (NLink!)")
        update_action.triggered.connect(update_nuke_functions)  # Butona fonksiyonu bağlama
        toolbar.addAction(update_action)
        toolbar.addSeparator()

        # 5. Boş widget ekleyerek butonları sağa veya alta iteceğiz (spacer)
        toolbar.addWidget(spacer)
        dock_names = [
            'workplace_dock',
            'outliner_dock',
            'header_dock',
            'console_dock',
            'nuke_ai_dock',
            'output_dock'
        ]
        dock_default_positions = {
            'workplace_dock': Qt.RightDockWidgetArea,
            'outliner_dock': Qt.LeftDockWidgetArea,
            'header_dock': Qt.LeftDockWidgetArea,
            'console_dock': Qt.BottomDockWidgetArea,
            'nuke_ai_dock': Qt.BottomDockWidgetArea,
            'output_dock': Qt.BottomDockWidgetArea
        }

        def set_default_mode(main_window):
            """
            Default Mode:
            - Tüm dock widget'ları görünür yapar.
            - Hepsini varsayılan yerlerine yerleştirir.
            - 'console_dock', 'nuke_ai_dock' ve 'output_dock' widget'larını altta sekmeli yapar.
            """
            # Dock'ları kontrol ederek görünür hale getirin ve konumlarını düzenleyin
            for dock_name, position in dock_default_positions.items():
                if hasattr(main_window, dock_name):
                    dock_widget = getattr(main_window, dock_name)
                    main_window.addDockWidget(position, dock_widget)
                    dock_widget.setVisible(True)

            # Alttaki dock'ları sekmeli yap
            if hasattr(main_window, 'output_dock') and hasattr(main_window, 'nuke_ai_dock') and hasattr(main_window,
                                                                                                         'console_dock'):
                main_window.tabifyDockWidget(main_window.output_dock, main_window.console_dock)
                main_window.tabifyDockWidget(main_window.output_dock, main_window.nuke_ai_dock)

            # İlk sekmenin açık olmasını sağla
            if hasattr(main_window, 'console_dock'):
                main_window.output_dock.raise_()

        def set_expanded_mode(main_window):
            """
            Expanded Mode:
            - Tüm dock widget'ları görünür hale getirir.
            - Outliner ve Header sol üstte, yan yana yerleştirilir.
            - Workplace sağ tarafta tam ekran yüksekliğinde olur.
            - Console, Output ve NukeAI aşağıda sekmesiz ayrı görünür.
            """
            print("Expanded Mode Activated")

            # Dock widget'ların isimleri

            # Tüm widget'ları görünür yap
            for dock_name in dock_names:
                if hasattr(main_window, dock_name):
                    dock_widget = getattr(main_window, dock_name)
                    dock_widget.setVisible(True)
                    dock_widget.setFloating(False)  # Expanded Mode'da dock edilmiş halde olmalı

            # Sol üst: Outliner ve Header yan yana
            if hasattr(main_window, 'outliner_dock') and hasattr(main_window, 'header_dock'):
                main_window.addDockWidget(Qt.LeftDockWidgetArea, main_window.outliner_dock)
                main_window.addDockWidget(Qt.LeftDockWidgetArea, main_window.header_dock)
                main_window.splitDockWidget(main_window.outliner_dock, main_window.header_dock, Qt.Horizontal)

            # Sağ: Workplace tam yükseklikte
            if hasattr(main_window, 'workplace_dock'):
                main_window.addDockWidget(Qt.RightDockWidgetArea, main_window.workplace_dock)

            # Alt: Console, Output ve NukeAI ayrı ayrı
            if hasattr(main_window, 'console_dock') and hasattr(main_window, 'output_dock') and hasattr(main_window,
                                                                                                        'nuke_ai_dock'):
                main_window.addDockWidget(Qt.BottomDockWidgetArea, main_window.console_dock)
                main_window.addDockWidget(Qt.BottomDockWidgetArea, main_window.output_dock)
                main_window.addDockWidget(Qt.BottomDockWidgetArea, main_window.nuke_ai_dock)

            # Alt dock'ları sekmeli yap
            main_window.tabifyDockWidget(main_window.console_dock, main_window.output_dock)
            main_window.tabifyDockWidget(main_window.console_dock, main_window.nuke_ai_dock)

            # İlk tab olarak Console'u seç
            main_window.console_dock.raise_()

            print("Expanded Mode: Panels arranged in an expanded layout.")

        def set_focus_mode(main_window):
            if hasattr(main_window, 'workplace_dock'):
                main_window.workplace_dock.setVisible(False)
                main_window.outliner_dock.setVisible(False)
                main_window.header_dock.setVisible(False)
                main_window.console_dock.setVisible(False)
                main_window.nuke_ai_dock.setVisible(False)
                main_window.output_dock.setVisible(False)
                print("Default Mode Activated: WORKPLACE dock hidden")
            else:
                print("Warning: 'workplace_dock' not found in the main window!")

        def set_compact_mode(main_window):
            """
            Compact Mode:
            - Tüm widget'ları alt tarafa sekmeli olarak taşır.
            - Görünmez widget'lar varsa görünür hale getirir.
            """
            print("Compact Mode Activated")

            # İlk görünür dock widget'ı bulun ve diğerlerini bunun altına tabify yap
            base_dock = None

            for dock_name in dock_names:
                if hasattr(main_window, dock_name):
                    dock_widget = getattr(main_window, dock_name)

                    # Görünmez widget'ları görünür hale getir
                    dock_widget.setVisible(True)

                    if base_dock is None:
                        # İlk dock'u tab'ın temeli olarak ayarla ve aşağıya taşı
                        base_dock = dock_widget
                        main_window.addDockWidget(Qt.BottomDockWidgetArea, base_dock)
                    else:
                        # Diğer dock'ları tab olarak ekle
                        main_window.tabifyDockWidget(base_dock, dock_widget)

            # En son tab'ı seçilebilir yap
            if base_dock:
                base_dock.raise_()

            print("Compact Mode: All panels are now tabbed at the bottom.")

        # Menü öğeleri ve işlev eşlemesi
        ui_modes = {
            "Default Mode": set_default_mode,
            "Expanded Mode": set_expanded_mode,
            "Focus Mode": set_focus_mode,
            "Compact Mode": set_compact_mode
        }

        # Menü oluşturma fonksiyonu
        def create_expand_menu():
            mode_menu = QMenu(parent)
            # Menü öğelerini oluştur ve ilgili işlevleri bağla
            for mode_name, function in ui_modes.items():
                action = mode_menu.addAction(mode_name)
                action.triggered.connect(
                    lambda checked=False, func=function: func(parent))  # checked'i varsayılan False yapar

            return mode_menu

        # Menü ve buton bağlama
        ui_menu = create_expand_menu()

        # QToolButton oluştur
        ui_button = QToolButton(toolbar)
        ui_button.setIcon(QIcon(os.path.join(PathFromOS().icons_path, 'ux_design.svg')))
        ui_button.setToolTip("Switch Toolbar Modes")
        ui_button.setPopupMode(QToolButton.InstantPopup)  # Menü anında açılır
        ui_button.setMenu(ui_menu)  # Menü bağlanır
        toolbar.addWidget(ui_button)  # Butonu toolbara ekle

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
