from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .types import TextBlock

JsonDict = Dict[str, Any]


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


def _normalise_text_lines(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
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


def _as_bool(value: Any) -> bool:
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
    return False


def _safe_lang(item: JsonDict) -> str:
    lang = item.get("lang") or item.get("lang_hint")
    if not lang:
        return "unknown"
    return str(lang)


def _safe_char_map_ref(readers_dir: Path, block_id: str) -> str:
    return f"{readers_dir / 'text_blocks.jsonl'}#{block_id}"


def _infer_paragraph_style(is_heading: bool, is_list: bool) -> str:
    if is_heading:
        return "heading"
    if is_list:
        return "list"
    return "body"


def build_text_blocks(readers_dir: Path) -> List[TextBlock]:
    path = readers_dir / "text_blocks.jsonl"
    if not path.exists():
        return []

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
            text_lines = _normalise_text_lines(item.get("text_lines"))
            bbox = _ensure_float_list(item.get("bbox"))

            block: TextBlock = {
                "id": block_id,
                "page": page,
                "text_raw": text_raw,
                "text_lines": text_lines,
                "bbox": bbox,
                "charmap_ref": _safe_char_map_ref(readers_dir, block_id),
            }

            if item.get("reading_order_index") is not None:
                block["reading_order_index"] = _as_int(item.get("reading_order_index"))

            is_heading = item.get("is_heading_like")
            is_heading_bool = _as_bool(is_heading) if is_heading is not None else False
            is_list = item.get("is_list_like")
            is_list_bool = _as_bool(is_list) if is_list is not None else False

            if is_heading is not None:
                block["is_heading_like"] = is_heading_bool
            if is_list is not None:
                block["is_list_like"] = is_list_bool

            block["lang"] = _safe_lang(item)

            if item.get("ocr_conf_avg") is not None:
                block["ocr_conf_avg"] = _as_float(item.get("ocr_conf_avg"))
            if item.get("font_size_avg") is not None:
                block["font_size"] = _as_float(item.get("font_size_avg"))
            if item.get("is_bold") is not None:
                block["is_bold"] = _as_bool(item.get("is_bold"))
            if item.get("is_upper") is not None:
                block["is_upper"] = _as_bool(item.get("is_upper"))
            if item.get("char_count") is not None:
                block["char_count"] = _as_int(item.get("char_count"))

            block["paragraph_style"] = _infer_paragraph_style(is_heading_bool, is_list_bool)
            block["list_level"] = 1 if is_list_bool else 0

            blocks.append(block)

    return blocks
