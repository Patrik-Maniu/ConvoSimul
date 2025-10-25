# gui_setup.py
from __future__ import annotations
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox
)
from main_window import MainWindow
def main():
    # Create the app no matter what, so we can show dialogs instead of silent exits.
    app = QApplication(sys.argv)
    try:
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        # Last-resort visible error if construction failed.
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Fatal Error")
        msg.setText("The application encountered a fatal error and must close.")
        msg.setInformativeText(str(e))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(1)


if __name__ == "__main__":
    main()
