# PURPOSE:
#   Minimal upstream connector for phase_08_heavy_normalization (v2 scaffold).
# OUTCOME:
#   Normalizes incoming items to a list of dicts.

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def connect_heavy_normalization_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    return [dict(x) for x in (items or [])]
