from __future__ import annotations

from collections import defaultdict
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
    "mixed": "mixed",
}

_ALLOWED_LANGS = ("de", "en")
_DEFAULT_LANG = "de"


def _tokenise_langs(raw: Any) -> List[str]:
    if raw is None:
        return []
    text = str(raw)
    if not text:
        return []
    return [token.strip() for token in text.replace(",", "+").split("+") if token]


def _collect_lang_tokens(raw_values: Iterable[Any] | None) -> List[str]:
    tokens: List[str] = []
    for raw in raw_values or []:
        for token in _tokenise_langs(raw):
            mapped = LANG_ALIAS.get(token.lower(), token.lower())
            if mapped in _ALLOWED_LANGS:
                if mapped not in tokens:
                    tokens.append(mapped)
            elif mapped == "mixed":
                for alias in _ALLOWED_LANGS:
                    if alias not in tokens:
                        tokens.append(alias)
    return tokens


def _normalise_lang(raw: Any, fallback: Iterable[str] | None = None) -> str:
    tokens = _collect_lang_tokens([raw])
    if not tokens:
        tokens = _collect_lang_tokens(fallback)
    if not tokens:
        return _DEFAULT_LANG
    has_de = "de" in tokens
    has_en = "en" in tokens
    if has_de and has_en:
        return "de+en"
    if has_de:
        return "de"
    if has_en:
        return "en"
    return _DEFAULT_LANG


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


def _page_size_payload(width: Optional[float], height: Optional[float]) -> Dict[str, float]:
    width_val = float(width) if width is not None else 0.0
    height_val = float(height) if height is not None else 0.0
    return {"width": width_val, "height": height_val}


def _normalise_rotation(value: Any) -> int:
    try:
        rotation = float(value)
    except Exception:
        rotation = 0.0
    if rotation < 0:
        rotation %= 360.0
    snapped = round(rotation / 90.0) * 90.0
    return int(snapped % 360.0)


def _compute_lang_share(
    blocks: Iterable[JsonDict],
    fallback_tokens: List[str],
) -> Dict[str, float]:
    totals: Dict[str, float] = defaultdict(float)
    total_chars = 0.0

    for block in blocks or []:
        char_count = _as_int(block.get("char_count") or len(str(block.get("text_raw") or "")))
        if char_count <= 0:
            continue
        tokens = _collect_lang_tokens([block.get("lang"), block.get("lang_hint")])
        if not tokens:
            tokens = list(fallback_tokens)
        if not tokens:
            continue
        weight = char_count / max(len(tokens), 1)
        for lang in tokens:
            totals[lang] += weight
        total_chars += char_count

    if total_chars <= 0:
        return {}

    shares: Dict[str, float] = {}
    for lang in _ALLOWED_LANGS:
        score = totals.get(lang)
        if score:
            shares[lang] = round(score / total_chars, 4)
    return shares


def _detect_header_footer(blocks: Iterable[JsonDict], page_height: Optional[float]) -> bool:
    if not blocks or not page_height or page_height <= 0:
        return False
    top_threshold = float(page_height) * 0.12
    bottom_threshold = float(page_height) - top_threshold
    has_header = False
    has_footer = False
    for block in blocks:
        bbox = block.get("bbox") or []
        if not isinstance(bbox, list) or len(bbox) < 4:
            continue
        try:
            y0 = float(bbox[1])
            y1 = float(bbox[3])
        except Exception:
            continue
        if y0 <= top_threshold:
            has_header = True
        if y1 >= bottom_threshold:
            has_footer = True
        if has_header and has_footer:
            return True
    return has_header or has_footer


def _compute_text_density(chars: int, width: Optional[float], height: Optional[float]) -> float:
    if chars <= 0 or width is None or height is None:
        return 0.0
    area = float(width) * float(height)
    if area <= 0:
        return 0.0
    return round(chars / area, 6)


