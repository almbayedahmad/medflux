from __future__ import annotations

import json
from . import get_version_info
from core.logging import configure_logging, get_logger


def main() -> None:
    """Emit version info via structured logging (no prints).

    Outcome:
        Logs a JSON object with version fields so runtime code avoids stdout
        prints. Tests should capture logs (caplog) instead of stdout.
    """
    try:
        # Do not force reconfigure to preserve existing handlers (e.g., caplog)
        configure_logging(force=False)
    except Exception:
        pass
    info = get_version_info()
    logger = get_logger("cli")
    try:
        logger.info(json.dumps(info, ensure_ascii=False))
    except Exception:
        logger.info(str(info))


if __name__ == "__main__":
    main()
