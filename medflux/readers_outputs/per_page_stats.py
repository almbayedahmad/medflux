from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set

from utils.config import CFG
from utils.lang_utils import collapse_doc_lang, normalise_lang, tokenise_langs
from utils.num_utils import as_float, as_int

from .types import PerPageStat

JsonDict = Dict[str, Any]

_ALLOWED_LANGS = ("de", "en")
_DEFAULT_LANG = "de"

OCR_LOW_CONF = float(CFG["thresholds"]["ocr_low_conf"])
OCR_LOW_TEXT_MIN_WORDS = int(CFG["thresholds"]["ocr_low_text_min_words"])
SUSPICIOUS_TEXT_CHARS_MIN = int(CFG["thresholds"]["suspicious_text_chars_min"])


def _lang_tokens(raw_values: Iterable[Any] | None) -> List[str]:
    tokens: List[str] = []
    if raw_values is None:
        return tokens
    if isinstance(raw_values, str):
        iter_values: Iterable[Any] = [raw_values]
    else:
        iter_values = raw_values
    for raw in iter_values or []:
        if raw is None:
            continue
        for part in str(raw).replace(",", "+").split("+"):
            token = part.strip()
            if not token:
                continue
            mapped = normalise_lang(token)
            if mapped in _ALLOWED_LANGS:
                if mapped not in tokens:
                    tokens.append(mapped)
            elif mapped == "mixed" or token.lower() == "mixed":
                for alias in _ALLOWED_LANGS:
                    if alias not in tokens:
                        tokens.append(alias)
    return tokens



def _normalise_lang(raw: Any, fallback: Iterable[str] | None = None) -> str:
    tokens = _lang_tokens([raw])
    if not tokens and fallback:
        tokens = _lang_tokens(fallback)
    if not tokens:
        return _DEFAULT_LANG
    share = {lang: (1.0 if lang in tokens else 0.0) for lang in _ALLOWED_LANGS}
    collapsed = collapse_doc_lang(share)
    return collapsed or _DEFAULT_LANG


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
        char_count = as_int(block.get("char_count") or len(str(block.get("text_raw") or "")))
        if char_count <= 0:
            continue
        tokens = _lang_tokens([block.get("lang"), block.get("lang_hint")])
        if not tokens:
            tokens = _lang_tokens(fallback_tokens)
        if not tokens:
            detected_counts = tokenise_langs(str(block.get("text_raw") or ""))
            tokens = [lang for lang in _ALLOWED_LANGS if detected_counts.get(lang, 0) > 0]
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
    height = float(page_height)
    margin = height * 0.12
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
        if y1 >= height - margin:
            has_header = True
        if y0 <= margin:
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
    fallback_tokens = _lang_tokens(lang_fallback)

    stats: List[PerPageStat] = []
    for entry in per_page_raw or []:
        if not isinstance(entry, dict):
            continue
        page_number = as_int(entry.get("page")) or 0
        source_normalised = _normalise_source(str(entry.get("source") or entry.get("decision") or "text"))
        lang_value = _normalise_lang(entry.get("lang"), fallback=lang_fallback)
        locale_value = _normalise_lang(entry.get("locale"), fallback=lang_fallback)
        flags_list = _normalise_flags(entry.get("flags") or [])

        chars = as_int(entry.get("chars"))
        ocr_words = as_int(entry.get("ocr_words"))
        tables_found = as_int(entry.get("tables_found"))
        table_cells = as_int(entry.get("table_cells"))
        has_table = bool(entry.get("has_table")) or tables_found > 0
        time_ms = round(as_float(entry.get("time_ms")), 2)

        ocr_conf_value = entry.get("ocr_conf")
        if ocr_conf_value is None:
            ocr_conf_value = entry.get("ocr_conf_avg")
        ocr_conf = None
        if ocr_conf_value is not None:
            try:
                ocr_conf = round(float(ocr_conf_value), 2)
            except Exception:
                ocr_conf = round(as_float(ocr_conf_value), 2)

        flags_generated: List[str] = []
        if ocr_conf is not None and ocr_conf < OCR_LOW_CONF:
            flags_generated.append("low_conf_page")
        if (ocr_conf is not None and ocr_conf >= OCR_LOW_CONF and ocr_words is not None and ocr_words < OCR_LOW_TEXT_MIN_WORDS):
            flags_generated.append("low_text_page")
        if source_normalised == "text" and chars is not None and chars < SUSPICIOUS_TEXT_CHARS_MIN:
            flags_generated.append("suspicious_text_page")
        combined_flags = []
        for flag in flags_list + flags_generated:
            if flag and flag not in combined_flags:
                combined_flags.append(flag)

        page_info = geometry.get(page_number) or {}
        width = page_info.get("width")
        height = page_info.get("height")
        rotation_value = _normalise_rotation(page_info.get("rotation"))
        page_size = _page_size_payload(width, height)

        is_multi_column = page_number in multi_column_pages
        columns_count = 2 if is_multi_column else 1

        skew_deg = round(as_float(entry.get("skew_deg")), 2)
        noise_score = round(as_float(entry.get("noise_score")), 3)
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

        images_count = as_int(page_info.get("images_count"))
        graphics_count = as_int(page_info.get("graphics_objects_count"))
        has_images = images_count > 0

        stat: PerPageStat = {
            "page": page_number,
            "source": source_normalised,
            "chars": chars,
            "lang": lang_value,
            "lang_share": lang_share,
            "ocr_conf": ocr_conf if ocr_conf is not None else 0.0,
            "ocr_words": ocr_words,
            "tables_found": tables_found,
            "table_cells": table_cells,
            "flags": combined_flags,
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
