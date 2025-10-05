from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ..internal_helpers.reader_helpers_runtime_settings import get_runtime_settings
from main_helpers.geom_utils import to_bottom_left, validate_bbox
from main_helpers.lang_utils import collapse_doc_lang, normalise_lang, tokenise_langs
from main_helpers.num_utils import as_float, as_int

from .readers_output_types import TextBlock

JsonDict = Dict[str, Any]

_ALLOWED_LANGS = ("de", "en")
_DEFAULT_LANG = "de"

SETTINGS = get_runtime_settings()
MULTI_COLUMN_LEFT_THR = float(SETTINGS.thresholds.get("multi_column_left_thr", 0.15))
MULTI_COLUMN_RIGHT_THR = float(SETTINGS.thresholds.get("multi_column_right_thr", 0.85))


def compute_readers_split_lang_candidates(*values: Any) -> List[str]:
    tokens: List[str] = []
    stack = list(values)
    while stack:
        raw = stack.pop()
        if raw is None:
            continue
        if isinstance(raw, (list, tuple, set)):
            stack.extend(raw)
            continue
        if isinstance(raw, dict):
            stack.extend(raw.values())
            continue
        text_value = str(raw)
        if not text_value:
            continue
        for part in text_value.replace(",", "+").split("+"):
            token = part.strip()
            if not token:
                continue
            mapped = normalise_lang(token)
            if mapped in _ALLOWED_LANGS:
                if mapped not in tokens:
                    tokens.append(mapped)
            elif mapped in {"mixed", "de+en"}:
                for alias in _ALLOWED_LANGS:
                    if alias not in tokens:
                        tokens.append(alias)
    return tokens



def compute_readers_resolve_lang(raw: Any, fallback: Any = None, text: str | None = None) -> str:
    tokens = compute_readers_split_lang_candidates(raw)
    if not tokens:
        tokens = compute_readers_split_lang_candidates(fallback)
    if not tokens and text:
        detected = tokenise_langs(text)
        tokens = [lang for lang in _ALLOWED_LANGS if detected.get(lang, 0) > 0]
    if not tokens:
        return _DEFAULT_LANG
    share = {lang: (1.0 if lang in tokens else 0.0) for lang in _ALLOWED_LANGS}
    collapsed = collapse_doc_lang(share)
    return collapsed or _DEFAULT_LANG


def compute_readers_ensure_float_list(values: Any) -> List[float]:
    if isinstance(values, list):
        floats: List[float] = []
        for value in values:
            try:
                floats.append(float(value))
            except Exception:
                continue
        return floats
    return []


def normalize_readers_text_lines(value: Any, fallback: str) -> List[str]:
    if isinstance(value, list):
        result = [str(item) for item in value if item is not None]
        return result if result else ([fallback] if fallback else [])
    if isinstance(value, str) and value:
        return [value]
    if fallback:
        lines = [line for line in fallback.splitlines() if line]
        return lines or ([fallback] if fallback else [])
    return []


def check_readers_bool_flag(value: Any, default: bool = False) -> bool:
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


def compute_readers_lang_confidence(lang: str) -> float:
    if lang == "de+en":
        return 0.7
    if lang in _ALLOWED_LANGS:
        return 0.95
    return 0.5 if lang else 0.0



def compute_readers_paragraph_style(is_heading: bool, is_list: bool) -> str:
    if is_heading:
        return "heading"
    if is_list:
        return "list"
    return "body"


def compute_readers_token_count(text: str) -> int:
    return len([token for token in (text or "").replace("\n", " ").split() if token])


def compute_readers_numbering_marker(text: str) -> str:
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


def compute_readers_block_type(
    is_heading: bool,
    is_list: bool,
    bbox: List[float],
    page_height: Optional[float],
) -> str:
    if page_height and bbox and len(bbox) >= 4:
        y0 = float(bbox[1])
        y1 = float(bbox[3])
        top_thr = page_height * 0.1
        bottom_thr = page_height * 0.1
        if y1 >= page_height - top_thr:
            return "header"
        if y0 <= bottom_thr:
            return "footer"
    if is_heading:
        return "heading"
    if is_list:
        return "list_item"
    return "paragraph"


