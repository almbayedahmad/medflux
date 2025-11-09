# PURPOSE:
#   Minimal upstream connector for phase_07_table_extraction (v2 scaffold).
# OUTCOME:
#   Normalizes incoming items to a list of dicts.

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def connect_table_extraction_upstream_connector(items: Sequence[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    return [dict(x) for x in (items or [])]
