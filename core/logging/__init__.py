"""Cross-cutting logging utilities for the core.

Provides:
- `configure_logging()` to apply central config from core/policy.
- `get_logger()` to obtain a configured logger.
- `with_context()` and `log_context()` to attach standard fields.
"""

from __future__ import annotations

import logging
import logging.handlers
import logging.config
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, Optional

from core.policy_utils import load_policy_with_overrides, repo_root

_DEFAULT_LEVEL = os.environ.get("MEDFLUX_LOG_LEVEL", "INFO").upper()
_DEFAULT_FORMAT = os.environ.get(
    "MEDFLUX_LOG_FORMAT",
    "%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def _ensure_configured(root_level: Optional[str] = None, fmt: Optional[str] = None) -> None:
    """Ensure root logging is configured once.

    This avoids duplicate handlers if `get_logger` is called many times.
    """

    root = logging.getLogger()
    if root.handlers:
        return
    # Resolve level/format at call time to respect current env
    lvl = (root_level or os.environ.get("MEDFLUX_LOG_LEVEL", "INFO")).upper()
    fmt_val = fmt or os.environ.get(
        "MEDFLUX_LOG_FORMAT",
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt_val))
    root.addHandler(handler)
    try:
        root.setLevel(getattr(logging, lvl))
    except Exception:
        root.setLevel(logging.INFO)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger.

    - Respects env vars `MEDFLUX_LOG_LEVEL` and `MEDFLUX_LOG_FORMAT`.
    - Safe to call from anywhere.
    """

    _ensure_configured()
    return logging.getLogger(name or "medflux")


def configure_logging(force: bool = False) -> None:
    """Apply central logging config from policy if available.

    Falls back to a simple stream handler if config cannot be loaded.
    """
    root = logging.getLogger()
    if root.handlers and not force:
        return
    try:
        profile = (os.environ.get("MEDFLUX_LOG_PROFILE", "dev").strip() or "dev").lower()
        # Prefer profile-specific config; fallback to base config
        policy = None
        for fname in (f"observability/logging/logging_config.{profile}.yaml", "observability/logging/logging_config.yaml"):
            try:
                policy = load_policy_with_overrides(fname)
                if policy:
                    break
            except Exception:
                continue
        if not policy:
            raise RuntimeError("logging policy not found")
        cfg: Dict[str, object] = policy.get("logging", {}) if isinstance(policy, dict) else {}
        if isinstance(cfg, dict) and cfg:
            # Ensure a root logger exists
            cfg.setdefault("version", 1)
            if "root" not in cfg:
                # Default to console handler if defined; else let dictConfig decide
                handlers = ["console"] if isinstance(cfg.get("handlers"), dict) and "console" in cfg["handlers"] else []
                cfg["root"] = {"level": os.environ.get("MEDFLUX_LOG_LEVEL", "INFO"), "handlers": handlers}
            # Optional JSON toggle via env
            try:
                fmt_override = os.environ.get("MEDFLUX_LOG_FORMAT", "").strip().lower()
                json_toggle = fmt_override == "json" or os.environ.get("MEDFLUX_LOG_JSON", "").strip().lower() in {"1", "true", "yes"}
                if isinstance(cfg.get("handlers"), dict):
                    console = cfg["handlers"].get("console")  # type: ignore[index]
                    if isinstance(console, dict):
                        if json_toggle:
                            console["formatter"] = "json"
                        # Force stderr when requested
                        if os.environ.get("MEDFLUX_LOG_TO_STDERR", "").strip().lower() in {"1", "true", "yes"}:
                            console["stream"] = "ext://sys.stderr"
                    # File handler toggles
                    file_off = os.environ.get("MEDFLUX_LOG_FILE", "").strip().lower() in {"0", "false", "no"}
                    daily_on = os.environ.get("MEDFLUX_LOG_DAILY", "").strip().lower() in {"1", "true", "yes"}
                    if file_off:
                        # Remove json_file handler and from root handlers
                        if "json_file" in cfg["handlers"]:
                            cfg["handlers"].pop("json_file", None)
                        try:
                            if isinstance(cfg.get("root"), dict) and isinstance(cfg["root"].get("handlers"), list):
                                cfg["root"]["handlers"] = [h for h in cfg["root"]["handlers"] if h != "json_file"]
                        except Exception:
                            pass
                    elif daily_on and "json_file_daily" in cfg["handlers"]:
                        try:
                            if isinstance(cfg.get("root"), dict) and isinstance(cfg["root"].get("handlers"), list):
                                handlers = cfg["root"]["handlers"]
                                cfg["root"]["handlers"] = ["json_file_daily" if h == "json_file" else h for h in handlers]
                        except Exception:
                            pass
                    # Anchor file handlers to repo root (dev default) and ensure directory exists
                    try:
                        base_dir = _log_root_dir()
                        if isinstance(cfg.get("handlers"), dict):
                            for hn in ("json_file", "json_file_daily"):
                                h = cfg["handlers"].get(hn)  # type: ignore[index]
                                if isinstance(h, dict):
                                    filename_val = h.get("filename")
                                    if isinstance(filename_val, str) and filename_val:
                                        fname = Path(filename_val)
                                        target = fname if fname.is_absolute() else base_dir / fname.name
                                        try:
                                            target.parent.mkdir(parents=True, exist_ok=True)
                                        except Exception:
                                            pass
                                        h["filename"] = str(target)
                    except Exception:
                        pass
            except Exception:
                pass
            logging.config.dictConfig(cfg)  # type: ignore[arg-type]
            # Capture stdlib warnings into logging
            try:
                logging.captureWarnings(True)
            except Exception:
                pass
            # In prod profile, enable queue handler by default (can be disabled via env)
            try:
                if os.environ.get("MEDFLUX_LOG_PROFILE", "dev").strip().lower() == "prod" and os.environ.get("MEDFLUX_LOG_ENABLE_QUEUE", "1") == "1":
                    from .queue_setup import attach_queue_to_root

                    attach_queue_to_root()
            except Exception:
                pass
            return
    except Exception:
        # Ignore and fall back to basic stream handler
        pass
    _ensure_configured()


class _ContextAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        merged = {**self.extra, **extra}
        kwargs["extra"] = merged
        return msg, kwargs


def with_context(logger: Optional[logging.Logger] = None, **fields) -> logging.Logger:
    base = logger or get_logger()
    return _ContextAdapter(base, fields)


@contextmanager
def log_context(logger: Optional[logging.Logger] = None, **fields) -> Iterator[logging.Logger]:
    yield with_context(logger, **fields)


def emit_json_event(**payload) -> None:
    """Emit an INFO-level event with structured extras.

    When the JSON formatter is enabled in policy (formatters.json), the output will be JSON lines.
    Otherwise the extra fields still appear if the formatter includes them.
    """
    get_logger().info("event", extra=payload)


def log_code(code: str, level: str = "INFO", **extra) -> None:
    """Emit a standardized message with a code identifier.

    - level: one of INFO/WARNING/ERROR/DEBUG
    - extra: additional context fields
    """
    level = (level or "INFO").upper()
    logger = get_logger()
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(f"code={code}", extra={"code": code, **extra})


def _log_root_dir() -> Path:
    env_root = os.environ.get("MEDFLUX_LOG_ROOT")
    if env_root:
        return Path(env_root)
    try:
        return repo_root() / "logs"
    except Exception:
        # Fallback to cwd-relative if repo root cannot be resolved
        return Path("logs")


def configure_log_destination(run_id: str, phase: str, *, flow: str | None = None, root: str | Path | None = None) -> Path:
    """Point the JSON file handler(s) to a structured path.

    Path schema:
      - If flow is provided: {root}/{flow}/{YYYY-MM-DD}/{run_id}/{phase}.jsonl
      - Else:                {root}/{YYYY-MM-DD}/{run_id}/{phase}.jsonl

    Supports both RotatingFileHandler and TimedRotatingFileHandler. If a
    queue listener is installed, handlers wired behind it are updated.
    Returns the resolved file path.
    """
    base = Path(root) if root is not None else _log_root_dir()
    day = datetime.utcnow().strftime("%Y-%m-%d")
    sub = [day, run_id]
    if flow:
        sub = [flow] + sub
    dest_dir = base.joinpath(*sub)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{phase}.jsonl"
    dest = dest_dir / filename

    # Repoint any file-based rotating handlers. If a QueueListener is active,
    # update handlers wired behind it; otherwise, update root handlers.
    handlers: list[logging.Handler] = []
    try:
        from .queue_setup import effective_handlers  # type: ignore

        handlers = list(effective_handlers())
    except Exception:
        handlers = list(logging.getLogger().handlers)

    for h in handlers:
        try:
            if isinstance(h, (logging.handlers.RotatingFileHandler, logging.handlers.TimedRotatingFileHandler)):
                h.acquire()
                try:
                    try:
                        h.close()
                    except Exception:
                        pass
                    h.baseFilename = str(dest)
                    h.stream = h._open()
                finally:
                    h.release()
        except Exception:
            continue
    return dest
