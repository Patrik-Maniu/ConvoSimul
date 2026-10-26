from contextvars import ContextVar


pause_event = ContextVar("pause_event", default=None)


class RequestsPaused(Exception):
    pass


def ensure_requests_allowed():
    event = pause_event.get()

    if event is not None and event.is_set():
        raise RequestsPaused()