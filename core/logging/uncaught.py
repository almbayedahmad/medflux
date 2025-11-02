from __future__ import annotations

import logging
import sys
import traceback


def install_uncaught_hook() -> None:
    """Install hooks that log uncaught exceptions (main thread and threads)."""

    def _hook(exctype, value, tb):
        logger = logging.getLogger("medflux.uncaught")
        stack = "".join(traceback.format_exception(exctype, value, tb))
        logger.error("Uncaught exception", extra={"exc_type": str(getattr(exctype, "__name__", str(exctype))), "exc": str(value), "stack": stack})
        # Delegate to default behavior
        try:
            sys.__excepthook__(exctype, value, tb)
        except Exception:
            pass

    sys.excepthook = _hook

    # Python 3.8+: also capture exceptions in threads
    try:
        import threading  # noqa: WPS433

        def _thread_hook(args):  # type: ignore[override]
            try:
                _hook(args.exc_type, args.exc_value, args.exc_traceback)
            except Exception:
                pass

        threading.excepthook = _thread_hook  # type: ignore[assignment]
    except Exception:
        pass
