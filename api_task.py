from threading import Event
from PyQt6.QtCore import QThread

from request_control import pause_event, RequestsPaused


class ApiTask(QThread):
    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function
        self.result = None
        self.error = None
        self.paused = False
        self.pause_requested = Event()

    def run(self):
        token = pause_event.set(self.pause_requested)

        try:
            self.result = self.function()

        except RequestsPaused:
            self.paused = True

        except Exception as error:
            self.error = f"{type(error).__name__}: {error}"

        finally:
            pause_event.reset(token)