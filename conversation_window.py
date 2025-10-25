from PyQt6.QtWidgets import (
    QDialog,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QApplication,
)
from PDFer import export_conversation_to_pdf

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
        QApplication.instance().quit()
        self.close()