# gui_setup.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QFormLayout, QMessageBox, QDialog
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
        
        # Widgets
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

        # Buttons / status
        self.start_btn = QPushButton("Start")
        self.reload_btn = QPushButton("Reload Models")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.turns = QTextEdit()
        self.turns.setObjectName("turns")
        self.turns.setPlaceholderText("Enter the number of turns... (must be a positive integer & if empty defaults to 5)")
        self.conversation_name = QTextEdit()
        self.conversation_name.setObjectName("Conversation_name")
        self.conversation_name.setPlaceholderText("Enter the conversation name...")

        # Layouts for each model column
        col1 = QFormLayout()
        col1.addRow("Model A:", self.models_combo)
        col1.addRow("System Prompt for A:", self.sys_edit)

        col2 = QFormLayout()
        col2.addRow("Model B:", self.models_combo_2)
        col2.addRow("System Prompt for B:", self.sys_edit_2)

        # Horizontal layout to hold the two columns
        columns = QHBoxLayout()
        columns.addLayout(col1)
        columns.addLayout(col2)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reload_btn)
        btn_row.addWidget(self.turns)
        btn_row.addWidget(self.conversation_name)
        btn_row.addStretch(1)

        # Root layout
        root = QVBoxLayout(self)
        root.addLayout(columns)
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
        name = self.conversation_name.toPlainText().strip()
        turns = self.turns.toPlainText().strip()

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
        A = [{"role": "system", "content": setup_1}]
        B = [{"role": "system", "content": setup_2}]
        PDF = [{"role": "setup for A:", "content": setup_1}, {"role": "setup for B:", "content": setup_2}]
        # Prepare arguments exactly as your original talk() expects
        talk_args = (
            name,                   # conversation name
            model_1["deployment"],  # model A
            model_2["deployment"],  # model B
            A,
            B,
            PDF,
            turns_int               # number of turns to run/advance
        )

        # Keep a reference so it doesn't get garbage collected
        self.conv_dialog = ConversationDialog(talk_args=talk_args, parent=self)
        self.conv_dialog.setModal(True)   # optional: make it modal
        self.conv_dialog.show()

class ConversationDialog(QDialog):
    """
    Dialog that displays conversation output from talk() and lets the user
    request the next chunk (Next) or quit the program (Stop).
    """
    def __init__(self, talk_args: tuple, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversation")
        self.resize(700, 500)
        self.name, self.deploy_A, self.deploy_B, self.A, self.B, self.PDF, self.turns = talk_args
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
                result = talk(msgs=self.A, dep=self.deploy_A)
            else:
                result = talk(msgs=self.B, dep=self.deploy_B)
        except Exception as e:
            # Show error in the text area and disable Next
            self.output.append(f"\n[Error calling talk()]: {e}")
            self.next_btn.setEnabled(False)
            return

        # Append result to output
        if self.output.toPlainText():
            if self.turn:
                self.output.append("\n" + "A: " + "\n")
            else:
                self.output.append("\n" + "B: " + "\n")
            self.output.append("\n" + result)
        else:
            if self.turn:
                self.output.setPlainText("A: " + "\n")
            else:
                self.output.setPlainText("B: " + "\n")
            self.output.append(result)

        # Scroll to bottom
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        
        # Append new message to message lists and change turn
        if self.turn:
            self.A.append({"role": "assistant", "content": result})
            self.B.append({"role": "user", "content": result})
            self.PDF.append({"role": "A:", "content": result})
        else:
            self.A.append({"role": "user", "content": result})
            self.B.append({"role": "assistant", "content": result})
            self.PDF.append({"role": "B:", "content": result})
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
