import hashlib
import json
from pathlib import Path


class ConversationReplay:
    def __init__(self, messages, source_path="", source_hash=""):
        if not isinstance(messages, list) or not messages:
            raise ValueError(
                "Il JSON deve contenere una lista non vuota di messaggi."
            )

        validated = []

        for number, message in enumerate(messages, 1):
            if not isinstance(message, dict):
                raise ValueError(
                    f"Messaggio {number}: è richiesto un oggetto JSON."
                )

            if message.get("role") not in ("A", "B"):
                raise ValueError(
                    f"Messaggio {number}: role deve essere A oppure B."
                )

            content = message.get("content")

            if not isinstance(content, str) or not content.strip():
                raise ValueError(
                    f"Messaggio {number}: content deve essere testo non vuoto."
                )

            validated.append((message["role"], content))

        self._messages = tuple(validated)
        self.source_path = str(source_path)
        self.source_hash = source_hash
        self.position = 0

    @classmethod
    def from_file(cls, path):
        source = Path(path).resolve()
        raw = source.read_bytes()

        try:
            messages = json.loads(raw.decode("utf-8-sig"))
        except UnicodeDecodeError as error:
            raise ValueError(
                "Il file JSON deve essere codificato in UTF-8."
            ) from error
        except json.JSONDecodeError as error:
            raise ValueError(
                f"JSON non valido: riga {error.lineno}, "
                f"colonna {error.colno}."
            ) from error

        return cls(
            messages,
            source,
            hashlib.sha256(raw).hexdigest(),
        )

    @property
    def total(self):
        return len(self._messages)

    @property
    def exhausted(self):
        return self.position >= self.total

    def peek(self):
        if self.exhausted:
            raise StopIteration("Conversazione JSON terminata.")

        role, content = self._messages[self.position]
        return {"role": role, "content": content}

    def advance(self):
        if self.exhausted:
            raise StopIteration("Conversazione JSON terminata.")

        self.position += 1

    def metadata(self):
        return {
            "source": self.source_path,
            "sha256": self.source_hash,
            "processed_messages": self.position,
            "total_messages": self.total,
            "next_message": (
                None if self.exhausted else self.position + 1
            ),
        }