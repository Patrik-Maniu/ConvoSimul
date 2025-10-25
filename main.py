# gui_setup.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QFormLayout, QMessageBox, QDialog, QSlider, QFileDialog
)
from PDFer import export_conversation_to_pdf


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
        self.labels_slider_map: Dict[QSlider, QLabel] = {}
        # Widgets
            # Naming models
        self.name_A = QLineEdit()
        self.name_A.setObjectName("Name for A inside conversation")
        self.name_B = QLineEdit()
        self.name_B.setObjectName("Name for B inside conversation")

            # First model boxes
        self.models_combo = QComboBox()
        self.models_combo.setObjectName("model")
        self.sys_edit = QTextEdit()
        self.sys_edit.setObjectName("System_prompt")
        self.sys_edit.setPlaceholderText("Enter the starting prompt...")

            # Second model boxes
        self.models_combo_2 = QComboBox()
        self.models_combo_2.setObjectName("model_2")
        self.sys_edit_2 = QTextEdit()
        self.sys_edit_2.setObjectName("System_prompt_2")
        self.sys_edit_2.setPlaceholderText("Enter the starting prompt...")

            # Settings A
                # Seed
        self.seed_A = QLineEdit()
        self.seed_A.setObjectName("seed_A")
        self.seed_A.setPlaceholderText("Enter seed (must be a positive integer & if empty defaults to random chosen by the server, deterministic behavior is not guaranteed)")

                # Max tokens
        self.max_tokens_A = QLineEdit()
        self.max_tokens_A.setObjectName("max_tokens_A")
        self.max_tokens_A.setPlaceholderText("Enter max_tokens for A... (must be a positive integer & if empty defaults to 1000)")

            # Settings B
                # Seed
        self.seed_B = QLineEdit()
        self.seed_B.setObjectName("seed_B")
        self.seed_B.setPlaceholderText("Enter seed (must be a positive integer & if empty defaults to random chosen by the server, deterministic behavior is not guaranteed)")

                # Max tokens
        self.max_tokens_B = QLineEdit()
        self.max_tokens_B.setObjectName("max_tokens_B")
        self.max_tokens_B.setPlaceholderText("Enter max_tokens for B... (must be a positive integer & if empty defaults to 1000)")
        
            # Simulation settings
        self.turns = QLineEdit()
        self.turns.setObjectName("turns")
        self.turns.setPlaceholderText("Enter the number of turns... (must be a positive integer & if empty defaults to 5)")
        self.file_name = QLineEdit()
        self.file_name.setObjectName("File_name")
        self.file_name.setPlaceholderText("Enter the file name...")

            # Buttons / status
        self.start_btn = QPushButton("Start")
        self.reload_btn = QPushButton("Reload Models")
        self.save_presets_btn = QPushButton("Save Presets")
        self.load_presets_btn = QPushButton("Load Presets")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

            # Layouts for each model column
        col1 = QFormLayout()
        col1.addRow("Name for Model A:", self.name_A)
        col1.addRow("Model A:", self.models_combo)
        col1.addRow("System Prompt for A:", self.sys_edit)
        col1.addRow("Seed for A:", self.seed_A)
        col1.addRow("Max tokens for A:", self.max_tokens_A)

        col2 = QFormLayout()
        col2.addRow("Name for Model B:", self.name_B)
        col2.addRow("Model B:", self.models_combo_2)
        col2.addRow("System Prompt for B:", self.sys_edit_2)
        col2.addRow("Seed for B:", self.seed_B)
        col2.addRow("Max tokens for B:", self.max_tokens_B)

            # Horizontal layout to hold the two columns
        columns = QHBoxLayout()
        columns.addLayout(col1)
        columns.addLayout(col2)

            # General settings row
        settings_row = QVBoxLayout()
        settings_row.addWidget(QLabel("Turns:"))
        settings_row.addWidget(self.turns)
        settings_row.addWidget(QLabel("File Name:"))
        settings_row.addWidget(self.file_name)

            # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reload_btn)
        btn_row.addWidget(self.save_presets_btn)
        btn_row.addWidget(self.load_presets_btn)

        btn_row.addStretch(1)

            # Root layout
        root = QVBoxLayout(self)
        root.addLayout(columns)
        root.addLayout(settings_row)
        root.addLayout(btn_row)
        root.addWidget(self.status_label)


            # Signals
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.reload_btn.clicked.connect(self.populate_models)
        self.save_presets_btn.clicked.connect(self.save_presets)
        self.load_presets_btn.clicked.connect(self.load_presets)

            # Populate
        self.populate_models()

    def populate_models(self):
        """Load models from JSON file into combo box. Never crashes the app."""
        self.models_combo.clear()
        self.models_combo_2.clear()
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
            self.models_combo_2.addItem(label, userData=m)
        
        self.status_label.setText(f"Loaded {len(models)} model(s) from {self.config_path}")
    
    def on_start_clicked(self):
        if self.models_combo.count() == 0 or self.models_combo_2.count() == 0:
            QMessageBox.warning(self, "No Models", "No models are loaded. Check your config and reload.")
            return

        model_1 = self.models_combo.currentData()
        model_2 = self.models_combo_2.currentData()
        if not model_1 or "deployment" not in model_1:
            QMessageBox.warning(self, "Invalid Selection", "Selected model entry for Model A is invalid.")
            return
        if not model_2 or "deployment" not in model_2:
            QMessageBox.warning(self, "Invalid Selection", "Selected model entry for Model B is invalid.")
            return

        setup_1 = self.sys_edit.toPlainText().strip()
        setup_2 = self.sys_edit_2.toPlainText().strip()
        name = self.file_name.text().strip()
        turns = self.turns.text().strip()

        if not setup_1:
            QMessageBox.warning(self, "Empty System setup for Model A", "Please enter a system prompt.")
            return
        if not setup_2:
            QMessageBox.warning(self, "Empty System setup for Model B", "Please enter a system prompt.")
            return

        try:
            turns_int = int(turns)
            if turns_int <= 0:
                raise ValueError("Number of turns must be positive.")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Turns", f"Please enter a valid number of turns:\n{e}")
            return
        name_A = self.name_A.text().strip()
        name_B = self.name_B.text().strip()
        config_A = (
            int(self.seed_A.text() if self.seed_A.text().strip().isdigit() else 0),
            int(self.max_tokens_A.text() if self.max_tokens_A.text().strip().isdigit() else 1000),
        )
        config_B = (
            int(self.seed_B.text() if self.seed_B.text().strip().isdigit() else 0),
            int(self.max_tokens_B.text() if self.max_tokens_B.text().strip().isdigit() else 1000),
        )
        if config_A[0] == 0:
            config_A = (None, config_A[1])
        if config_B[0] == 0:
            config_B = (None, config_B[1])
        A = [{"role": "system", "content": setup_1}]
        B = [{"role": "system", "content": setup_2}]
        PDF = [{"role": f"setup for {name_A}:", "content": f"System prompt: {setup_1}\n Max tokens: {config_A[1]}\n Seed: {config_A[0]}"},
               {"role": f"setup for {name_B}:", "content": f"System prompt: {setup_2}\n Max tokens: {config_B[1]}\n Seed: {config_B[0]}" }]
        # Prepare arguments exactly as your original talk() expects
        talk_args = (
            name,
            model_1["deployment"],
            model_2["deployment"],
            A,
            B,
            PDF,
            turns_int,
            name_A,
            name_B,
            config_A,
            config_B
        )

        # Keep a reference so it doesn't get garbage collected
        self.conv_dialog = ConversationDialog(talk_args=talk_args, parent=self)
        self.conv_dialog.setModal(True)   # optional: make it modal
        self.conv_dialog.show()

    def save_presets(self):
        # Save current settings to a JSON file.
        file_name = self.file_name.text().strip()
        presets = {
            "name_A": self.name_A.text(),
            "name_B": self.name_B.text(),
            "sys_A": self.sys_edit.toPlainText(),
            "sys_B": self.sys_edit_2.toPlainText(),
            "seed_A": self.seed_A.text(),
            "max_tokens_A": self.max_tokens_A.text(),
            "seed_B": self.seed_B.text(),
            "max_tokens_B": self.max_tokens_B.text(),
            "turns": self.turns.text(),
            "file_name": file_name,
        }
        # Ensure the subfolder 'presets' exists
        os.makedirs("presets", exist_ok=True)
        # Construct the full path (add .json extension if missing)
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        file_path = os.path.join("presets", file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=4)
            self.status_label.setText(f"Status: Preset saved to {file_path}")
            print(f"Preset saved successfully to {file_path}")
        except Exception as e:
            print(f"Error saving preset: {e}")

    def load_presets(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",         # Window title
            "",                       # Starting directory ("" = current)
            "JSON Files (*.json);;All Files (*)"  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"Loading preset from {file_name}...")
        with open(file_name, "r") as f:
            presets = json.load(f)
            self.name_A.setText(presets.get("name_A", ""))
            self.name_B.setText(presets.get("name_B", ""))
            self.sys_edit.setPlainText(presets.get("sys_A", ""))
            self.sys_edit_2.setPlainText(presets.get("sys_B", ""))
            self.seed_A.setText(presets.get("seed_A", ""))
            self.max_tokens_A.setText(presets.get("max_tokens_A", ""))
            self.seed_B.setText(presets.get("seed_B", ""))
            self.max_tokens_B.setText(presets.get("max_tokens_B", ""))
            self.turns.setText(presets.get("turns", ""))
            self.file_name.setText(presets.get("file_name", ""))
        return

