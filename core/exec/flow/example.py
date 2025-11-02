from __future__ import annotations

from typing import Any, Dict

from core.logging import get_logger, with_context
from core.versioning import get_version


def example_flow(context: Dict[str, Any]) -> Dict[str, Any]:
    log = with_context(get_logger("medflux.core.exec.flow.example"), flow="example", version=get_version())
    log.info("Starting example flow")
    # Simulate work using provided context
    payload = {"ok": True, "echo": context.get("echo")}
    log.debug("Example flow payload prepared: %s", payload)
    return payload
