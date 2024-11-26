from PySide2.QtCore import Qt

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
        main_window.ddDockWidget(Qt.BottomDockWidgetArea, main_window.console_dock)
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

ui_modes = {
    "Default Mode": set_default_mode,
    "Expanded Mode": set_expanded_mode,
    "Focus Mode": set_focus_mode,
    "Compact Mode": set_compact_mode
}
root_modes = {
    "Mumen Rider (Professional)": set_default_mode,
    "Saitama (immersive)": set_focus_mode,

}
