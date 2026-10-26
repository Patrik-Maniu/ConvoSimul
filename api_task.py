from PyQt6.QtCore import QThread


class ApiTask(QThread):
    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.function()
        except Exception as error:
            self.error = f"{type(error).__name__}: {error}"