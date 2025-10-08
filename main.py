# gui_setup.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QFormLayout, QMessageBox
)


def load_models_config(config_path: Path) -> List[Dict[str, Any]]:
    """Load and validate model list from JSON config file. Returns [] if not found."""
    if not config_path.exists():
        return []  # Don't crash; we'll just show a warning in the UI.

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    models = data.get("models")
    if not isinstance(models, list):
        return []

    valid_models = []
    for model in models:
        if isinstance(model, dict) and model.get("deployment") and model.get("model_name"):
            valid_models.append({"deployment": model["deployment"], "model_name": model["model_name"]})
    return valid_models


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Conversation Setup")
        self.resize(560, 420)

        # Paths
        self.config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"

        # Widgets
        self.models_combo = QComboBox()
        self.models_combo.setObjectName("models")
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setObjectName("starting_prompt")
        self.prompt_edit.setPlaceholderText("Enter the starting prompt...")

        # Buttons / status
        self.start_btn = QPushButton("Start")
        self.reload_btn = QPushButton("Reload Models")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        # Layout
        form = QFormLayout()
        form.addRow("Models:", self.models_combo)
        form.addRow("Starting Prompt:", self.prompt_edit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reload_btn)
        btn_row.addStretch(1)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(btn_row)
        root.addWidget(self.status_label)

        # Signals
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.reload_btn.clicked.connect(self.populate_models)

        # Populate
        self.populate_models()

    def populate_models(self):
        """Load models from JSON file into combo box. Never crashes the app."""
        self.models_combo.clear()
        try:
            models = load_models_config(self.config_path)
        except Exception as e:
            QMessageBox.warning(self, "Error Loading Models", f"Could not read config:\n{e}")
            self.status_label.setText("Status: failed to load models.")
            return

        if not models:
            self.status_label.setText(
                f"No models found. Expected JSON at:\n{self.config_path}"
            )
            return

        for m in models:
            label = f"{m['deployment']} — {m['model_name']}"
            self.models_combo.addItem(label, userData=m)

        self.status_label.setText(f"Loaded {len(models)} model(s) from {self.config_path}")

    def on_start_clicked(self):
        """Import request.start lazily and call it."""
        if self.models_combo.count() == 0:
            QMessageBox.warning(self, "No Models", "No models are loaded. Check your config and reload.")
            return

        data = self.models_combo.currentData()
        if not data or "deployment" not in data:
            QMessageBox.warning(self, "Invalid Selection", "Selected model entry is invalid.")
            return

        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a starting prompt.")
            return

        # Lazy import so a bad conversation.py doesn't kill the window before it shows.
        try:
            from conversation import talk  # noqa
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import talk() from conversation.py:\n{e}")
            return

        try:
            talk(data["deployment"], prompt)
        except Exception as e:
            QMessageBox.critical(self, "talk() Error", f"talk(model, prompt) raised an error:\n{e}")
            return

        QMessageBox.information(self, "Started", f"Conversation started with model '{data['deployment']}'.")
        self.status_label.setText(f"Status: started with model '{data['deployment']}'.")


def main():
    import sys
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
