from __future__ import annotations

"""Upstream connector for the detect_type stage."""

from typing import Any, Dict, List, Sequence


def connect_detect_type_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """Return the normalised list of generic items provided to the stage."""

    if items is None:
        return []
    return [dict(item) for item in items]
