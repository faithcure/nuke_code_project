import requests
import os
import sys

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMessageBox, QProgressDialog

from editor.settings.settings_ui import ModuleInstallerThread


def validate_credentials(self, username_input, token_input):
    """
    Kullanıcıdan gelen GitHub kullanıcı adı ve token bilgilerini doğrular.
    """
    username = username_input.text().strip()
    token = token_input.text().strip()

    if not username or not token:
        QMessageBox.warning(self, "Validation Failed", "Username or token cannot be empty.")
        return

    if self.check_github_credentials(username, token):
        # Doğrulama başarılıysa
        self.status_label.setText("Validated successfully")
        self.status_label.setStyleSheet("color: #8bc34a; font-weight: bold;")  # Pastel yeşil
        # QMessageBox.information(self, "Validation Successful", "The GitHub credentials are valid.")
    else:
        # Doğrulama başarısızsa
        self.status_label.setText("Validation failed")
        self.status_label.setStyleSheet("color: #ff6f61; font-weight: bold;")  # Pastel kırmızı
        QMessageBox.critical(self, "Validation Failed", "Invalid GitHub credentials. Please try again.")


def check_github_credentials(self, username, token):
    """
    GitHub kullanıcı adı ve token doğrulama işlevi.
    """
    if not username or not token:
        QMessageBox.critical(
            self,
            "Validation Error",
            "Please enter both username and token."
        )
        return False

    try:
        url = "https://api.github.com/user"
        response = requests.get(url, auth=(username, token))

        if response.status_code == 200:
            # API'den dönen kullanıcı adı
            api_username = response.json().get('login', '')

            # Kullanıcı adı eşleşiyor mu?
            if username == api_username:
                QMessageBox.information(
                    self,
                    "Validation Successful",
                    f"Welcome, {api_username}!, The GitHub credentials are valid."
                )
                return True
            else:
                QMessageBox.critical(
                    self,
                    "Username Mismatch",
                    f"Provided username does not match the token owner.\n"
                    f"Expected: {api_username}\nProvided: {username}"
                )
                return False
        elif response.status_code == 401:
            QMessageBox.critical(
                self,
                "Authentication Failed",
                "Authentication failed. Please check your username and token."
            )
            return False
        else:
            QMessageBox.critical(
                self,
                "Authentication Error",
                f"Unexpected error: {response.json().get('message', 'Unknown error')}."
            )
            return False
    except requests.exceptions.RequestException as e:
        QMessageBox.critical(self, "Network Error", f"An error occurred: {e}")
        return False


def show_fix_instructions(self, install_path):
    """
    Show instructions on how to manually add the modules path to sys.path.
    """
    code_to_add = f"sys.path.append('{install_path}')"
    QMessageBox.information(
        self,
        "Fix Instructions",
        f"The following code needs to be added to your init.py file:\n\n"
        f"{code_to_add}\n\n"
        "Path to init.py: ~/.nuke/init.py\n\n"
        "Make sure to restart Nuke after making these changes."
    )


