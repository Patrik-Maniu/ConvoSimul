import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QApplication,
    QLineEdit,
    QCheckBox,
)
from PyQt6.QtGui import QColor
from PDFer import export_conversation_to_pdf

def import_lan_pack(language):
    language_path = Path(__file__).resolve().parent / "language_packs" / language
    if not language_path.exists():
        first_lan = os.listdir(Path(__file__).resolve().parent / "language_packs")[0]
        language_path = Path(__file__).resolve().parent / "language_packs" / first_lan
    with language_path.open("r", encoding="utf-8") as f:
        return json.load(f)

class ConversationDialog(QDialog):
    def __init__(self, talk_args: tuple, parent=None):
        super().__init__(parent)
        self.language, self.name, self.deploy_A, self.deploy_B, self.A, self.B, self.PDF, self.turns, self.passed_referee, self.name_A, self.name_B, self.config_A, self.config_B = talk_args
        self.lan_pack = import_lan_pack(self.language).get("conversation_window.py")
        self.setWindowTitle(self.lan_pack.get("window_title"))
        self.resize(700, 500)
        self.seed_A, self.max_tokens_A, self.color_A = self.config_A
        self.seed_B, self.max_tokens_B, self.color_B = self.config_B
        self.turn = True
        self.save_N_pdf = 1
        self.save_N_json = 1
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.referee = QCheckBox(self.lan_pack.get("referee_checkbox_text"))
        self.turns_input = QLineEdit()
        self.turns_input.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.next_btn = QPushButton(self.lan_pack.get("next_button_text"))
        self.stop_btn = QPushButton(self.lan_pack.get("stop_button_text"))
        self.save_btn = QPushButton(self.lan_pack.get("save_to_PDF_button_text"))
        self.save_json = QPushButton(self.lan_pack.get("save_to_JSON_button_text"))
        self.status_label = QMessageBox(self)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.referee)
        btns.addWidget(self.turns_input)
        btns.addWidget(self.next_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.save_btn)
        btns.addWidget(self.save_json)

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addLayout(btns)
        layout.addWidget(self.status_label)

        self.next_btn.clicked.connect(self.on_next_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.save_json.clicked.connect(self.json_save)
        self.referee.setChecked(self.passed_referee)

        # Setup
        for msg in self.A:
            if msg["role"] == "assistant":
                self.output.append(f"{self.name_A}: " + "\n" + msg["content"] + "\n")
            if msg["role"] == "user":
                self.output.append(f"{self.name_B}: " + "\n" + msg["content"] + "\n")
        self.context_check = "Given the following conversation and system prompts reply with just yes or no, if the last message is still keeping the same context (some messages might be missing, just consider if the new message is a possible continuation of this context), context:\n"
        for msg in self.PDF:
            self.context_check += msg["role"] + ": " + msg["content"] + "\n"
        self.context_check += "New message: \n"

        # Check turn
        if len(self.A) % 2 == 1:
            self.turn = True
        else:
            self.turn = False
        self.turns_input.setText(str(self.turns))
        self.on_next_clicked()

    def on_next_clicked(self):
        self.turns = int(self.turns_input.text().strip()) if self.turns_input.text().strip().isdigit() and int(self.turns_input.text().strip()) > 0 else 1
        self.turns_input.clear()
        # Scroll to beginning of next output
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        while self.turns > 0:
            # Lazy import so a bad conversation.py doesn't kill the window before it shows.
            try:
                from conversation import talk
            except Exception as e:
                QMessageBox.critical(self, self.lan_pack.get("import_talk_function_error_1"), f"{self.lan_pack.get('import_talk_function_error_2')}{e}")
                return

            try:
                if self.turn:
                    result = talk(msgs=self.A, dep=self.deploy_A, seed=self.seed_A, max_tokens=self.max_tokens_A)
                else:
                    result = talk(msgs=self.B, dep=self.deploy_B, seed=self.seed_B, max_tokens=self.max_tokens_B)
            except Exception as e:
                # Show error in the text area and disable Next
                self.output.append(f"\n{self.lan_pack.get('import_talk_function_output')}: {e}")
                self.next_btn.setEnabled(False)
                return

            # Append result to output
            if self.output.toPlainText():
                if self.turn:
                    self.output.setTextColor(QColor(self.color_A))
                    self.output.append("\n" + f"{self.name_A}: " + "\n")
                else:
                    self.output.setTextColor(QColor(self.color_B))
                    self.output.append("\n" + f"{self.name_B}: " + "\n")
                self.output.append("\n" + result)
            else:
                if self.turn:
                    self.output.setTextColor(QColor(self.color_A))
                    self.output.setPlainText(f"{self.name_A}: " + "\n")
                else:
                    self.output.setTextColor(QColor(self.color_B))
                    self.output.setPlainText(f"{self.name_B}: " + "\n")
                self.output.append(result)

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
            if self.referee.isChecked():
                # Context checker
                print("entered here")
                context_temp = self.context_check + result + "\n reply with just yes or no."
                context_msg = [{"role": "system", "content": "Your'e a context checker, your response will be used in a program so strictly reply just yes or no"}, {"role": "user", "content": context_temp}]
                try:
                    from conversation import talk
                except Exception as e:
                    QMessageBox.critical(self, self.lan_pack.get("import_talk_function_error_1"), f"{self.lan_pack.get('import_talk_function_error_2')}{e}")
                    return
                try:
                    stop = talk(msgs=context_msg, dep=self.deploy_A, seed=None, max_tokens=100)
                    stop = stop.lower().strip()
                    print(stop)
                    if("no" in stop):
                        self.turns = 0
                        self.status_label.setText(self.lan_pack.get("out_of_context"))
                except Exception as e:
                    # Show error in the text area and disable Next
                    self.output.append(f"\n{self.lan_pack.get('import_talk_function_output')}: {e}")
                    self.next_btn.setEnabled(False)
                    return
            self.turns -= 1

    def on_stop_clicked(self):
        # Close the entire program
        export_conversation_to_pdf(messages=self.PDF, name=self.name)
        QApplication.instance().quit()
        self.close()
    
    def on_save_clicked(self):
        export_conversation_to_pdf(messages=self.PDF, name=self.name + str(self.save_N_pdf))
        self.save_N_pdf += 1

    def json_save(self):
        file_name = self.name + str(self.save_N_json)
        temp_A = self.A.copy()
        temp_B = self.B.copy()
        temp_A = [msg for msg in temp_A if msg["role"] != "system"]
        temp_B = [msg for msg in temp_B if msg["role"] != "system"]
        messages = {
            "A": temp_A,
            "B": temp_B,
        }
        # Ensure the subfolder 'conversations' exists
        os.makedirs("conversations", exist_ok=True)
        # Construct the full path (add .json extension if missing)
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        file_path = os.path.join("conversations", file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=4)
            self.save_N_json += 1
            self.status_label.setText(f"{self.lan_pack.get('JSON_save_success_status')} {file_path}")
        except Exception as e:
            print(f"Error saving conversation: {e}")