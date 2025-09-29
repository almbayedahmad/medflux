from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set

from .types import PerPageStat

JsonDict = Dict[str, Any]

LANG_ALIAS = {
    "deu": "de",
    "ger": "de",
    "german": "de",
    "de": "de",
    "eng": "en",
    "english": "en",
    "en": "en",
    "mixed": "de+en",
}


def _tokenise_langs(raw: Any) -> List[str]:
    tokens: List[str] = []
    if raw is None:
        return tokens
    for part in str(raw).replace(',', '+').split('+'):
        token = part.strip()
        if token:
            tokens.append(token)
    return tokens


def _normalise_lang(raw: Any, fallback: Iterable[str] | None = None) -> str:
    tokens = _tokenise_langs(raw)
    if not tokens and fallback:
        for item in fallback:
            tokens.extend(_tokenise_langs(item))
    normalised: List[str] = []
    for token in tokens:
        lower = token.lower()
        mapped = LANG_ALIAS.get(lower, lower)
        if mapped and mapped not in normalised:
            normalised.append(mapped)
    if not normalised:
        return "unknown"
    if len(normalised) == 1:
        return normalised[0]
    return "+".join(sorted(normalised))


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


def _normalise_source(raw: str) -> str:
    lowered = (raw or "").lower()
    if "ocr" in lowered and "native" in lowered:
        return "mixed"
    if "ocr" in lowered:
        return "ocr"
    if "text" in lowered:
        return "text"
    if "native" in lowered:
        return "text"
    return lowered or "text"


def _page_size_payload(width: Optional[float], height: Optional[float]) -> Optional[Dict[str, float]]:
    if width is None or height is None:
        return None
    return {"width": float(width), "height": float(height)}


def build_per_page_stats(
    summary_payload: Dict[str, Any],
    *,
    page_geometry: Dict[int, Dict[str, float]] | None = None,
    lang_fallback: Iterable[str] | None = None,
    multi_column_pages: Set[int] | None = None,
) -> List[PerPageStat]:
    per_page_raw = summary_payload.get("per_page_stats")
    if per_page_raw is None:
        per_page_raw = (summary_payload.get("summary", {}) or {}).get("per_page_stats")

    geometry = page_geometry or {}
    multi_column_pages = multi_column_pages or set()

    stats: List[PerPageStat] = []
    for entry in per_page_raw or []:
        if not isinstance(entry, dict):
            continue
        page_number = _as_int(entry.get("page"))
        source_normalised = _normalise_source(str(entry.get("source") or entry.get("decision") or "text"))
        lang_value = _normalise_lang(entry.get("lang"), fallback=lang_fallback)
        locale_value = _normalise_lang(entry.get("locale"))

        stat: PerPageStat = {
            "page": page_number,
            "source": source_normalised,
            "conf": _as_float(entry.get("conf")),
            "ocr_words": _as_int(entry.get("ocr_words")),
            "chars": _as_int(entry.get("chars")),
            "has_table": bool(entry.get("has_table")),
            "tables_found": _as_int(entry.get("tables_found")),
            "table_cells": _as_int(entry.get("table_cells")),
            "decision": str(entry.get("decision") or entry.get("source") or "text"),
            "time_ms": _as_float(entry.get("time_ms")),
            "lang": lang_value,
            "locale": locale_value,
            "flags": _normalise_flags(entry.get("flags") or []),
            "is_multi_column": page_number in multi_column_pages,
        }

        ocr_conf = entry.get("ocr_conf")
        if ocr_conf is None:
            ocr_conf = entry.get("ocr_conf_avg")
        if ocr_conf is not None:
            value = _as_float(ocr_conf)
            stat["ocr_conf"] = value
            stat["ocr_conf_avg"] = value

        page_info = geometry.get(page_number) or {}
        width = page_info.get("width")
        height = page_info.get("height")
        rotation = page_info.get("rotation")
        if rotation is not None:
            stat["rotation_deg"] = float(rotation)
        size_payload = _page_size_payload(width, height)
        if size_payload is not None:
            stat["page_size"] = size_payload

        stats.append(stat)
    return stats
