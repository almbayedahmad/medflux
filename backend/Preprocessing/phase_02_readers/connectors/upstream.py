# PURPOSE:
#   Backward-compat connector shim exposing readers upstream under connectors/.
# OUTCOME:
#   Allows v2 API to import from connectors while preserving legacy modules.

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def connect_readers_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if items is None:
        return []
    return [dict(item) for item in items]

__all__ = ["connect_readers_upstream_connector"]
