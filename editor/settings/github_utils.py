import os
import sys
import json
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
    GIT_MODULES_AVAILABLE = True
except ImportError:
    GIT_MODULES_AVAILABLE = False


def get_status(editor_window):
    """Gets the current Git status."""
    if not GIT_MODULES_AVAILABLE:
        show_git_module_warning(editor_window)
        return

    if not check_project_directory(editor_window):
        return

    repo_path = editor_window.project_dir
    if not os.path.exists(repo_path):
        QMessageBox.warning(editor_window, "Error", "Project path does not exist.")
        return

    try:
        repo = Repo(repo_path)
        status = repo.git.status()
        editor_window.status_bar.showMessage(f"Git Status: {status}", 5000)
    except GitCommandError as e:
        editor_window.status_bar.showMessage(f"Status check failed: {e}", 5000)


from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

def get_commit_message(editor_window):
    """
    Opens a dialog to input a commit message.
    Returns the commit message if provided, otherwise None.
    """
    class CommitMessageDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Commit Message")
            self.setMinimumWidth(300)

            # Dialog layout
            layout = QVBoxLayout()

            # Instruction label
            layout.addWidget(QLabel("Enter commit message:"))

            # Commit message input
            self.commit_input = QLineEdit()
            layout.addWidget(self.commit_input)

            # Commit button
            self.commit_button = QPushButton("Commit")
            layout.addWidget(self.commit_button)

            self.setLayout(layout)

            # Commit button connected to accept
            self.commit_button.clicked.connect(self.accept)

        def get_message(self):
            return self.commit_input.text().strip()

    # Create and display dialog
    dialog = CommitMessageDialog(editor_window)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_message()
    return None


def commit_changes(editor_window, message=None):
    """Performs a Git commit with a dynamic commit message."""
    if not GIT_MODULES_AVAILABLE:
        show_git_module_warning(editor_window)
        return

    if not check_project_directory(editor_window):
        return

    repo_path = editor_window.project_dir
    if not os.path.exists(repo_path):
        QMessageBox.warning(editor_window, "Error", "Project path does not exist.")
        return

    # Get commit message dynamically if not provided
    if message is None:
        message = get_commit_message(editor_window)
        if not message:  # If no message, cancel the operation
            QMessageBox.warning(editor_window, "Commit Canceled", "Commit message cannot be empty.")
            return

    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            Repo.init(repo_path)

        repo = Repo(repo_path)
        repo.git.add(all=True)
        repo.index.commit(message)
        QMessageBox.information(editor_window, "Success", f"Changes committed with message: {message}")
    except GitCommandError as e:
        QMessageBox.critical(editor_window, "Commit Failed", f"Commit failed: {e}")
    except InvalidGitRepositoryError:
        QMessageBox.warning(editor_window, "Invalid Repository", "The selected path is not a valid Git repository.")



