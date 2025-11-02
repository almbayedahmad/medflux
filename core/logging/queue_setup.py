from __future__ import annotations

import atexit
import logging
import logging.handlers
import queue
from typing import Iterable, List

_q: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=10000)
_listener: logging.handlers.QueueListener | None = None


def attach_queue_to_root() -> None:
    """Replace root handlers with a QueueHandler and start a QueueListener.

    Existing root handlers are preserved behind the listener. Ensures a clean
    shutdown via atexit to flush remaining records.
    """
    global _listener
    root = logging.getLogger()
    handlers = root.handlers[:]
    root.handlers.clear()
    qh = logging.handlers.QueueHandler(_q)
    root.addHandler(qh)
    _listener = logging.handlers.QueueListener(_q, *handlers, respect_handler_level=True)
    _listener.start()
    # Ensure the listener stops on interpreter shutdown
    atexit.register(stop_queue)


def stop_queue() -> None:
    global _listener
    try:
        if _listener is not None:
            _listener.stop()
    except Exception:
        pass
    _listener = None


def effective_handlers() -> List[logging.Handler]:
    """Return the active handlers receiving log records.

    If a QueueListener is installed, this returns the handlers wired behind it;
    otherwise returns the current root handlers.
    """
    if _listener is not None:
        try:
            # QueueListener stores the target handlers in .handlers
            return list(getattr(_listener, "handlers", ()))
        except Exception:
            return []
    return logging.getLogger().handlers[:]
