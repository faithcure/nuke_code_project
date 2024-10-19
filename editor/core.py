import os

class OutputCatcher:
    def __init__(self, output_widget):
        self.output_widget = output_widget

    def write(self, message):
        self.output_widget.append(message)  # Mesajı Output penceresine ekle

    def flush(self):
        pass  # Gerekirse bir flush metodu eklenebilir, fakat burada gerek yok

class PathFromOS:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons_path = os.path.join(self.project_root, 'ui', 'icons')
        self.json_path = os.path.join(self.project_root, 'assets')
        self.nuke_ref_path = os.path.join(self.project_root, 'assets', 'nuke.py')
        self.nukescripts_ref_path = os.path.join(self.project_root, 'assets', 'nukescripts.py')
        self.assets_path = os.path.join(self.project_root, 'assets')
        # Getting dynamic fonts from JetBrains Mono
        self.jet_fonts = os.path.join(self.project_root, 'assets', 'jetBrains','ttf')
        self.jet_fonts_var = os.path.join(self.project_root, 'assets', 'jetBrains','ttf',"variable")

