from __future__ import annotations

"""Upstream connector for the readers stage."""

from typing import Any, Dict, List, Sequence


def connect_readers_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    if items is None:
        return []
    return [dict(item) for item in items]
