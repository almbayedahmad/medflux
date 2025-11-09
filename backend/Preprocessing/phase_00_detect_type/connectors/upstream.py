# PURPOSE:
#   Backward-compat connector shim exposing the detect_type upstream connector
#   under the new connectors/ package.
# OUTCOME:
#   Enables v2 API to import from connectors while preserving legacy modules.

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def connect_detect_type_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """Return the normalised list of generic items provided to the stage."""

    if items is None:
        return []
    return [dict(item) for item in items]

__all__ = ["connect_detect_type_upstream_connector"]
