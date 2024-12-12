from PySide2.QtWidgets import QTextEdit

class ConsoleWidget(QTextEdit):
    def __init__(self, parent=None):
        super(ConsoleWidget, self).__init__(parent)
        self.setReadOnly(False)  # Konsolda yazma işlemi yapılacak
        self.command_history = []  # Girilen komutları saklamak için bir liste
        self.history_index = -1

    def run_command(self, command):
        """Python komutunu çalıştırır ve sonucu gösterir."""
        try:
            exec(command)  # Gelen Python komutunu çalıştırır
        except Exception as e:
            self.append(f"Error: {e}")