def install_github_modules(self):
    """
    Install GitHub modules to the 'modules' directory using a background thread and show detailed progress.
    After installation, add the 'modules' path to sys.path in the .nuke/init.py file and ask the user to restart Nuke.
    """
    # Hedef dizini belirle
    install_path = os.path.join(os.path.dirname(__file__), "modules")
    required_modules = ["gitdb", "GitPython"]

    # .nuke klasörünü bul
    user_home = os.path.expanduser("~")
    nuke_dir = os.path.join(user_home, ".nuke")
    init_path = os.path.join(nuke_dir, "init.py")
    print(init_path, "init path")

    # 'modules' klasörü yoksa oluştur
    if not os.path.exists(install_path):
        os.makedirs(install_path)

    # Sistem Python yorumlayıcısını bul
    python_path = "python"
    if "PYTHON_HOME" in os.environ:
        python_path = os.path.join(os.environ["PYTHON_HOME"], "python.exe")
    else:
        # Kullanıcının ana dizinini bul
        user_home = os.path.expanduser("~")  # Dinamik olarak kullanıcı dizinini alır

        possible_paths = [
            # Dinamik Windows Yolları
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python311", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python310", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python39", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python38", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python37", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Microsoft", "WindowsApps", "python.exe"),
            os.path.join(user_home, "anaconda3", "python.exe"),
            os.path.join(user_home, "miniconda3", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Continuum", "anaconda3", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Continuum", "miniconda3", "python.exe"),

            # Sabit Windows Yolları
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Python39\python.exe",
            r"C:\Python38\python.exe",
            r"C:\Python37\python.exe",
            r"C:\Python36\python.exe",
            r"C:\Program Files\Python311\python.exe",
            r"C:\Program Files\Python310\python.exe",
            r"C:\Program Files\Python39\python.exe",
            r"C:\Program Files\Python38\python.exe",
            r"C:\Program Files (x86)\Python37\python.exe",
            r"C:\Program Files (x86)\Python36\python.exe",

            # Linux ve MacOS Yolları
            "/usr/bin/python3.11",
            "/usr/bin/python3.10",
            "/usr/bin/python3.9",
            "/usr/bin/python3.8",
            "/usr/bin/python3.7",
            "/usr/bin/python3.6",
            "/usr/bin/python3",
            "/usr/bin/python",
            "/usr/local/bin/python3.11",
            "/usr/local/bin/python3.10",
            "/usr/local/bin/python3.9",
            "/usr/local/bin/python3.8",
            "/usr/local/bin/python3.7",
            "/usr/local/bin/python3",
            "/usr/local/bin/python",
            "/opt/python3.11/bin/python3",
            "/opt/python3.10/bin/python3",
            "/opt/python3.9/bin/python3",
            "/opt/python3.8/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.8/bin/python3",

            # Virtualenv veya Conda Sanal Ortamları
            os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin", "python"),
            os.path.join(os.environ.get("CONDA_PREFIX", ""), "bin", "python"),

            # Pyenv Python Yolları
            os.path.join(user_home, ".pyenv", "shims", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.11.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.10.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.9.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.8.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.7.0", "bin", "python"),

            # Custom Paths
            r"D:\Python311\python.exe",
            r"D:\Python310\python.exe",
            r"D:\Python39\python.exe"
        ]

        # Çıktıyı kontrol et
        for path in possible_paths:
            print(f"Checking: {path}")

        for path in possible_paths:
            if os.path.exists(path):
                python_path = path
                break
        else:
            QMessageBox.critical(
                self,
                "Python Not Found",
                "System Python could not be located. Please install Python or specify its path using the PYTHON_HOME environment variable."
            )
            return

    # Progress Dialog oluştur
    progress = QProgressDialog("Installing GitHub modules...", "Cancel", 0, len(required_modules))
    progress.setWindowTitle("Installation Progress")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)

    # Modül kurulum işlemi için thread başlat
    thread = ModuleInstallerThread(install_path, required_modules, python_path)
    thread.progress_updated.connect(lambda value, text: (
        progress.setValue(value),
        progress.setLabelText(text)
    ))
    thread.download_info.connect(lambda info: progress.setLabelText(info))

    def on_completed():
        # init.py'yi güncelle
        try:
            if os.path.exists(init_path):
                # Dosya yazılabilir mi kontrol et
                if not os.access(init_path, os.W_OK):
                    raise PermissionError(f"Cannot write to {init_path}. Check file permissions.")

                with open(init_path, "a") as init_file:
                    init_file.write(f"\n# Automatically added modules path\n")
                    init_file.write(f"import sys\n")
                    init_file.write(f"sys.path.append({repr(install_path)})\n")  # Kaçış karakterlerini düzelt

                QMessageBox.information(
                    self,
                    "Installation Complete",
                    f"Modules have been successfully installed, and the path was added to {init_path}.\n"
                    "Please restart Nuke to apply changes."
                )
            else:
                QMessageBox.warning(
                    self,
                    "init.py Not Found",
                    f"Could not locate {init_path}. Please manually add the following line to your init.py:\n"
                    f"sys.path.append({repr(install_path)})"
                )
        except PermissionError as pe:
            QMessageBox.critical(self, "Permission Error", str(pe))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update init.py: {e}")

        progress.setValue(len(required_modules))
        self.prompt_restart_nuke()

    thread.completed.connect(on_completed)
    thread.error_occurred.connect(lambda error: QMessageBox.critical(self, "Installation Error", error))
    progress.canceled.connect(lambda: thread.terminate())
    thread.start()


