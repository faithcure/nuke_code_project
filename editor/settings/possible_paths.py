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