def compute_readers_text_blocks(
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
            page = as_int(item.get("page"))
            text_raw = str(item.get("text_raw") or item.get("text") or "")
            text_lines_list = normalize_readers_text_lines(item.get("text_lines"), text_raw)
            bbox = compute_readers_ensure_float_list(item.get("bbox"))
            if len(bbox) != 4:
                bbox = (bbox + [0.0, 0.0, 0.0, 0.0])[:4]
            page_info = geometry_lookup.get(page) or {}
            page_width = page_info.get("width")
            page_height = page_info.get("height")
            if page_height:
                bbox = to_bottom_left(bbox, float(page_height))

            block: TextBlock = {
                "id": block_id,
                "page": page,
                "text_raw": text_raw,
                "text_lines": text_lines_list,
                "bbox": bbox,
                "token_count": compute_readers_token_count(text_raw),
                "char_count": len(text_raw),
                "reading_order_index": as_int(item.get("reading_order_index")) if item.get("reading_order_index") is not None else index,
            }

            is_heading_bool = check_readers_bool_flag(item.get("is_heading_like"))
            is_list_bool = check_readers_bool_flag(item.get("is_list_like"))
            block["is_heading_like"] = is_heading_bool
            block["is_list_like"] = is_list_bool

            lang_value = compute_readers_resolve_lang(item.get("lang"), fallback=item.get("lang_hint"), text=text_raw)
            block["lang"] = lang_value
            block["lang_conf"] = round(compute_readers_lang_confidence(lang_value), 2)

            ocr_conf_avg = item.get("ocr_conf_avg")
            block["ocr_conf_avg"] = round(as_float(ocr_conf_avg), 2) if ocr_conf_avg is not None else 0.0
            font_size_value = item.get("font_size_avg") or item.get("font_size")
            block["font_size"] = round(as_float(font_size_value), 2) if font_size_value is not None else 0.0
            block["is_bold"] = check_readers_bool_flag(item.get("is_bold"))
            block["is_upper"] = check_readers_bool_flag(item.get("is_upper"))

            if item.get("char_count") is not None:
                block["char_count"] = as_int(item.get("char_count"))

            block["paragraph_style"] = compute_readers_paragraph_style(is_heading_bool, is_list_bool)
            list_level_value = item.get("list_level")
            if list_level_value is not None:
                block["list_level"] = as_int(list_level_value)
            else:
                block["list_level"] = 1 if is_list_bool else 0

            line_height = 0.0
            baseline_y = 0.0
            column_index = 0
            indent_level = 0
            if validate_bbox(bbox):
                y0 = float(bbox[1])
                y1 = float(bbox[3])
                x0 = float(bbox[0])
                x1 = float(bbox[2])
                line_height = max(0.0, y1 - y0)
                baseline_y = y0
                if page_width and page_width > 0:
                    center = (x0 + x1) / 2.0
                    normalized = min(max(center / page_width, 0.0), 1.0)
                    if normalized >= MULTI_COLUMN_RIGHT_THR:
                        column_index = 1
                    elif normalized <= MULTI_COLUMN_LEFT_THR:
                        column_index = 0
                    else:
                        column_index = 0
                    indent_unit = max(page_width * 0.04, 12.0)
                    indent_level = int(max(0.0, (x0 - 10.0) / indent_unit))
            block["line_height"] = round(line_height, 2)
            block["baseline_y"] = round(baseline_y, 2)
            block["column_index"] = column_index
            block["indent_level"] = indent_level

            numbering_marker = compute_readers_numbering_marker(text_raw)
            block["numbering_marker"] = numbering_marker
            block["block_type"] = compute_readers_block_type(is_heading_bool, is_list_bool, bbox, page_height)

            blocks.append(block)

    return blocks




