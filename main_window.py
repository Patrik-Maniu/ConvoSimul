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

def load_models_config() -> List[Dict[str, Any]]:
    config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
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

def load_languages_list() -> List[str]:
    return os.listdir(Path(__file__).resolve().parent / "language_packs")

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

def what_language():
    config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
    if not config_path.exists():
        return []  # Don't crash; we'll just show a warning in the UI.

    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    lan_pack = data.get("lan_pack")
    return lan_pack

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.lan_pack = import_lan_pack().get("main_window.py")
        self.setWindowTitle(self.lan_pack.get("window_title"))
        self.resize(560, 420)
        self.A_load = []
        self.B_load = []
        self.PDF_load = []
        
        # Widgets
        self.language_select = QComboBox()
            # Naming models
        self.name_A = QLineEdit()
        self.name_B = QLineEdit()

            # First model boxes
        self.models_combo = QComboBox()
        self.sys_edit = QTextEdit()
        self.sys_edit.setPlaceholderText(self.lan_pack.get("system_prompt_placeholder"))

            # Second model boxes
        self.models_combo_2 = QComboBox()
        self.sys_edit_2 = QTextEdit()
        self.sys_edit_2.setPlaceholderText(self.lan_pack.get("system_prompt_placeholder"))

            # Settings A
                # Seed
        self.seed_A = QLineEdit()
        self.seed_A.setPlaceholderText(self.lan_pack.get("seed_placeholder"))

                # Max tokens
        self.max_tokens_A = QLineEdit()
        self.max_tokens_A.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
                # Color
        self.color_A = QLineEdit()
        self.color_A.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        
            # Settings B
                # Seed
        self.seed_B = QLineEdit()
        self.seed_B.setPlaceholderText(self.lan_pack.get("seed_placeholder"))

                # Max tokens
        self.max_tokens_B = QLineEdit()
        self.max_tokens_B.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        
                # Color
        self.color_B = QLineEdit()
        self.color_B.setPlaceholderText(self.lan_pack.get("color_placeholder"))
            # Simulation settings
        self.turns = QLineEdit()
        self.turns.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.referee = QCheckBox(self.lan_pack.get("referee_checkbox_text"))
        self.file_name = QLineEdit()
        self.file_name.setPlaceholderText(self.lan_pack.get("file_name_placeholder"))

            # Buttons / status
        self.start_btn = QPushButton(self.lan_pack.get("start_button_text"))
        self.reload_btn = QPushButton(self.lan_pack.get("reload_models_button_text"))
        self.save_presets_btn = QPushButton(self.lan_pack.get("save_presets_button_text"))
        self.load_presets_btn = QPushButton(self.lan_pack.get("load_presets_button_text"))
        self.flag_conversation_loaded = False
        self.load_conversation_btn = QPushButton(self.lan_pack.get("load_conversation_button_text"))
        self.flush_conversation_btn = QPushButton(self.lan_pack.get("flush_conversation_button_text"))
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

            #Layout for language selection
        top = QHBoxLayout()
        top.addWidget(QLabel(self.lan_pack.get("language_select_description") + ":"))
        top.addWidget(self.language_select)

            # Layouts for each model column
        col1 = QFormLayout()
        col1.addRow(self.lan_pack.get("name_description") + " A:", self.name_A)
        col1.addRow(self.lan_pack.get("model_description") + " A:", self.models_combo)
        col1.addRow(self.lan_pack.get("system_prompt_description") + " A:", self.sys_edit)
        col1.addRow(self.lan_pack.get("seed_description") + " A:", self.seed_A)
        col1.addRow(self.lan_pack.get("max_tokens_description") + " A:", self.max_tokens_A)
        col1.addRow(self.lan_pack.get("color_description") + " A:", self.color_A)

        col2 = QFormLayout()
        col2.addRow(self.lan_pack.get("name_description") + " B:", self.name_B)
        col2.addRow(self.lan_pack.get("model_description") + " B:", self.models_combo_2)
        col2.addRow(self.lan_pack.get("system_prompt_description") + " B:", self.sys_edit_2)
        col2.addRow(self.lan_pack.get("seed_description") + " B:", self.seed_B)
        col2.addRow(self.lan_pack.get("max_tokens_description") + " B:", self.max_tokens_B)
        col2.addRow(self.lan_pack.get("color_description") + " B:", self.color_B)

            # Horizontal layout to hold the two columns
        columns = QHBoxLayout()
        columns.addLayout(col1)
        columns.addLayout(col2)

            # General settings row
        settings_row = QVBoxLayout()
        settings_row.addWidget(QLabel(self.lan_pack.get("turns_description")))
        settings_row.addWidget(self.turns)
        temp_HBox = QHBoxLayout()
        temp_HBox.addWidget(QLabel(self.lan_pack.get("referee_description")))
        temp_HBox.addWidget(self.referee)
        settings_row.addLayout(temp_HBox)
        settings_row.addWidget(QLabel(self.lan_pack.get("file_name_description")))
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
        root.addLayout(top)
        root.addLayout(columns)
        root.addLayout(settings_row)
        root.addLayout(btn_row)
        root.addWidget(self.status_label)

            # Populate
        self.populate_combos()

            # Signals
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.reload_btn.clicked.connect(self.populate_combos)
        self.save_presets_btn.clicked.connect(self.save_presets)
        self.load_presets_btn.clicked.connect(self.load_presets)
        self.load_conversation_btn.clicked.connect(self.load_conversation)
        self.flush_conversation_btn.clicked.connect(self.flush_conversation)
        self.language_select.currentIndexChanged.connect(self.on_language_change)

    def populate_combos(self):
        self.models_combo.clear()
        self.models_combo_2.clear()
        self.language_select.clear()
        try:
            models = load_models_config()
            languages = load_languages_list()
        except Exception as e:
            # CHANGE LANG PACK LATER
            QMessageBox.warning(self, self.lan_pack.get("load_models_warning_1"), f"{self.lan_pack.get("load_models_warning_2")}{e}")
            self.status_label.setText(self.lan_pack.get("load_models_warning_status"))
            return

        if not models or not languages:
            self.status_label.setText(
                # CHANGE LANG PACK LATER
                f"{self.lan_pack.get("load_models_no_models")}{Path(__file__).resolve().parent / "config" / "setupModels.json"}"
            )
            return

        for m in models:
            label = f"{m['deployment']} — {m['model_name']}"
            self.models_combo.addItem(label, userData=m)
            self.models_combo_2.addItem(label, userData=m)
        
        for lang in languages:
            self.language_select.addItem(lang)
        self.language_select.setCurrentText(what_language())
        self.status_label.setText(f"{self.lan_pack.get("load_models_loaded_status_1")} {len(models)} {self.lan_pack.get("load_models_loaded_status_2")} {Path(__file__).resolve().parent / "config" / "setupModels.json"}")

    @staticmethod
    def is_hex_color(s: str) -> bool:
        return bool(re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", s))

    def on_start_clicked(self):
        if self.models_combo.count() == 0 or self.models_combo_2.count() == 0:
            QMessageBox.warning(self, self.lan_pack.get("on_click_no_model_chosen_1"), self.lan_pack.get("on_click_no_model_loaded_2"))
            return

        model_1 = self.models_combo.currentData()
        model_2 = self.models_combo_2.currentData()
        if not model_1 or "deployment" not in model_1:
            QMessageBox.warning(self, self.lan_pack.get("on_click_model_invalid_1"), self.lan_pack.get("on_click_model_invalid_2") + " Model A " + self.lan_pack.get("on_click_model_invalid_3"))
            return
        if not model_2 or "deployment" not in model_2:
            QMessageBox.warning(self, self.lan_pack.get("on_click_model_invalid_1"), self.lan_pack.get("on_click_model_invalid_2") + " Model B " + self.lan_pack.get("on_click_model_invalid_3"))
            return

        setup_1 = self.sys_edit.toPlainText().strip()
        setup_2 = self.sys_edit_2.toPlainText().strip()
        name = self.file_name.text().strip()
        turns = self.turns.text().strip()

        if not setup_1:
            QMessageBox.warning(self, self.lan_pack.get("on_click_system_prompt_empty_1") + " Model A", self.lan_pack.get("on_click_system_prompt_empty_2"))
            return
        if not setup_2:
            QMessageBox.warning(self, self.lan_pack.get("on_click_system_prompt_empty_1") + " Model B", self.lan_pack.get("on_click_system_prompt_empty_2"))
            return

        try:
            turns_int = int(turns)
            if turns_int <= 0:
                raise ValueError(self.lan_pack.get("on_click_turns_not_positive"))
        except ValueError as e:
            QMessageBox.warning(self, self.lan_pack.get("on_click_turns_not_positive_warning_1"), f"{self.lan_pack.get("on_click_turns_not_positive_warning_2")}\n{e}")
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
            self.language_select.currentText(),
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
        os.makedirs(Path(__file__).resolve().parent / "outputs" / "presets", exist_ok=True)
        # Construct the full path (add .json extension if missing)
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        file_path = Path(__file__).resolve().parent / "outputs" / "presets" / file_name
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(presets, f, ensure_ascii=False, indent=4)
            self.status_label.setText(f"{self.lan_pack.get("preset_saved_status")} {file_path}")
        except Exception as e:
            print(f"Error saving preset: {e}")

    def load_presets(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",         # Window title
            "outputs/presets/",                       # Starting directory ("" = current)
            "JSON Files (*.json);;All Files (*)"  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"{self.lan_pack.get("preset_loading_status")} {file_name}...")
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
            "outputs/Conversations_JSON/",                       # Starting directory ("" = current)
            "JSON Files (*.json);;All Files (*)"  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"{self.lan_pack.get("conversation_loading_status")} {file_name}")
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
            self.status_label.setText(f"{self.lan_pack.get("conversation_loaded_status")} {file_name}")
        return
    
    def flush_conversation(self):
        self.flag_conversation_loaded = False
        self.status_label.setText(self.lan_pack.get("conversation_flushed_status"))
        return

    def on_language_change(self):
        selected_language = self.language_select.currentText()
        config_path = Path(__file__).resolve().parent / "language_packs" / selected_language
        if not config_path.exists():
            QMessageBox.warning(self, self.lan_pack.get("language_pack_not_found_1"), f"{self.lan_pack.get("language_pack_not_found_2")}{selected_language}")
            return
        with config_path.open("r", encoding="utf-8") as f:
            self.lan_pack = json.load(f).get("main_window.py")
        # Update all UI text elements
        self.setWindowTitle(self.lan_pack.get("window_title"))
        self.sys_edit.setPlaceholderText(self.lan_pack.get("system_prompt_placeholder"))
        self.sys_edit_2.setPlaceholderText(self.lan_pack.get("system_prompt_placeholder"))
        self.seed_A.setPlaceholderText(self.lan_pack.get("seed_placeholder"))
        self.max_tokens_A.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        self.color_A.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        self.seed_B.setPlaceholderText(self.lan_pack.get("seed_placeholder"))
        self.max_tokens_B.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        self.color_B.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        self.turns.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.referee.setText(self.lan_pack.get("referee_checkbox_text"))
        self.start_btn.setText(self.lan_pack.get("start_button_text"))
        self.reload_btn.setText(self.lan_pack.get("reload_models_button_text"))
        self.save_presets_btn.setText(self.lan_pack.get("save_presets_button_text"))
        self.load_presets_btn.setText(self.lan_pack.get("load_presets_button_text"))
        self.load_conversation_btn.setText(self.lan_pack.get("load_conversation_button_text"))
        self.flush_conversation_btn.setText(self.lan_pack.get("flush_conversation_button_text"))
        config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["lan_pack"] = selected_language
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)