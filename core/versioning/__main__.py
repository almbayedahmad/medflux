from __future__ import annotations

import json
from . import get_version_info
from core.logging import get_logger


def main() -> None:
    """CLI entry to emit version info via logging (no prints)."""
    info = get_version_info()
    logger = get_logger("cli")
    try:
        logger.info(json.dumps(info, ensure_ascii=False))
    except Exception:
        logger.info(str(info))


if __name__ == "__main__":
    main()
