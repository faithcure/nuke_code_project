# ✨ Nuke Python IDE (Beta Experimental 🚧)

A specialized Python IDE tailored for the **Foundry Nuke** environment, enabling VFX professionals to script, test, and debug seamlessly within Nuke. This IDE is built to enhance productivity and integrate effortlessly into VFX workflows, combining the power of Python scripting with the capabilities of Nuke.

---

## 📜 Table of Contents
- [🔍 Overview](#-overview)
- [✨ Features](#-features)
- [📥 Installation](#-installation)
- [🛠️ Usage](#️-usage)
- [🖥️ Compatibility](#-compatibility)
- [🤝 Contributions & Development](#-contributions--diaries)
- [📄 Licenses](#-licenses)
- [👨‍💻 Developers](#-developer-Diaris)

---

## 🔍 Overview
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #121212;
            color: #fff;
        }

        .gallery {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            padding: 20px;
        }

        .gallery img {
            width: 200px;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
            cursor: pointer;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .gallery img:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 16px rgba(255, 255, 255, 0.3);
        }

        /* Lightbox styles */
        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .lightbox img {
            max-width: 90%;
            max-height: 80%;
            border-radius: 10px;
        }

        .lightbox:target {
            display: flex;
        }

        .lightbox .close {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 30px;
            color: #fff;
            text-decoration: none;
            font-weight: bold;
            transition: color 0.3s ease;
        }

        .lightbox .close:hover {
            color: #f00;
        }
    </style>
</head>
<body>

<h1 style="text-align: center; padding: 20px;">Nuke Python IDE - Image Gallery</h1>
<div class="gallery">
    <a href="#lightbox1">
        <img src="https://github.com/faithcure/nuke_code_project/blob/master/nuke_python_ide.jpg" alt="Nuke Python IDE UI">
    </a>
    <a href="#lightbox2">
        <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_01.jpg" alt="Settings UI 1">
    </a>
    <a href="#lightbox3">
        <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_02.jpg" alt="Settings UI 2">
    </a>
    <a href="#lightbox4">
        <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_03.jpg" alt="Settings UI 3">
    </a>
</div>

<!-- Lightbox 1 -->
<div id="lightbox1" class="lightbox">
    <a href="#" class="close">&times;</a>
    <img src="https://github.com/faithcure/nuke_code_project/blob/master/nuke_python_ide.jpg" alt="Nuke Python IDE UI">
</div>

<!-- Lightbox 2 -->
<div id="lightbox2" class="lightbox">
    <a href="#" class="close">&times;</a>
    <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_01.jpg" alt="Settings UI 1">
</div>

<!-- Lightbox 3 -->
<div id="lightbox3" class="lightbox">
    <a href="#" class="close">&times;</a>
    <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_02.jpg" alt="Settings UI 2">
</div>

<!-- Lightbox 4 -->
<div id="lightbox4" class="lightbox">
    <a href="#" class="close">&times;</a>
    <img src="https://github.com/faithcure/nuke_code_project/blob/master/settings_03.jpg" alt="Settings UI 3">
</div>

</body>
</html>

### 🌟 Why Nuke Python IDE?
- Eliminate the need for external IDEs, with a fully integrated coding environment inside Nuke.
- Write, debug, and test your scripts directly within the Nuke ecosystem.
- Streamline tool creation, plugin development, and automation scripts for your pipeline.

### 🎯 Who Is It For?
- **VFX Artists**: Automate repetitive tasks and customize your workflow with ease.
- **Technical Directors**: Develop sophisticated tools and pipeline scripts without leaving Nuke.
- **Developers**: Build and test Nuke plugins with real-time feedback.

---

## 💡 Features

### 🧩 **Seamless Nuke Integration**
- Write and execute Python scripts directly inside Nuke, eliminating the need for external tools.
- Test your custom gizmos, nodes, and plugins instantly.

### 🎨 **Enhanced Syntax Highlighting**
- Beautiful syntax highlighting for Python and Nuke-specific modules (`nuke`, `nukescripts`).
- Clear distinction between functions, classes, and keywords for better readability.

### 🕹️ **Customizable Workspace**
- Fully dockable panels: **Outliner**, **Header**, **Console**, and more.
- Save and load custom UI layouts to match your preferred workflow.
- Dark mode and scalable fonts/icons for visual comfort.

### 🚀 **Version Control Integration**
- Built-in GitHub support for `commit`, `push`, and `pull`.
- View and manage repositories directly from the IDE.
- Keep your projects versioned and collaborate effortlessly.

### 🔍 **Advanced Error Management**
- Real-time error reporting with clickable error messages.
- Built-in Python console for debugging your scripts.

### 🛠️ **Powerful Features for Professionals**
- **Outliner**: Navigate your classes, methods, and functions effortlessly.
- **Search Bar**: Quickly locate specific code snippets or keywords.
- **Multi-File Tabs**: Open, edit, and organize multiple files in a tabbed interface.

### 📚 **Learning Resources**
> 🚧 **Note**: Tutorials are coming soon.
---

## 📥 Installation
> 🚧 **Note**: Installation instructions will be available soon as the project progresses for the all users.
> if you want to install:
- Please refer to the [🤝 Contributions & Development](#-contributions--development) section...

---

## 🛠️ Usage
1. Launch the IDE within **Foundry Nuke**.
2. Open your Python scripts or create new ones from the **File** menu.
3. Use the **Outliner** to navigate and the **Console** for debugging.
4. Test your scripts directly in Nuke with real-time execution.
5. Save, commit, and push changes to GitHub, all from within the IDE.

---

## 🖥️ Compatibility
- **Operating Systems**: Windows, macOS, Linux. (Not tested macOS or Linux yet!)
- **Nuke Versions**: Fully tested on **Nuke 13.0+**.
- **Python Versions**: Supports Python 3.6 and later.

---
## 🤝 Contributions & Development

I warmly welcome your contributions and suggestions to improve the **Nuke Python IDE**. Here's how you can get involved and what you should know:

### Guidelines for Contributions:
   - Any enhancements, features, or fixes you submit and that are accepted into the project will automatically fall under the existing free license. By contributing, you agree to these terms.
   - Advanced versions may include features or fixes you add. While I will credit you (e.g., by name or GitHub username) in the project documentation or release notes, no financial or licensing claims will be associated.
   - Fork the repository, make your changes, and submit a pull request. Please ensure your changes are thoroughly tested and well-documented.
   - Share feature ideas, report bugs, or enhance existing functionalities.  
   - Improve the documentation or create tutorial content for the IDE.
   - You can find in this file for the Developer instructions: 
**💡 Developer Guidelines:** Don't forget to read the [Installation Guide](Installation-and-Contributing.md) for more details.


Let’s build the future of Python scripting in Nuke together! 🚀
---
## 📄 Licenses

If you choose to install external fonts such as JetBrains Mono or other custom fonts, they are not covered under the internal license. However, these can be freely used under their respective open licenses.
Operations such as GitHub or PyCharm connections do not have any license binding or restrictions.
The **Nuke Python IDE** plugin is distributed as a **"Lite Version"**, completely free to use and open for further development. Contributions are welcome!
eface is available under the SIL Open Font License 1.1 license and can be used free of charge for both commercial and non-commercial purposes.

---

### 💬 Let's Connect!
Have feedback or suggestions? Feel free to [open an issue](https://github.com/faithcure/nuke_code_project/issues/new) or contribute to this project. Your input is invaluable! 💖
