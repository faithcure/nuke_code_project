import json
import os
import nuke
from editor.core import PathFromOS

# Nuke fonksiyonlarını çekme fonksiyonu
def get_nuke_functions():
    """Nuke fonksiyonlarını dinamik olarak çeker."""
    nuke_functions = [attr for attr in dir(nuke) if callable(getattr(nuke, attr))]
    return nuke_functions

# Nuke fonksiyonlarını JSON dosyasına yazma
def update_nuke_functions():
    """Nuke'deki fonksiyonları JSON'a yazar."""
    nuke_functions = get_nuke_functions()

    # JSON dosyasının bulunduğu dizin
    json_dir = os.path.join(PathFromOS().assets_path, 'dynamic_data')

    # dynamic_data dizini yoksa oluştur
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    json_path = os.path.join(json_dir, 'nuke_functions.json')

    # Dosyayı yazma modu ile açıyoruz ve güncelliyoruz
    with open(json_path, 'w') as json_file:
        json.dump(nuke_functions, json_file, indent=4)

# JSON dosyasından Nuke fonksiyonlarını yükleme
def load_nuke_functions():
    """Nuke fonksiyonlarını JSON dosyasından yükler. Dosya yoksa günceller."""
    json_path = os.path.join(PathFromOS().assets_path, 'dynamic_data', 'nuke_functions.json')

    # Eğer JSON dosyası yoksa güncelleme yap
    if not os.path.exists(json_path):
        update_nuke_functions()

    # JSON dosyasını aç ve içeriği döndür
    with open(json_path, 'r') as json_file:
        return json.load(json_file)
