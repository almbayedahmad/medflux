from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import TextBlock

JsonDict = Dict[str, Any]

_LANG_ALIAS = {
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


def _ensure_float_list(values: Any) -> List[float]:
    if isinstance(values, list):
        floats: List[float] = []
        for value in values:
            try:
                floats.append(float(value))
            except Exception:
                continue
        return floats
    return []


def _normalise_text_lines(value: Any, fallback: str) -> List[str]:
    if isinstance(value, list):
        result = [str(item) for item in value if item is not None]
        return result if result else ([fallback] if fallback else [])
    if isinstance(value, str) and value:
        return [value]
    if fallback:
        lines = [line for line in fallback.splitlines() if line]
        return lines or ([fallback] if fallback else [])
    return []


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


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return default


def _tokenise_lang(raw: Any) -> List[str]:
    if raw is None:
        return []
    text = str(raw)
    if not text:
        return []
    return [token.strip() for token in text.replace(",", "+").split("+") if token]


def _normalise_lang(raw: Any, fallback: Any = None) -> str:
    tokens: List[str] = []
    tokens.extend(_tokenise_lang(raw))
    if not tokens:
        tokens.extend(_tokenise_lang(fallback))
    normalised: List[str] = []
    for token in tokens:
        mapped = _LANG_ALIAS.get(token.lower(), token.lower())
        if mapped in _ALLOWED_LANGS:
            if mapped not in normalised:
                normalised.append(mapped)
        elif mapped == "mixed":
            for alias in _ALLOWED_LANGS:
                if alias not in normalised:
                    normalised.append(alias)
    if not normalised:
        return _DEFAULT_LANG
    if len(normalised) == 2:
        return "de+en"
    return normalised[0]


def _lang_confidence(lang: str) -> float:
    if lang == "de+en":
        return 0.7
    if lang in _ALLOWED_LANGS:
        return 0.95
    return 0.5 if lang else 0.0


def _safe_char_map_ref(readers_dir: Path, block_id: str) -> str:
    return f"{readers_dir / 'text_blocks.jsonl'}#{block_id}"


def _infer_paragraph_style(is_heading: bool, is_list: bool) -> str:
    if is_heading:
        return "heading"
    if is_list:
        return "list"
    return "body"


def _token_count(text: str) -> int:
    return len([token for token in (text or "").replace("\n", " ").split() if token])


def _infer_numbering_marker(text: str) -> str:
    stripped = (text or "").lstrip()
    if not stripped:
        return ""
    prefixes = ("- ", "* ", "+ ", "\u0007 ", "\u0007")
    for prefix in prefixes:
        if stripped.startswith(prefix):
            return prefix.strip()
    if len(stripped) >= 3 and stripped[0].isdigit() and stripped[1] in {'.', ')'}:
        return stripped[:2]
    if len(stripped) >= 3 and stripped[0].isalpha() and stripped[1] in {'.', ')'}:
        return stripped[:2]
    return ""


def _derive_block_type(
    is_heading: bool,
    is_list: bool,
    bbox: List[float],
    page_height: Optional[float],
) -> str:
    if page_height and bbox and len(bbox) >= 4:
        y0 = float(bbox[1])
        y1 = float(bbox[3])
        top_thr = page_height * 0.1
        bottom_thr = page_height * 0.9
        if y0 <= top_thr:
            return "header"
        if y1 >= bottom_thr:
            return "footer"
    if is_heading:
        return "heading"
    if is_list:
        return "list_item"
    return "paragraph"


def build_text_blocks(
    readers_dir: Path,
    page_geometry: Dict[int, Dict[str, float]] | None = None,
) -> List[TextBlock]:
    path = readers_dir / "text_blocks.jsonl"
    if not path.exists():
        return []

    geometry_lookup = page_geometry or {}
    blocks: List[TextBlock] = []
    with path.open("r", encoding="utf-8") as handle:
        for index, raw_line in enumerate(handle):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item: JsonDict = json.loads(line)
            except Exception:
                continue
            if not isinstance(item, dict):
                continue

            block_id = str(item.get("id") or f"b{index:04d}")
            page = _as_int(item.get("page"))
            text_raw = str(item.get("text_raw") or item.get("text") or "")
            text_lines_list = _normalise_text_lines(item.get("text_lines"), text_raw)
            bbox = _ensure_float_list(item.get("bbox"))
            if len(bbox) != 4:
                bbox = (bbox + [0.0, 0.0, 0.0, 0.0])[:4]
            page_info = geometry_lookup.get(page) or {}
            page_width = page_info.get("width")
            page_height = page_info.get("height")

            block: TextBlock = {
                "id": block_id,
                "page": page,
                "text_raw": text_raw,
                "text_lines": text_lines_list,
                "bbox": bbox,
                "charmap_ref": _safe_char_map_ref(readers_dir, block_id),
                "token_count": _token_count(text_raw),
                "char_count": len(text_raw),
                "reading_order_index": _as_int(item.get("reading_order_index")) if item.get("reading_order_index") is not None else index,
            }

            is_heading_bool = _as_bool(item.get("is_heading_like"))
            is_list_bool = _as_bool(item.get("is_list_like"))
            block["is_heading_like"] = is_heading_bool
            block["is_list_like"] = is_list_bool

            lang_value = _normalise_lang(item.get("lang"), fallback=item.get("lang_hint"))
            block["lang"] = lang_value
            block["lang_conf"] = round(_lang_confidence(lang_value), 2)

            ocr_conf_avg = item.get("ocr_conf_avg")
            block["ocr_conf_avg"] = round(_as_float(ocr_conf_avg), 2) if ocr_conf_avg is not None else 0.0
            font_size_value = item.get("font_size_avg") or item.get("font_size")
            block["font_size"] = round(_as_float(font_size_value), 2) if font_size_value is not None else 0.0
            block["is_bold"] = _as_bool(item.get("is_bold"))
            block["is_upper"] = _as_bool(item.get("is_upper"))

            if item.get("char_count") is not None:
                block["char_count"] = _as_int(item.get("char_count"))

            block["paragraph_style"] = _infer_paragraph_style(is_heading_bool, is_list_bool)
            list_level_value = item.get("list_level")
            if list_level_value is not None:
                block["list_level"] = _as_int(list_level_value)
            else:
                block["list_level"] = 1 if is_list_bool else 0

            line_height = 0.0
            baseline_y = 0.0
            column_index = 0
            indent_level = 0
            if bbox and len(bbox) >= 4:
                y0 = float(bbox[1])
                y1 = float(bbox[3])
                x0 = float(bbox[0])
                x1 = float(bbox[2])
                line_height = max(0.0, y1 - y0)
                baseline_y = y1
                if page_width and page_width > 0:
                    center = (x0 + x1) / 2.0
                    normalized = min(max(center / page_width, 0.0), 1.0)
                    column_index = 1 if normalized >= 0.55 else 0
                    indent_unit = max(page_width * 0.04, 12.0)
                    indent_level = int(max(0.0, (x0 - 10.0) / indent_unit))
            block["line_height"] = round(line_height, 2)
            block["baseline_y"] = round(baseline_y, 2)
            block["column_index"] = column_index
            block["indent_level"] = indent_level

            numbering_marker = _infer_numbering_marker(text_raw)
            block["numbering_marker"] = numbering_marker
            block["block_type"] = _derive_block_type(is_heading_bool, is_list_bool, bbox, page_height)

            blocks.append(block)

    return blocks
