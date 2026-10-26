import json
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest import case
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
    QToolButton,
    QMenu,
    QWidgetAction,
)
from conversation_window import ConversationDialog
from test_mode import ConversationReplay
from referee_menu import RefereeMenu
import re
import base64
from docx import Document
import fitz

def image_to_base64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

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
        self.file_loaded = []
        self.file_filters = "All supported (*.txt *.md *.json *.docx *.png *.jpg *.jpeg *.gif *.bmp *.webp *.pdf)"
        
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
                # Max tokens
        self.max_tokens_A = QLineEdit()
        self.max_tokens_A.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
                # Color
        self.color_A = QLineEdit()
        self.color_A.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        
            # Settings B
                # Max tokens
        self.max_tokens_B = QLineEdit()
        self.max_tokens_B.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        
                # Color
        self.color_B = QLineEdit()
        self.color_B.setPlaceholderText(self.lan_pack.get("color_placeholder"))
            # Simulation settings
        self.turns = QLineEdit()
        self.turns.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.referee = RefereeMenu(
            self.lan_pack.get("referee_checkbox_text"),
            self,
        )
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
        self.load_file_btn = QPushButton(self.lan_pack.get("load_file_button_text"))
        self.flush_file_btn = QPushButton(self.lan_pack.get("flush_file_button_text"))
        self.test_mode_btn = QPushButton(
            self.lan_pack.get(
                "test_mode_button_text",
                "Modalità test (JSON)",
            )
        )
        self.test_mode_btn.setToolTip(
            "Legge i messaggi dal JSON mantenendo "
            "attivi i controlli selezionati."
        )
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
        col1.addRow(self.lan_pack.get("max_tokens_description") + " A:", self.max_tokens_A)
        col1.addRow(self.lan_pack.get("color_description") + " A:", self.color_A)

        col2 = QFormLayout()
        col2.addRow(self.lan_pack.get("name_description") + " B:", self.name_B)
        col2.addRow(self.lan_pack.get("model_description") + " B:", self.models_combo_2)
        col2.addRow(self.lan_pack.get("system_prompt_description") + " B:", self.sys_edit_2)
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
        btn_row.addWidget(self.load_file_btn)
        btn_row.addWidget(self.flush_file_btn)

        btn_row.addStretch(1)

            # Root layout
        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addLayout(columns)
        root.addLayout(settings_row)
        root.addLayout(btn_row)
        root.addWidget(self.status_label)
        root.addWidget(self.test_mode_btn)

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
        self.load_file_btn.clicked.connect(self.load_file)
        self.flush_file_btn.clicked.connect(self.flush_file)
        self.test_mode_btn.clicked.connect(self.on_test_mode_clicked)

    def populate_combos(self):
        self.models_combo.clear()
        self.models_combo_2.clear()
        try:
            models = load_models_config()
            languages = load_languages_list()
        except Exception as e:
            # CHANGE LANG PACK LATER
            QMessageBox.warning(self, self.lan_pack.get("load_models_warning_1"), f"{self.lan_pack.get("load_models_warning_2")}{e}")
            self.status_label.setText(self.lan_pack.get("load_models_warning_status"))
            return
        previous_signals = self.language_select.blockSignals(True)

        self.language_select.clear()

        for lang in languages:
            self.language_select.addItem(lang)

        if languages:
            self.language_select.setCurrentText(what_language())

        self.language_select.blockSignals(previous_signals)
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
        
        self.status_label.setText(f"{self.lan_pack.get("load_models_loaded_status_1")} {len(models)} {self.lan_pack.get("load_models_loaded_status_2")} {Path(__file__).resolve().parent / "config" / "setupModels.json"}")

    @staticmethod
    def is_hex_color(s: str) -> bool:
        return bool(re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", s))

    def on_start_clicked(self):
        self._start_conversation()

    def on_test_mode_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona una conversazione JSON da testare",
            str(
                Path(__file__).resolve().parent
                / "outputs"
                / "Conversations_JSON"
            ),
            "JSON Files (*.json)",
        )

        if not file_name:
            return

        try:
            replay = ConversationReplay.from_file(file_name)
        except (OSError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Conversazione JSON non valida",
                str(error),
            )
            return

        self._start_conversation(replay=replay)

    def _start_conversation(self, replay=None):
        methods = self.referee.selected()
        model_1 = self.models_combo.currentData() or {}
        model_2 = self.models_combo_2.currentData() or {}

        # In modalità normale servono entrambi i modelli.
        # In test serve A soltanto se il controllore è attivo.
        if replay is None:
            required = [
                ("A", model_1),
                ("B", model_2),
            ]
        else:
            required = (
                [("A", model_1)]
                if any(methods.values())
                else []
            )

        for label, model in required:
            if (
                not isinstance(model, dict)
                or not model.get("deployment")
            ):
                QMessageBox.warning(
                    self,
                    "Modello non configurato",
                    f"Seleziona un deployment valido per {label}.",
                )
                return

        setup_1 = self.sys_edit.toPlainText().strip()
        setup_2 = self.sys_edit_2.toPlainText().strip()
        name = self.file_name.text().strip()
        turns = self.turns.text().strip()

        if not setup_1 or not setup_2:
            QMessageBox.warning(
                self,
                "Prompt mancanti",
                "Inserisci il prompt di sistema di entrambi "
                "gli interlocutori.",
            )
            return

        try:
            turns_int = int(turns) if turns else 3

            if turns_int <= 0:
                raise ValueError(
                    "Il numero di turni deve essere positivo."
                )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Turni non validi",
                str(error),
            )
            return

        name_A = self.name_A.text().strip() or "A"
        name_B = self.name_B.text().strip() or "B"

        config_A = (
            int(
                self.max_tokens_A.text()
                if self.max_tokens_A.text().strip().isdigit()
                else 2500
            ),
            (
                self.color_A.text().strip()
                if self.is_hex_color(self.color_A.text().strip())
                else "#FF0000"
            ),
        )

        config_B = (
            int(
                self.max_tokens_B.text()
                if self.max_tokens_B.text().strip().isdigit()
                else 2500
            ),
            (
                self.color_B.text().strip()
                if self.is_hex_color(self.color_B.text().strip())
                else "#0000FF"
            ),
        )

        A = [{"role": "system", "content": setup_1}]
        B = [{"role": "system", "content": setup_2}]

        for entry in self.file_loaded:
            A.append(entry)
            B.append(entry)

        PDF = [
            {
                "role": f"system prompt for {name_A}:",
                "content": setup_1 + "\n",
            },
            {
                "role": f"config for {name_A}:",
                "content": f"Max tokens: {config_A[0]}",
            },
            {
                "role": f"system prompt for {name_B}:",
                "content": setup_2 + "\n",
            },
            {
                "role": f"config for {name_B}:",
                "content": f"Max tokens: {config_B[0]}",
            },
        ]

        # Il test parte dal JSON scelto, senza incorporare
        # conversazioni precaricate per la modalità normale.
        if replay is None and self.flag_conversation_loaded:
            A.extend(self.A_load)
            B.extend(self.B_load)
            PDF.extend(self.PDF_load)

        talk_args = (
            self.language_select.currentText(),
            name,
            model_1.get("deployment", ""),
            model_2.get("deployment", ""),
            A,
            B,
            PDF,
            turns_int,
            methods,
            name_A,
            name_B,
            config_A,
            config_B,
            list(self.file_loaded),
        )

        self.conv_dialog = ConversationDialog(
            talk_args=talk_args,
            parent=self,
            replay=replay,
        )

        self.conv_dialog.setModal(True)
        self.conv_dialog.show()

    def save_presets(self):
        # Save current settings to a JSON file.
        file_name = self.file_name.text().strip()
        presets = {
            "name_A": self.name_A.text(),
            "name_B": self.name_B.text(),
            "sys_A": self.sys_edit.toPlainText(),
            "sys_B": self.sys_edit_2.toPlainText(),
            "max_tokens_A": self.max_tokens_A.text(),
            "color_A": self.color_A.text(),
            "max_tokens_B": self.max_tokens_B.text(),
            "color_B": self.color_B.text(),
            "turns": self.turns.text(),
            "referee": self.referee.selected(),
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
            self.max_tokens_A.setText(presets.get("max_tokens_A", ""))
            self.color_A.setText(presets.get("color_A", ""))
            self.max_tokens_B.setText(presets.get("max_tokens_B", ""))
            self.color_B.setText(presets.get("color_B", ""))
            self.turns.setText(presets.get("turns", ""))
            self.referee.setSelected(
                presets.get("referee", False)
            )
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
            self.A_load.clear()
            self.B_load.clear()
            self.PDF_load.clear()
            for msg in data:
                if msg["role"] == "A":
                    temp_A = {"role": "assistant", "content": msg["content"]}
                    self.A_load.append(temp_A)
                    temp_B = {"role": "user", "content": msg["content"]}
                    self.B_load.append(temp_B)
                    self.PDF_load.append({"role": f"{self.name_A.text().strip()}:", "content": msg["content"]})
                if msg["role"] == "B":
                    temp_A = {"role": "user", "content": msg["content"]}
                    self.A_load.append(temp_A)
                    temp_B = {"role": "assistant", "content": msg["content"]}
                    self.B_load.append(temp_B)
                    self.PDF_load.append({"role": f"{self.name_B.text().strip()}:", "content": msg["content"]})
            self.flag_conversation_loaded = True
            self.status_label.setText(f"{self.lan_pack.get("conversation_loaded_status")} {file_name}")
        return
    
    def flush_conversation(self):
        self.A_load.clear()
        self.B_load.clear()
        self.PDF_load.clear()

        self.flag_conversation_loaded = False
        self.status_label.setText(
            self.lan_pack.get("conversation_flushed_status")
        )

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open context File",         # Window title
            "",                       # Starting directory ("" = current)
            self.file_filters  # File filter
        )
        if not file_name:
            return  # User cancelled
        self.status_label.setText(f"{self.lan_pack.get("file_loading_status")} {file_name}")
        match Path(file_name).suffix.lower():
            case ".txt" | ".md" | ".json":
                with open(file_name, "r", encoding="utf-8") as f:
                    data = f.read()
                    content_string = f"FILE: {data}"
                self.file_loaded.append({"role": "system", "content": content_string})
            case ".png" | ".jpg" | ".jpeg" | ".gif" | ".bmp" | ".webp":
                base64_str = image_to_base64(file_name)
                url_string = f"data:image/{Path(file_name).suffix.lower()[1:]};base64,{base64_str}"
                self.file_loaded.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": url_string}}]})
            case ".pdf":
                output_dir = Path(__file__).resolve().parent / "temp_pdf_images"
                output_dir.mkdir(parents=True, exist_ok=True)
                doc = fitz.open(file_name)
                urls = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=400)
                    image_path = output_dir / f"{Path(file_name).stem}_page_{page_num + 1}.png"
                    pix.save(image_path)
                    base64_str = image_to_base64(str(image_path))
                    url_string = f"data:image/png;base64,{base64_str}"
                    urls.append({"type": "image_url", "image_url": {"url": url_string}})
                self.file_loaded.append({"role": "user", "content": urls})
            case ".docx":
                doc = Document(file_name)
                data = "\n".join([para.text for para in doc.paragraphs])
                content_string = f"FILE: {data}"
                self.file_loaded.append({"role": "system", "content": content_string})
        return
    
    def flush_file(self):
        self.file_loaded = []
        self.status_label.setText(self.lan_pack.get("flush_file_status"))
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
        self.max_tokens_A.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        self.color_A.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        self.max_tokens_B.setPlaceholderText(self.lan_pack.get("max_tokens_placeholder"))
        self.color_B.setPlaceholderText(self.lan_pack.get("color_placeholder"))
        self.turns.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.referee.setTitle(
            self.lan_pack.get("referee_checkbox_text")
        )
        self.start_btn.setText(self.lan_pack.get("start_button_text"))
        self.reload_btn.setText(self.lan_pack.get("reload_models_button_text"))
        self.save_presets_btn.setText(self.lan_pack.get("save_presets_button_text"))
        self.load_presets_btn.setText(self.lan_pack.get("load_presets_button_text"))
        self.load_conversation_btn.setText(self.lan_pack.get("load_conversation_button_text"))
        self.flush_conversation_btn.setText(self.lan_pack.get("flush_conversation_button_text"))
        self.test_mode_btn.setText(self.lan_pack.get("test_mode_button_text", "Modalità test (JSON)",))
        config_path = Path(__file__).resolve().parent / "config" / "setupModels.json"
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data["lan_pack"] = selected_language
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)