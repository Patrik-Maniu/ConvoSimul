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
    QLabel,
)
from datetime import datetime
from controllore import referee, configure_referee
from referee_menu import RefereeMenu
from PyQt6.QtGui import QColor
from PDFer import export_conversation_to_pdf

def clear_temp_files():
    temp_dir = Path(__file__).resolve().parent / "temp_pdf_images"
    if temp_dir.exists() and temp_dir.is_dir():
        for temp_file in temp_dir.iterdir():
            try:
                temp_file.unlink()
            except Exception as e:
                print(f"Error deleting temp file {temp_file}: {e}")

def import_lan_pack(language):
    language_path = Path(__file__).resolve().parent / "language_packs" / language
    if not language_path.exists():
        first_lan = os.listdir(Path(__file__).resolve().parent / "language_packs")[0]
        language_path = Path(__file__).resolve().parent / "language_packs" / first_lan
    with language_path.open("r", encoding="utf-8") as f:
        return json.load(f)

class ConversationDialog(QDialog):
    def __init__(self, talk_args: tuple, parent=None, replay=None):
        super().__init__(parent)
        (
            self.language,
            self.name,
            self.deploy_A,
            self.deploy_B,
            self.A,
            self.B,
            self.PDF,
            self.turns,
            self.passed_referee,
            self.name_A,
            self.name_B,
            self.config_A,
            self.config_B,
            self.referee_files,
        ) = talk_args
        self.lan_pack = import_lan_pack(self.language).get("conversation_window.py")
        self.setWindowTitle(self.lan_pack.get("window_title"))
        self.replay = replay
        self.replay_finished = False

        if self.replay is not None:
            self.setWindowTitle("Conversazione - Modalità test")
        self.resize(700, 500)
        self.max_tokens_A, self.color_A = self.config_A
        self.max_tokens_B, self.color_B = self.config_B
        self.turn = True
        self.save_N_pdf = 1
        self.save_N_json = 1
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.referee = RefereeMenu("Controllore", self)
        self.referee.setSelected(self.passed_referee)
        self.referee.selectionChanged.connect(
            self._on_referee_selection
        )
        self.turns_input = QLineEdit()
        self.turns_input.setPlaceholderText(self.lan_pack.get("turns_placeholder"))
        self.next_btn = QPushButton(self.lan_pack.get("next_button_text"))
        self.stop_btn = QPushButton(self.lan_pack.get("stop_button_text"))
        self.save_btn = QPushButton(self.lan_pack.get("save_to_PDF_button_text"))
        self.save_json = QPushButton(self.lan_pack.get("save_to_JSON_button_text"))
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)

        self.progress_label = QLabel(self)
        self.progress_label.setVisible(self.replay is not None)
        self._update_replay_progress()

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.referee)
        btns.addWidget(self.turns_input)
        btns.addWidget(self.next_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.save_btn)
        btns.addWidget(self.save_json)

        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.output)
        layout.addLayout(btns)
        layout.addWidget(self.status_label)

        self.next_btn.clicked.connect(self.on_next_clicked)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.save_json.clicked.connect(self.json_save)

        # Setup
        for msg in self.A:
            if msg["role"] == "assistant":
                self.output.setTextColor(QColor(self.color_A))
                self.output.append(f"{self.name_A}: " + "\n" + msg["content"] + "\n")
            if msg["role"] == "user":
                if not isinstance(msg["content"], str):
                    continue
                self.output.setTextColor(QColor(self.color_B))
                self.output.append(f"{self.name_B}: " + "\n" + msg["content"] + "\n")
        initial_history = [
            {
                "speaker": (
                    "A" if msg["role"] == "assistant" else "B"
                ),
                "content": msg["content"],
            }
            for msg in self.A[1 + len(self.referee_files):]
            if msg["role"] in {"assistant", "user"}
        ]

        # Gli allegati non devono alterare il calcolo
        # del prossimo interlocutore.
        self.turn = (
            not initial_history
            or initial_history[-1]["speaker"] != "A"
        )
        if self.replay is not None and not self.replay.exhausted:
            self.turn = self.replay.peek()["role"] == "A"
        self.referee_state = {}

        preparation = referee(
            state=self.referee_state,
            methods=self.passed_referee,
            prompts={
                "A": self.A[0]["content"],
                "B": self.B[0]["content"],
            },
            attachments=self.referee_files,
            history=initial_history,
            deployment=self.deploy_A,
        )

        if preparation["stop"]:
            self.next_btn.setEnabled(False)
            self._suspend_referee(preparation)
            return
        self.turns_input.setText(str(self.turns))
        self.on_next_clicked()

    def _on_referee_selection(self):
        if (
            getattr(self, "_busy", False)
            or getattr(self, "_closing", False)
        ):
            return

        self.next_btn.setEnabled(not self.replay_finished)
        self.status_label.setText(
            "La nuova selezione sarà applicata premendo Next."
        )

    def on_next_clicked(self):
        if self.replay_finished:
            return

        preparation = configure_referee(
            self.referee_state,
            self.referee.selected(),
        )

        if preparation["stop"]:
            self._suspend_referee(preparation)
            return
        self.turns = int(self.turns_input.text().strip()) if self.turns_input.text().strip().isdigit() and int(self.turns_input.text().strip()) > 0 else 1
        self.turns_input.clear()
        # Scroll to beginning of next output
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)
        while self.turns > 0:
            if self.replay is not None:
                if self.replay.exhausted:
                    self._finish_replay()
                    return

                recorded = self.replay.peek()
                self.turn = recorded["role"] == "A"
                result = recorded["content"]

            else:
                try:
                    from conversation import talk

                    if self.turn:
                        result = talk(
                            msgs=self.A,
                            dep=self.deploy_A,
                            max_tokens=self.max_tokens_A,
                        )
                    else:
                        result = talk(
                            msgs=self.B,
                            dep=self.deploy_B,
                            max_tokens=self.max_tokens_B,
                        )

                except Exception as error:
                    self.output.append(
                        f"\n{self.lan_pack.get('import_talk_function_output')}: "
                        f"{error}"
                    )
                    self.next_btn.setEnabled(False)
                    return

            # Append result to output
            name = self.name_A if self.turn else self.name_B
            color = self.color_A if self.turn else self.color_B

            self.output.setTextColor(QColor(color))
            self.output.insertPlainText(
                f"\n{name}:\n{result}\n"
            )
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
            decision = referee(
                state=self.referee_state,
                # Il codice precedente ha già invertito self.turn.
                speaker="B" if self.turn else "A",
                message=result,
            )

            if decision["stop"]:
                self.PDF[-1]["role"] += " [BLOCCATO]"

                if self.replay is not None:
                    # La conversazione registrata contiene comunque
                    # questo messaggio: conserviamolo come contesto,
                    # indicando che il controllore lo ha bloccato.
                    self.referee_state["history"].append({
                        "turn": decision["turn"],
                        "speaker": "B" if self.turn else "A",
                        "content": result,
                        "blocked": True,
                    })

                    self.replay.advance()
                    self._update_replay_progress()

                    self.replay_finished = self.replay.exhausted

                    if not self.replay_finished:
                        self.turn = (
                            self.replay.peek()["role"] == "A"
                        )

                else:
                    # In modalità normale il turno bloccato
                    # viene rimosso e potrà essere rigenerato.
                    self.A.pop()
                    self.B.pop()
                    self.turn = not self.turn

                self._suspend_referee(decision)
                break
            if self.replay is not None:
                self.replay.advance()
                self._update_replay_progress()

                if self.replay.exhausted:
                    self._finish_replay()
                    return

                self.turn = self.replay.peek()["role"] == "A"

            self.turns -= 1

    def _update_replay_progress(self):
        if self.replay is not None:
            self.progress_label.setText(
                f"Test: {self.replay.position}/{self.replay.total} "
                "messaggi elaborati"
            )

    def _finish_replay(self):
        if self.replay_finished:
            return

        self.replay_finished = True
        self.turns = 0
        self.next_btn.setEnabled(False)

        message = self.lan_pack.get(
            "test_mode_complete",
            "Test completato: fine del file JSON.",
        )
        decision = {
            "stop": False,
            "esito": "test_completato",
            "motivo": message,
        }

        try:
            destination = self._save_referee_snapshot(decision)
            message += f"\nReport: {destination}"
        except Exception as error:
            message += f"\nSALVATAGGIO FALLITO: {error}"

        self.status_label.setText(message)
        self.output.append("\n[Test] " + message)

    def _suspend_referee(self, decision):
        self.turns = 0
        message = f"{decision['esito']}: {decision['motivo']}"

        ready = bool(self.referee_state.get("ready"))

        self.next_btn.setEnabled(
            not self.replay_finished
        )

        if self.replay is not None:
            if not ready:
                message += (
                    "\nPreparazione fallita: correggi l'errore "
                    "e riavvia il test."
                )
            elif self.replay_finished:
                message += (
                    "\nUltimo messaggio del JSON: "
                    "test terminato con un blocco."
                )
            else:
                message += (
                    "\nTest sospeso: premi Next per esaminare "
                    "il messaggio successivo."
                )

        try:
            destination = self._save_referee_snapshot(decision)
            message += f"\nSalvataggio: {destination}"
        except Exception as error:
            message += f"\nSALVATAGGIO FALLITO: {error}"

        self.output.append("\n[Controllore] " + message)
        self.status_label.setText(message)

    def _save_referee_snapshot(self, decision):
        snapshot = {
            "format": "ConvoSimul-referee-v1",
            "name": self.name,
            "mode": "test" if self.replay is not None else "live",
            "replay": (
                self.replay.metadata()
                if self.replay is not None
                else None
            ),
            "participants": {
                "A": self.name_A,
                "B": self.name_B,
            },
            "deployments": {
                "A": self.deploy_A,
                "B": self.deploy_B,
            },
            "config_A": self.config_A,
            "config_B": self.config_B,
            "next_speaker": (
                None
                if self.replay is not None and self.replay.exhausted
                else ("A" if self.turn else "B")
            ),
            "decision": decision,
            "controller": self.referee_state,
            "transcript": self.PDF,
        }

        folder = (
            Path(__file__).resolve().parent
            / "outputs"
            / "Referee"
        )
        folder.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        destination = folder / f"referee_{stamp}.json"
        temporary = destination.with_suffix(".tmp")

        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(
                snapshot,
                stream,
                ensure_ascii=False,
                indent=2,
            )

        temporary.replace(destination)
        return destination

    def on_stop_clicked(self):
        # Close the entire program
        export_conversation_to_pdf(messages=self.PDF, name=self.name)
        clear_temp_files()
        QApplication.instance().quit()
        self.close()
    
    def on_save_clicked(self):
        export_conversation_to_pdf(messages=self.PDF, name=self.name + str(self.save_N_pdf))
        self.save_N_pdf += 1

    def json_save(self):
        file_name = self.name + str(self.save_N_json)
        msgs = [
            {
                "role": msg["speaker"],
                "content": msg["content"],
            }
            for msg in self.referee_state["history"]
        ]
        # Ensure the subfolder 'conversations' exists
        os.makedirs(Path(__file__).resolve().parent / "outputs" / "Conversations_JSON", exist_ok=True)
        # Construct the full path (add .json extension if missing)
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        file_path = Path(__file__).resolve().parent / "outputs" / "Conversations_JSON" / file_name
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(msgs, f, ensure_ascii=False, indent=4)
            self.save_N_json += 1
            self.status_label.setText(f"{self.lan_pack.get('JSON_save_success_status')} {file_path}")
        except Exception as e:
            print(f"Error saving conversation: {e}")