def build_per_page_stats(
    summary_payload: Dict[str, Any],
    *,
    page_geometry: Dict[int, Dict[str, float]] | None = None,
    lang_fallback: Iterable[str] | None = None,
    multi_column_pages: Set[int] | None = None,
    blocks_by_page: Dict[int, List[Dict[str, Any]]] | None = None,
) -> List[PerPageStat]:
    per_page_raw = summary_payload.get("per_page_stats")
    if per_page_raw is None:
        per_page_raw = (summary_payload.get("summary", {}) or {}).get("per_page_stats")

    geometry = page_geometry or {}
    multi_column_pages = multi_column_pages or set()
    blocks_lookup = blocks_by_page or {}
    fallback_tokens = _collect_lang_tokens(lang_fallback)

    stats: List[PerPageStat] = []
    for entry in per_page_raw or []:
        if not isinstance(entry, dict):
            continue
        page_number = _as_int(entry.get("page")) or 0
        source_normalised = _normalise_source(str(entry.get("source") or entry.get("decision") or "text"))
        lang_value = _normalise_lang(entry.get("lang"), fallback=lang_fallback)
        locale_value = _normalise_lang(entry.get("locale"), fallback=lang_fallback)
        flags_list = _normalise_flags(entry.get("flags") or [])

        chars = _as_int(entry.get("chars"))
        ocr_words = _as_int(entry.get("ocr_words"))
        tables_found = _as_int(entry.get("tables_found"))
        table_cells = _as_int(entry.get("table_cells"))
        has_table = bool(entry.get("has_table")) or tables_found > 0
        time_ms = round(_as_float(entry.get("time_ms")), 2)

        ocr_conf_value = entry.get("ocr_conf")
        if ocr_conf_value is None:
            ocr_conf_value = entry.get("ocr_conf_avg")
        ocr_conf = round(_as_float(ocr_conf_value), 2) if ocr_conf_value is not None else 0.0

        page_info = geometry.get(page_number) or {}
        width = page_info.get("width")
        height = page_info.get("height")
        rotation_value = _normalise_rotation(page_info.get("rotation"))
        page_size = _page_size_payload(width, height)

        is_multi_column = page_number in multi_column_pages
        columns_count = 2 if is_multi_column else 1

        skew_deg = round(_as_float(entry.get("skew_deg")), 2)
        noise_score = round(_as_float(entry.get("noise_score")), 3)
        if noise_score < 0.0:
            noise_score = 0.0
        if noise_score > 1.0:
            noise_score = 1.0
        text_density = _compute_text_density(chars, width, height)

        blocks = blocks_lookup.get(page_number, [])
        lang_share = _compute_lang_share(blocks, fallback_tokens)
        if not lang_share:
            if lang_value == "de+en":
                lang_share = {"de": 0.5, "en": 0.5}
            elif lang_value in _ALLOWED_LANGS:
                lang_share = {lang_value: 1.0}
            else:
                lang_share = {}

        has_header_footer = _detect_header_footer(blocks, height)

        images_count = _as_int(page_info.get("images_count"))
        graphics_count = _as_int(page_info.get("graphics_objects_count"))
        has_images = images_count > 0

        stat: PerPageStat = {
            "page": page_number,
            "source": source_normalised,
            "chars": chars,
            "lang": lang_value,
            "lang_share": lang_share,
            "ocr_conf": ocr_conf,
            "ocr_words": ocr_words,
            "tables_found": tables_found,
            "table_cells": table_cells,
            "flags": flags_list,
            "rotation_deg": rotation_value,
            "skew_deg": skew_deg,
            "is_multi_column": is_multi_column,
            "columns_count": columns_count,
            "page_size": page_size,
            "noise_score": noise_score,
            "text_density": text_density,
            "has_header_footer": has_header_footer,
            "has_images": has_images,
            "images_count": images_count,
            "graphics_objects_count": graphics_count,
            "time_ms": time_ms,
            "locale": locale_value,
            "decision": str(entry.get("decision") or entry.get("source") or "text"),
            "has_table": has_table,
        }

        stats.append(stat)
    return stats
