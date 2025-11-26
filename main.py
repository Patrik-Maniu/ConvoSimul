from __future__ import annotations
import json
import os
from pathlib import Path
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox
)
from main_window import MainWindow

def import_lan_pack():
    config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
    if not config_path.exists():
        return []  # Don't crash; we'll just show a warning in the UI.

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lan_pack = data.get("lan_pack")
    language_path = Path(__file__).resolve().parent / "language_packs" / lan_pack
    if not language_path.exists():
        first_lan = os.listdir(Path(__file__).resolve().parent / "language_packs")[0]
        language_path = Path(__file__).resolve().parent / "language_packs" / first_lan
    with language_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # Create the app no matter what, so we can show dialogs instead of silent exits.
    app = QApplication(sys.argv)
    lan_pack = import_lan_pack().get("main.py")
    try:
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        # Last-resort visible error if construction failed.
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(lan_pack.get("window_title"))
        msg.setText(lan_pack.get("error_message"))
        msg.setInformativeText(str(e))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(1)


if __name__ == "__main__":
    main()
