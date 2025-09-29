from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .types import PerPageStat


PageEntry = Dict[str, Any]


def _as_int(value: Any) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str) and value.strip():
            return int(float(value))
    except Exception:
        return 0
    return 0


def _as_float(value: Any) -> float:
    try:
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip():
            return float(value)
    except Exception:
        return 0.0
    return 0.0


def _normalise_flags(flags: Iterable[Any]) -> List[str]:
    result: List[str] = []
    for flag in flags or []:
        if not flag:
            continue
        flag_str = str(flag).strip()
        if flag_str:
            result.append(flag_str)
    return result


def _normalise_entry(entry: PageEntry, fallback_source: str) -> PerPageStat:
    page_number = _as_int(entry.get("page"))
    source = str(entry.get("source") or fallback_source or "native")
    decision = str(entry.get("decision") or source)

    stat: PerPageStat = {
        "page": page_number,
        "source": source,
        "conf": _as_float(entry.get("conf")),
        "ocr_words": _as_int(entry.get("ocr_words")),
        "chars": _as_int(entry.get("chars")),
        "has_table": bool(entry.get("has_table")),
        "tables_found": _as_int(entry.get("tables_found")),
        "table_cells": _as_int(entry.get("table_cells")),
        "decision": decision,
        "time_ms": _as_float(entry.get("time_ms")),
        "lang": str(entry.get("lang") or "unknown"),
        "locale": str(entry.get("locale") or "unknown"),
        "flags": _normalise_flags(entry.get("flags") or []),
    }

    if entry.get("ocr_conf_avg") is not None:
        stat["ocr_conf_avg"] = _as_float(entry.get("ocr_conf_avg"))

    return stat


def build_per_page_stats(summary_payload: Dict[str, Any]) -> List[PerPageStat]:
    """Return normalised per-page statistics ready for doc meta output."""
    raw_entries = summary_payload.get("per_page_stats")
    if raw_entries is None:
        raw_entries = (summary_payload.get("summary", {}) or {}).get("per_page_stats")

    stats: List[PerPageStat] = []
    for entry in raw_entries or []:
        if not isinstance(entry, dict):
            continue
        fallback_source = str(entry.get("source") or entry.get("decision") or "native")
        stats.append(_normalise_entry(entry, fallback_source))
    return stats