def update_github_modules(self, install_path, required_modules):
    """
    Update the specified GitHub modules in the 'modules' directory.
    Args:
        install_path (str): Path to the folder where modules are installed.
        required_modules (list): List of required module names to update.
    """
    # Sistem Python yorumlayıcısını bul
    python_path = "python"
    if "PYTHON_HOME" in os.environ:
        python_path = os.path.join(os.environ["PYTHON_HOME"], "python.exe")
    else:
        # Kullanıcının ana dizinini bul
        user_home = os.path.expanduser("~")  # Dinamik olarak kullanıcı dizinini alır

        possible_paths = [
            # Dinamik Windows Yolları
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python311", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python310", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python39", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python38", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Python", "Python37", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Microsoft", "WindowsApps", "python.exe"),
            os.path.join(user_home, "anaconda3", "python.exe"),
            os.path.join(user_home, "miniconda3", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Continuum", "anaconda3", "python.exe"),
            os.path.join(user_home, "AppData", "Local", "Continuum", "miniconda3", "python.exe"),

            # Sabit Windows Yolları
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Python39\python.exe",
            r"C:\Python38\python.exe",
            r"C:\Python37\python.exe",
            r"C:\Python36\python.exe",
            r"C:\Program Files\Python311\python.exe",
            r"C:\Program Files\Python310\python.exe",
            r"C:\Program Files\Python39\python.exe",
            r"C:\Program Files\Python38\python.exe",
            r"C:\Program Files (x86)\Python37\python.exe",
            r"C:\Program Files (x86)\Python36\python.exe",

            # Linux ve MacOS Yolları
            "/usr/bin/python3.11",
            "/usr/bin/python3.10",
            "/usr/bin/python3.9",
            "/usr/bin/python3.8",
            "/usr/bin/python3.7",
            "/usr/bin/python3.6",
            "/usr/bin/python3",
            "/usr/bin/python",
            "/usr/local/bin/python3.11",
            "/usr/local/bin/python3.10",
            "/usr/local/bin/python3.9",
            "/usr/local/bin/python3.8",
            "/usr/local/bin/python3.7",
            "/usr/local/bin/python3",
            "/usr/local/bin/python",
            "/opt/python3.11/bin/python3",
            "/opt/python3.10/bin/python3",
            "/opt/python3.9/bin/python3",
            "/opt/python3.8/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.9/bin/python3",
            "/Library/Frameworks/Python.framework/Versions/3.8/bin/python3",

            # Virtualenv veya Conda Sanal Ortamları
            os.path.join(os.environ.get("VIRTUAL_ENV", ""), "bin", "python"),
            os.path.join(os.environ.get("CONDA_PREFIX", ""), "bin", "python"),

            # Pyenv Python Yolları
            os.path.join(user_home, ".pyenv", "shims", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.11.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.10.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.9.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.8.0", "bin", "python"),
            os.path.join(user_home, ".pyenv", "versions", "3.7.0", "bin", "python"),

            # Custom Paths
            r"D:\Python311\python.exe",
            r"D:\Python310\python.exe",
            r"D:\Python39\python.exe"
        ]

        # Çıktıyı kontrol et
        for path in possible_paths:
            print(f"Checking: {path}")

        for path in possible_paths:
            if os.path.exists(path):
                python_path = path
                break
        else:
            QMessageBox.critical(
                self,
                "Python Not Found",
                "System Python could not be located. Please install Python or specify its path using the PYTHON_HOME environment variable."
            )
            return

    # Progress Dialog oluştur
    progress = QProgressDialog("Updating GitHub modules...", "Cancel", 0, len(required_modules))
    progress.setWindowTitle("Update Progress")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumDuration(0)

    # Modül güncelleme işlemi için thread başlat
    thread = ModuleInstallerThread(install_path, required_modules, python_path)

    def on_completed():
        progress.setValue(len(required_modules))
        QMessageBox.information(
            self,
            "Update Complete",
            "GitHub modules have been successfully updated."
        )

    def on_error(error):
        progress.close()
        QMessageBox.critical(self, "Update Error", error)

    thread.progress_updated.connect(lambda value, text: (
        progress.setValue(value),
        progress.setLabelText(text)
    ))

    def on_cancel():
        if thread.isRunning():
            thread.terminate()
        progress.close()

    thread.download_info.connect(lambda info: progress.setLabelText(info))
    thread.completed.connect(on_completed)
    thread.error_occurred.connect(on_error)
    progress.canceled.connect(lambda: thread.terminate())
    progress.canceled.connect(on_cancel)
    thread.start()


def prompt_restart_nuke(self):
    """
    Prompt the user to restart Nuke after module installation, explaining why it is necessary.
    """
    response = QMessageBox.question(
        self,
        "Restart Nuke",
        "The installed modules will take effect only after restarting Nuke. "
        "Do you want to restart Nuke now?",
        QMessageBox.Yes | QMessageBox.No
    )
    if response == QMessageBox.Yes:
        self.restart_nuke()


def restart_nuke(self):
    """
    Restart Nuke by terminating the current process and starting a new instance.
    """
    QMessageBox.information(self, "Restarting Nuke", "Nuke is restarting...")
    # Nuke yeniden başlatma işlemi burada yapılabilir
    # (örneğin, os.execv ile mevcut uygulama yeniden başlatılabilir)
    python_executable = sys.executable
    os.execv(python_executable, [python_executable] + sys.argv)


def check_github_modules(self, install_path, required_modules):
    """
    Check if required modules are present in the specified folder.
    Args:
        install_path (str): Path to the target folder where modules are installed.
        required_modules (list): List of required module names.
    Returns:
        bool: True if all required modules are found, False otherwise.
    """
    if not os.path.exists(install_path):
        return False

    installed_modules = os.listdir(install_path)  # List all directories/files in the install path
    for module in required_modules:
        if not any(module.lower() in item.lower() for item in installed_modules):
            return False
    return True