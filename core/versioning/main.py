# PURPOSE:
#   CLI-oriented version info emitter without using stdout prints.
#
# OUTCOME:
#   Provides a main() entry that logs version information via the central
#   logging policy, satisfying CI rules that forbid print() in runtime code.
#
# INPUTS:
#   None. Reads version metadata from the package and environment (optional).
#
# OUTPUTS:
#   Emits a single structured log line at INFO level containing version JSON.
#
# DEPENDENCIES:
#   - core.logging.configure_logging/get_logger for policy-compliant logging.
#   - core.versioning.get_version_info for version metadata.

from __future__ import annotations

import json

from core.logging import configure_logging, get_logger
from . import get_version_info


def main() -> None:
    """Log version info as JSON using the configured logger.

    Outcome:
        Avoids printing to stdout; emits a single INFO record with the
        version payload. This entrypoint is intended for environments where
        printing is disallowed by runtime code policy.
    """

    # Ensure logging is initialized according to policy (honors env vars).
    try:
        configure_logging(force=False)
    except Exception:
        # Fall back to default logging if policy config is unavailable.
        pass

    logger = get_logger("cli")
    info = get_version_info()
    try:
        logger.info(json.dumps(info, ensure_ascii=False))
    except Exception:
        logger.info(str(info))


__all__ = ["main"]