class ConversationDialog(QDialog):
    """
    Dialog that displays conversation output from talk() and lets the user
    request the next chunk (Next) or quit the program (Stop).
    """
    def __init__(self, talk_args: tuple, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversation")
        self.resize(700, 500)
        self.name, self.deploy_A, self.deploy_B, self.A, self.B, self.PDF, self.turns, self.name_A, self.name_B, self.config_A, self.config_B = talk_args
        self.turn = True
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)

        self.next_btn = QPushButton("Next", self)
        self.stop_btn = QPushButton("Stop", self)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.next_btn)
        btns.addWidget(self.stop_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addLayout(btns)

        self.next_btn.clicked.connect(self.on_next_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.on_next_clicked()

    def on_next_clicked(self):
        # Lazy import so a bad conversation.py doesn't kill the window before it shows.
        try:
            from conversation import talk
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import talk() from conversation.py:\n{e}")
            return
        
        try:
            if self.turn:
                result = talk(msgs=self.A, dep=self.deploy_A, config=self.config_A)
            else:
                result = talk(msgs=self.B, dep=self.deploy_B, config=self.config_B)
        except Exception as e:
            # Show error in the text area and disable Next
            self.output.append(f"\n[Error calling talk()]: {e}")
            self.next_btn.setEnabled(False)
            return

        # Append result to output
        if self.output.toPlainText():
            if self.turn:
                self.output.append("\n" + f"{self.name_A}: " + "\n")
            else:
                self.output.append("\n" + f"{self.name_B}: " + "\n")
            self.output.append("\n" + result)
        else:
            if self.turn:
                self.output.setPlainText(f"{self.name_A}: " + "\n")
            else:
                self.output.setPlainText(f"{self.name_B}: " + "\n")
            self.output.append(result)

        # Scroll to bottom
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        
        # Append new message to message lists and change turn
        if self.turn:
            self.A.append({"role": "assistant", "content": result})
            self.B.append({"role": "user", "content": result})
            self.PDF.append({"role": f"{self.name_A}:", "content": result})
        else:
            self.A.append({"role": "user", "content": result})
            self.B.append({"role": "assistant", "content": result})
            self.PDF.append({"role": f"{self.name_B}:", "content": result})
        self.turn = not self.turn
        self.turns -= 1
        if self.turns == 0:
            self.on_stop_clicked()

    def on_stop_clicked(self):
        # Close the entire program
        export_conversation_to_pdf(messages=self.PDF, name=self.name)
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

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
