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
import copy
from functools import partial
from PyQt6.QtCore import QTimer
from api_task import ApiTask
import conversation


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
        self.stop_btn.setText("Salva e chiudi")

        self.pause_btn = QPushButton("Interrompi richieste")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.on_pause_clicked)
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
        btns.addWidget(self.pause_btn)
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

        # Inizializzazione locale: methods={} evita chiamate API.
        # I controlli selezionati saranno applicati dal worker.
        referee(
            state=self.referee_state,
            methods={},
            prompts={
                "A": self.A[0]["content"],
                "B": self.B[0]["content"],
            },
            attachments=self.referee_files,
            history=initial_history,
            deployment=self.deploy_A,
        )

        self._task = None
        self._busy = False
        self._closing = False
        self._quit_after_close = False
        self._candidate = None
        self._pause_requested = False
        self._batch_total = self.turns
        self._batch_done = 0

        self.turns_input.setText(str(self.turns))

        # Lascia prima che la finestra venga mostrata.
        QTimer.singleShot(0, self.on_next_clicked)

    def _on_referee_selection(self):
        if (
            getattr(self, "_busy", False)
            or getattr(self, "_closing", False)
        ):
            return

        self.next_btn.setEnabled(not self.replay_finished)
        self._status(
            "La nuova selezione sarà applicata premendo Next."
        )

    def _set_busy(self, busy):
        self._busy = busy
        self.pause_btn.setEnabled(
            busy
            and not self._pause_requested
            and not self._closing
        )

        if busy:
            self.referee.menu().close()

        for widget in (
            self.referee,
            self.turns_input,
            self.save_btn,
            self.save_json,
        ):
            widget.setEnabled(not busy and not self._closing)

        self.next_btn.setEnabled(
            not busy
            and not self._closing
            and not self.replay_finished
        )

    def _run_task(self, function, callback):
        self._task_callback = callback
        self._task = ApiTask(function, self)
        self._task.finished.connect(self._task_finished)
        self._task.start()

    def _task_finished(self):
        task = self._task
        result, error = task.result, task.error
        paused = task.paused
        callback = self._task_callback

        self._task = None
        task.deleteLater()

        if self._closing:
            if self._candidate is not None:
                self.PDF[-1]["role"] += " [VALUTAZIONE INTERROTTA]"

            self._set_busy(False)
            self.close()
            return

        if paused:
            self._pause_batch()
            return

        if error is not None:
            if self._candidate is not None:
                self.PDF[-1]["role"] += " [NON VALUTATO]"
                self._candidate = None

            self.turns = 0
            self._set_busy(False)
            self._status(error)
            self.output.append("\n[Errore] " + error)
            return

        callback(result)

    def on_next_clicked(self):
        if self._busy or self._closing or self.replay_finished:
            return

        value = self.turns_input.text().strip()

        self.turns = (
            int(value)
            if value.isdigit() and int(value) > 0
            else 1
        )

        self.turns_input.clear()

        self._batch_total = self.turns
        self._batch_done = 0
        self._pause_requested = False

        self._set_busy(True)
        self._status("Preparazione del controllore…")

        self._pending_state = copy.deepcopy(self.referee_state)

        self._run_task(
            partial(
                configure_referee,
                self._pending_state,
                self.referee.selected(),
            ),
            self._prepared,
        )

    def _prepared(self, decision):
        self.referee_state = self._pending_state

        if decision["stop"]:
            self._set_busy(False)
            self._suspend_referee(decision)

        elif self._pause_requested:
            self._pause_batch()

        elif self._candidate is not None:
            # La risposta è già arrivata durante la pausa:
            # deve essere controllata, non rigenerata.
            self._check_candidate()

        else:
            self._start_turn()

    def _start_turn(self):
        if self._closing or not self._busy:
            return

        if self._pause_requested:
            self._pause_batch()
            return

        if self.replay is not None:
            if self.replay.exhausted:
                self._set_busy(False)
                self._finish_replay()
                return

            recorded = self.replay.peek()
            self.turn = recorded["role"] == "A"
            self._generated(recorded["content"])

        else:
            self._status(
                "Generazione del messaggio…",
                in_progress=True,
            )

            self._run_task(
                partial(
                    conversation.talk,
                    msgs=copy.deepcopy(
                        self.A if self.turn else self.B
                    ),
                    dep=(
                        self.deploy_A if self.turn
                        else self.deploy_B
                    ),
                    max_tokens=(
                        self.max_tokens_A if self.turn
                        else self.max_tokens_B
                    ),
                ),
                self._generated,
            )

    def _generated(self, text):
        speaker = "A" if self.turn else "B"
        name = self.name_A if self.turn else self.name_B

        self._candidate = (speaker, text)

        # Mostra il messaggio PRIMA di avviare il giudizio.
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output.setTextCursor(cursor)

        self.output.setTextColor(
            QColor(self.color_A if self.turn else self.color_B)
        )
        self.output.insertPlainText(f"\n{name}:\n{text}\n")

        self.PDF.append({
            "role": f"{name}:",
            "content": text,
        })
        self._check_candidate()

    def _checked(self, decision):
        self.referee_state = self._pending_state
        speaker, text = self._candidate
        self._candidate = None

        self._batch_done += 1

        name = self.name_A if speaker == "A" else self.name_B
        self.PDF[-1]["role"] = f"{name}:"

        blocked = decision["stop"]

        if not blocked or self.replay is not None:
            self.A.append({
                "role": "assistant" if speaker == "A" else "user",
                "content": text,
            })
            self.B.append({
                "role": "assistant" if speaker == "B" else "user",
                "content": text,
            })

        if blocked:
            self.PDF[-1]["role"] += " [BLOCCATO]"

            if self.replay is not None:
                self.referee_state["history"].append({
                    "turn": decision["turn"],
                    "speaker": speaker,
                    "content": text,
                    "blocked": True,
                })

        if self.replay is not None:
            self.replay.advance()
            self._update_replay_progress()

            if not self.replay.exhausted:
                self.turn = self.replay.peek()["role"] == "A"
            elif blocked:
                self.replay_finished = True

        elif not blocked:
            self.turn = not self.turn

        self.turns -= 1

        if blocked:
            # Ferma questo gruppo, senza disattivare i controlli.
            self._set_busy(False)
            self._suspend_referee(decision)

        elif self.replay is not None and self.replay.exhausted:
            self._set_busy(False)
            self._finish_replay()

        elif self._pause_requested:
            # L'ultimo giudizio ricevuto è stato applicato.
            # Non parte un altro turno.
            self._pause_batch()

        elif self.turns > 0:
            self._start_turn()

        else:
            self._set_busy(False)
            self._status(
                "Turni completati. "
                "Puoi cambiare i controlli e premere Next."
            )
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

        self._status(message)
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
        self._status(message)

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
        self._quit_after_close = True
        self.close()

    def reject(self):
        # Gestisce anche la chiusura tramite Esc.
        self.close()

    def closeEvent(self, event):
        self._closing = True
        self.turns = 0

        if self._task is not None:
            event.ignore()
            self._status(
                "Chiusura in attesa dell’operazione API in corso…"
            )
            return

        if self._quit_after_close:
            try:
                export_conversation_to_pdf(
                    messages=self.PDF,
                    name=self.name,
                )
                clear_temp_files()

            except Exception as error:
                QMessageBox.warning(
                    self,
                    "Errore nel salvataggio",
                    str(error),
                )

            QApplication.instance().quit()

        event.accept()

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
            self._status(f"{self.lan_pack.get('JSON_save_success_status')} {file_path}")
        except Exception as e:
            print(f"Error saving conversation: {e}")
    def _status(self, message, in_progress=False):
        if in_progress:
            number = min(
                self._batch_done + 1,
                self._batch_total,
            )
            prefix = f"Turno {number}/{self._batch_total}"
        else:
            prefix = (
                f"Turni valutati: "
                f"{self._batch_done}/{self._batch_total}"
            )

        self.status_label.setText(f"{prefix}\n{message}")

    def on_pause_clicked(self):
        if not self._busy or self._closing:
            return

        self._pause_requested = True
        self.pause_btn.setEnabled(False)

        self._status(
            "Interruzione richiesta: "
            "attendo la risposta già in corso."
        )

        if self._task is not None:
            self._task.pause_requested.set()
        else:
            self._pause_batch()

    def _pause_batch(self):
        self.turns = 0
        self._set_busy(False)

        if self._candidate is not None:
            speaker, _ = self._candidate
            name = self.name_A if speaker == "A" else self.name_B

            self.PDF[-1]["role"] = (
                f"{name}: [IN ATTESA DI CONTROLLO]"
            )

            self._status(
                "In pausa. Next controllerà il messaggio "
                "ricevuto prima di proseguire."
            )
        else:
            self._status(
                "In pausa. Premi Next per riprendere "
                "con i controlli selezionati."
            )

    def _check_candidate(self):
        if self._pause_requested:
            self._pause_batch()
            return

        speaker, text = self._candidate

        self._status(
            "Controllo del messaggio…",
            in_progress=True,
        )

        self._pending_state = copy.deepcopy(self.referee_state)

        self._run_task(
            partial(
                referee,
                state=self._pending_state,
                speaker=speaker,
                message=text,
            ),
            self._checked,
        )