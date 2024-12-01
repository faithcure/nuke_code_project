# 🤝 Contributions & Development

Welcome to the **Nuke Python IDE Contributions & Development** page! We value your input and collaboration to help make this project the best it can be.

---

## 🌟 How You Can Contribute

We welcome contributions in the following areas:

1. **Bug Reports**  
   - Found an issue? Open a [new issue](https://github.com/your-repo/issues) to let us know.
   - Provide a detailed description, including steps to reproduce the issue and the expected vs. actual behavior.

2. **Feature Suggestions**  
   - Have an idea for a new feature? Share it with us via the [discussions tab](https://github.com/your-repo/discussions) or open an issue.
   - Explain the feature, how it improves the project, and any implementation ideas.

3. **Code Contributions**  
   - Fork the repository, make your changes, and submit a pull request (PR).
   - Ensure your code is clean, tested, and aligns with the project’s style and guidelines.

4. **Documentation Enhancements**  
   - Help improve existing documentation or create tutorials for the IDE.
   - Contribute translations to make the IDE accessible globally.

---

## 📜 Contribution Guidelines

Before contributing, please adhere to the following:

1. **Clone from GitHub**  
   - Clone it locally and set up the project as described in the HERE.
   - Install folder '(nuke_code_project)' the inside ".nuke" environment.
   - `menu.py`, `init_ide.py`, `init.py`: Just copy this files in the ".nuke".
   > ⚠️ if you have `menu.py`, `init.py` please save them.
 
---

## 🛠️ Development Roadmap

Here are some key areas we are currently focusing on:

- **Dual Window Usage**: Allowing the main window to function both as a Nuke panel and as a standalone window.
- **Code Editing**: Streamlining and enhancing the process of organizing and modifying scripts.
- **AI Integration**: Developing and refining AI functionalities for better support and automation.
- **Simplifying Coding**: Making coding as straightforward as possible for users.
- **Bug Fixes**: Identifying and resolving issues to improve stability and performance.
- **Multi-Platform Testing**: Ensuring the IDE works seamlessly across different platforms and environments.
- **Community Contributions**: Encouraging feedback and collaboration to enhance the project further.
- **THANKS**
---
# 📂 Project Structure

Below is an overview of the file and folder structure for better understanding:

```markdown
├── nuke_code_project
   ├── editor
      ├── ai                  # Under construction. Need help! :D
      ├── dialogs             # Important dialogs are handled here.
      ├── nodes               # Nuke feature completer settings.
      ├── settings            
         ├── modules          # External modules are stored here.
            ├── Pygments      # Syntax highlighting uses this module. 
            ├── Git           # Optional GitHub Pull, Push, Commit settings.
         ├── github_utils.py   # GitHub utility functions.
         ├── possible_paths.py # Path definitions and utilities.
         ├── settings_ui.py    # UI settings and related functionalities.
         ├── settings_ux.py    # Dynamic UX settings.
      ├── code_editor.py      # Handles settings for the code panel.
      ├── completer.py        # Configuration for code completion.
      ├── console.py          # Executes external Python code. Under development.
      ├── core.py             # Main UI settings and hooks.
      ├── editor_window.py    # Main window widgets, signals, and slots.
      ├── inline_ghosting.py  # Line-by-line completer functionality.
      ├── main_toolbar.py     # Toolbar setup and settings.
      ├── nlink.py            # Updates app with one click for offline Nuke use.
      ├── output.py           # Executes Python code within Nuke.
   ├── assets
      ├── dynamic_data
         ├── nodeList.json       # Detailed node list from Nuke. Clicking the update button upgrades this JSON from Nuke (via nlink).
         ├── nuke_functions.json # Detailed functions for AI or suggestions. Upgraded via nlink.
      ├── JetBrains              # Contains JetBrains fonts.
   ├── trash         # Temporary folder for discarded items.
   ├── ui            # Used for graphical assets like icons, images, etc.  