# Core Functions
def load_github_credentials(settings_file="settings.json"):
    """
    Loads GitHub credentials and repository URL from the settings file.
    Returns:
        tuple: A tuple containing the username, token, and repo URL.
    Raises:
        ValueError: If the settings file does not exist or required fields are missing.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, settings_file)

    try:
        if not os.path.exists(settings_path):
            raise ValueError(f"Settings file not found at: {settings_path}")

        with open(settings_path, "r", encoding="utf-8") as file:
            settings = json.load(file)

        github_data = settings.get("Github", {})
        username = github_data.get("github_username")
        token = github_data.get("github_token")
        repo_url = github_data.get("github_repo_url")

        if not username or not token or not repo_url:
            missing_fields = [
                field for field, value in {
                    "Username": username,
                    "Token": token,
                    "Repository URL": repo_url
                }.items() if not value
            ]
            raise ValueError(f"Missing fields in settings: {', '.join(missing_fields)}")

        return username, token, repo_url

    except Exception as e:
        raise ValueError(f"Failed to load GitHub credentials: {e}")


def push_to_github(editor_window, settings_file="settings.json"):
    """Pushes changes to the remote GitHub repository using credentials."""
    if not GIT_MODULES_AVAILABLE:
        show_git_module_warning(editor_window)
        return

    if not check_project_directory(editor_window):
        return

    repo_path = editor_window.project_dir
    if not os.path.exists(repo_path):
        QMessageBox.critical(editor_window, "Error", "Project path does not exist.")
        return

    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            QMessageBox.critical(editor_window, "Invalid Repository", "The selected path is not a valid Git repository.")
            return

        username, token, repo_url = load_github_credentials(settings_file)
        repo = Repo(repo_path)

        if not repo.remotes:
            repo.create_remote("origin", repo_url)
            QMessageBox.information(editor_window, "Remote Added", "Remote repository added successfully.")

        origin = repo.remotes.origin
        secure_url = repo_url.replace("https://", f"https://{username}:{token}@")
        origin.set_url(secure_url)

        current_branch = repo.active_branch
        if current_branch.tracking_branch() is None:
            origin.push(refspec=f"{current_branch.name}:{current_branch.name}")
            current_branch.set_tracking_branch(origin.refs[current_branch.name])
            QMessageBox.information(editor_window, "Upstream Set",
                                    f"Upstream branch set to '{origin.name}/{current_branch.name}'.")

        origin.push()
        QMessageBox.information(editor_window, "Success", "Changes pushed to GitHub successfully.")
        origin.set_url(repo_url)

    except GitCommandError as e:
        QMessageBox.critical(editor_window, "Push Failed", f"Push failed: {e}")
    except AttributeError:
        QMessageBox.critical(editor_window, "Invalid Repository", "No remote repository found.")
    except ValueError as e:
        QMessageBox.critical(editor_window, "Error", str(e))
    except Exception as e:
        QMessageBox.critical(editor_window, "Unexpected Error", f"An unexpected error occurred: {e}")

def add_remote(editor_window, repo_name, settings_file="settings.json"):
    """Adds a Git remote using credentials."""
    if not GIT_MODULES_AVAILABLE:
        show_git_module_warning(editor_window)
        return

    repo_path = editor_window.project_dir
    if not os.path.exists(repo_path):
        QMessageBox.warning(editor_window, "Error", "Project path does not exist.")
        return

    try:
        # Load GitHub credentials
        username, token = load_github_credentials(settings_file)

        # Construct the remote URL
        remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"

        repo = Repo(repo_path)
        if not repo.remotes:
            repo.create_remote("origin", remote_url)
            editor_window.status_bar.showMessage("Remote repository added successfully.", 5000)
        else:
            QMessageBox.warning(editor_window, "Remote Exists", "A remote repository is already configured.")
    except Exception as e:
        editor_window.status_bar.showMessage(f"Failed to add remote: {e}", 5000)



def pull_from_github(editor_window, settings_file="settings.json"):
    """Pulls changes from the remote GitHub repository using credentials."""
    if not GIT_MODULES_AVAILABLE:
        show_git_module_warning(editor_window)
        return

    if not check_project_directory(editor_window):
        return

    repo_path = editor_window.project_dir
    if not os.path.exists(repo_path):
        QMessageBox.critical(editor_window, "Error", "Project path does not exist.")
        return

    try:
        username, token, repo_url = load_github_credentials(settings_file)
        repo = Repo(repo_path)

        if not repo.remotes:
            QMessageBox.warning(editor_window, "No Remote", "No remote repository is configured.")
            return

        origin = repo.remotes.origin
        secure_url = repo_url.replace("https://", f"https://{username}:{token}@")
        origin.set_url(secure_url)

        origin.pull()
        QMessageBox.information(editor_window, "Success", "Changes pulled from GitHub successfully.")
        origin.set_url(repo_url)

    except GitCommandError as e:
        QMessageBox.critical(editor_window, "Pull Failed", f"Pull failed: {e}")
    except Exception as e:
        QMessageBox.critical(editor_window, "Unexpected Error", f"An unexpected error occurred: {e}")



# Utility Functions
def check_project_directory(editor_window):
    """Checks if the project directory is set."""
    if not editor_window.project_dir:
        QMessageBox.warning(
            editor_window,
            "Project Directory Not Set",
            "No project directory is set. Please open or create a project before performing Git operations."
        )
        return False
    return True

def show_git_module_warning(editor_window):
    """Shows a warning if Git modules are not installed."""
    QMessageBox.warning(
        editor_window,
        "Git Modules Not Installed",
        "Git modules are not installed. Please go to 'Settings' and install the required modules to use Git features."
    )

def install_git_modules():
    """Installs the required Git modules."""
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gitpython"])
        return True
    except Exception as e:
        return False


def add_git_install_option(settings_window):
    """Adds an option to install Git modules in the settings menu."""
    install_button = settings_window.create_button("Install Git Modules")
    install_button.clicked.connect(lambda: handle_git_install(settings_window))


def handle_git_install(settings_window):
    """Handles the Git module installation process."""
    if install_git_modules():
        QMessageBox.information(
            settings_window,
            "Installation Successful",
            "Git modules installed successfully. Please restart the application to use Git features."
        )
    else:
        QMessageBox.warning(
            settings_window,
            "Installation Failed",
            "Failed to install Git modules. Please check your internet connection or Python setup."
        )
