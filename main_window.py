import json
import os
from pathlib import Path
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
    QFileDialog,
    QCheckBox,
)
from conversation_window import ConversationDialog
import re

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
        self.A_load = []
        self.B_load = []
        self.PDF_load = []

        # Paths
        self.config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
        
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

                # Color
        self.color_A = QLineEdit()
        self.color_A.setObjectName("color_A")
        self.color_A.setPlaceholderText("Enter color for A... (#RRGGBB)")
        
            # Settings B
                # Seed
        self.seed_B = QLineEdit()
        self.seed_B.setObjectName("seed_B")
        self.seed_B.setPlaceholderText("Enter seed (must be a positive integer & if empty defaults to random chosen by the server, deterministic behavior is not guaranteed)")

                # Max tokens
        self.max_tokens_B = QLineEdit()
        self.max_tokens_B.setObjectName("max_tokens_B")
        self.max_tokens_B.setPlaceholderText("Enter max_tokens for B... (must be a positive integer & if empty defaults to 1000)")
        
                # Color
        self.color_B = QLineEdit()
        self.color_B.setObjectName("color_B")
        self.color_B.setPlaceholderText("Enter color for B... (#RRGGBB)")

            # Simulation settings
        self.turns = QLineEdit()
        self.turns.setObjectName("turns")
        self.turns.setPlaceholderText("Enter the number of turns... (must be a positive integer & if empty defaults to 5)")
        self.referee = QCheckBox("Enable Referee (checks if conversation is going off-topic)")
        self.file_name = QLineEdit()
        self.file_name.setObjectName("File_name")
        self.file_name.setPlaceholderText("Enter the file name...")

            # Buttons / status
        self.start_btn = QPushButton("Start")
        self.reload_btn = QPushButton("Reload Models")
        self.save_presets_btn = QPushButton("Save Presets")
        self.load_presets_btn = QPushButton("Load Presets")
        self.flag_conversation_loaded = False
        self.load_conversation_btn = QPushButton("Load Conversation")
        self.flush_conversation_btn = QPushButton("Flush Conversations")
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

            # Layouts for each model column
        col1 = QFormLayout()
        col1.addRow("Name for Model A:", self.name_A)
        col1.addRow("Model A:", self.models_combo)
        col1.addRow("System Prompt for A:", self.sys_edit)
        col1.addRow("Seed for A:", self.seed_A)
        col1.addRow("Max tokens for A:", self.max_tokens_A)
        col1.addRow("Color for A:", self.color_A)

        col2 = QFormLayout()
        col2.addRow("Name for Model B:", self.name_B)
        col2.addRow("Model B:", self.models_combo_2)
        col2.addRow("System Prompt for B:", self.sys_edit_2)
        col2.addRow("Seed for B:", self.seed_B)
        col2.addRow("Max tokens for B:", self.max_tokens_B)
        col2.addRow("Color for B:", self.color_B)

            # Horizontal layout to hold the two columns
        columns = QHBoxLayout()
        columns.addLayout(col1)
        columns.addLayout(col2)

            # General settings row
        settings_row = QVBoxLayout()
        settings_row.addWidget(QLabel("Turns:"))
        settings_row.addWidget(self.turns)
        temp_HBox = QHBoxLayout()
        temp_HBox.addWidget(QLabel("Referee:"))
        temp_HBox.addWidget(self.referee)
        settings_row.addLayout(temp_HBox)
        settings_row.addWidget(QLabel("File Name:"))
        settings_row.addWidget(self.file_name)

            # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reload_btn)
        btn_row.addWidget(self.save_presets_btn)
        btn_row.addWidget(self.load_presets_btn)
        btn_row.addWidget(self.load_conversation_btn)
        btn_row.addWidget(self.flush_conversation_btn)

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
        self.load_conversation_btn.clicked.connect(self.load_conversation)
        self.flush_conversation_btn.clicked.connect(self.flush_conversation)

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
    
    @staticmethod
    def is_hex_color(s: str) -> bool:
        return bool(re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", s))


    def on_start_clicked(self):
        if self.models_combo.count() == 0 or self.models_combo_2.count() == 0:
            QMessageBox.warning(self, "No Models", "No models are loaded. Check your config and reload.")
            return

        model_1 = self.models_combo.currentData()
        model_2 = self.models_combo_2.currentData()
        if not model_1 or "deployment" not in model_1:
            QMessageBox.warning(self, "Invalid Selecti  on", "Selected model entry for Model A is invalid.")
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
            self.color_A.text().strip() if self.is_hex_color(self.color_A.text().strip()) else "#FF0000",
        )
        config_B = (
            int(self.seed_B.text() if self.seed_B.text().strip().isdigit() else 0),
            int(self.max_tokens_B.text() if self.max_tokens_B.text().strip().isdigit() else 1000),
            self.color_B.text().strip() if self.is_hex_color(self.color_B.text().strip()) else "#0000FF",
        )
        if config_A[0] == 0:
            config_A = (None, config_A[1], config_A[2])
        if config_B[0] == 0:
            config_B = (None, config_B[1], config_B[2])
        A = [{"role": "system", "content": setup_1}]
        B = [{"role": "system", "content": setup_2}]
        PDF = [{"role": f"system prompt for {name_A}:", "content": f"{setup_1}\n"},
                {"role": f"config for {name_A}:", "content": f"Max tokens: {config_A[1]}\n Seed: {config_A[0]}"},
                {"role": f"system prompt for {name_B}:", "content": f"{setup_2}\n"},
                {"role": f"config for {name_B}:", "content": f"Max tokens: {config_B[1]}\n Seed: {config_B[0]}"}]
        if self.flag_conversation_loaded:
            A.extend(self.A_load)
            B.extend(self.B_load)
            PDF.extend(self.PDF_load)
        # Prepare arguments exactly as your original talk() expects
        talk_args = (
            name,
            model_1["deployment"],
            model_2["deployment"],
            A,
            B,
            PDF,
            turns_int,
            self.referee.isChecked(),
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
            "color_A": self.color_A.text(),
            "seed_B": self.seed_B.text(),
            "max_tokens_B": self.max_tokens_B.text(),
            "color_B": self.color_B.text(),
            "turns": self.turns.text(),
            "referee": self.referee.isChecked(),
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
            "presets/",                       # Starting directory ("" = current)
            "JSON Files (*.json);;All Files (*)"  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"Loading preset from {file_name}...")
        with open(file_name, "r", encoding="utf-8") as f:
            presets = json.load(f)
            self.name_A.setText(presets.get("name_A", ""))
            self.name_B.setText(presets.get("name_B", ""))
            self.sys_edit.setPlainText(presets.get("sys_A", ""))
            self.sys_edit_2.setPlainText(presets.get("sys_B", ""))
            self.seed_A.setText(presets.get("seed_A", ""))
            self.max_tokens_A.setText(presets.get("max_tokens_A", ""))
            self.color_A.setText(presets.get("color_A", ""))
            self.seed_B.setText(presets.get("seed_B", ""))
            self.max_tokens_B.setText(presets.get("max_tokens_B", ""))
            self.color_B.setText(presets.get("color_B", ""))
            self.turns.setText(presets.get("turns", ""))
            self.referee.setChecked(presets.get("referee", False))
            self.file_name.setText(presets.get("file_name", ""))
        return

    def load_conversation(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",         # Window title
            "conversations/",                       # Starting directory ("" = current)
            "JSON Files (*.json);;All Files (*)"  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"Loading conversation from {file_name}...")
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.A_load = data["A"]
            self.B_load = data["B"]
            for msg in self.A_load:
                if msg["role"] == "assistant":
                    self.PDF_load.append({"role": f"{self.name_A.text().strip()}:", "content": msg["content"]})
                if msg["role"] == "user":
                    self.PDF_load.append({"role": f"{self.name_B.text().strip()}:", "content": msg["content"]})
            self.flag_conversation_loaded = True
            self.status_label.setText(f"Conversation loaded from {file_name}. You can now start the simulation.")
        return
    def flush_conversation(self):
        self.flag_conversation_loaded = False
        return