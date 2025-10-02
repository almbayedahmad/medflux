from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from utils.geom_utils import to_bottom_left
from utils.lang_utils import normalise_lang
from utils.num_utils import as_float, as_int

from .components import (
    build_detected_languages,
    build_locale_hints,
    load_artifacts,
    normalize_encoding,
    prepare_timings,
    summarise_logs,
)
from .per_page_stats import build_per_page_stats
from .text_blocks import build_text_blocks
from .types import Artifact, DocMeta, TextBlock, WordEntry, ZoneEntry

READER_VERSION = "unified-readers-v1"
_DEFAULT_OCR_LANGS = "deu+eng"


def _map_file_type(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    mapping = {
        "pdf_text": "pdf_text",
        "pdf_scanned": "pdf_scan",
        "pdf_scan": "pdf_scan",
        "pdf_mixed": "pdf_scan_hybrid",
        "pdf_scan_hybrid": "pdf_scan_hybrid",
        "docx": "docx",
        "image": "image",
        "txt": "pdf_text",
    }
    return mapping.get(value, "unknown")


def _coordinate_unit(file_type: str) -> str:
    if file_type.startswith("pdf"):
        return "pdf_points"
    if file_type == "docx":
        return "docx_emus"
    if file_type == "image":
        return "image_pixels"
    return "unknown"


def _fallback_lang_tokens(*values: Any) -> List[str]:
    tokens: List[str] = []
    stack: List[Any] = list(values)
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
            token = normalise_lang(part.strip())
            if not token:
                continue
            if token in {"mixed", "de+en"}:
                for alias in ("de", "en"):
                    if alias not in tokens:
                        tokens.append(alias)
            else:
                if token not in tokens:
                    tokens.append(token)
    if not tokens:
        tokens = ["de", "en"]
    return tokens


def _float_list(value: Any) -> List[float]:
    if not isinstance(value, list):
        return []
    floats: List[float] = []
    for item in value:
        try:
            floats.append(float(item))
        except Exception:
            continue
    return floats


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    entries.append(obj)
    except Exception:
        return []
    return entries


def _load_words(
    readers_dir: Path,
    page_geometry: Dict[int, Dict[str, float]],
    blocks_lookup: Dict[int, List[Dict[str, Any]]],
) -> List[WordEntry]:
    words_path = readers_dir / "words.jsonl"
    entries = _load_jsonl(words_path)
    words: List[WordEntry] = []
    if not entries:
        return words

    block_index: Dict[tuple[int, str], List[float]] = {}
    for page, blocks in blocks_lookup.items():
        for block in blocks or []:
            block_id = str(block.get("id") or "")
            if not block_id:
                continue
            bbox = block.get("bbox")
            if isinstance(bbox, list) and len(bbox) == 4:
                block_index[(int(page), block_id)] = [float(x) for x in bbox]

    for item in entries:
        page = as_int(item.get("page"))
        page_info = page_geometry.get(page) or {}
        height = page_info.get("height")
        bbox_raw = _float_list(item.get("bbox"))
        if page <= 0 or len(bbox_raw) != 4 or not height:
            continue
        bbox = to_bottom_left(bbox_raw, float(height))
        block_id = str(item.get("block_id") or "")
        if block_id:
            block_bbox = block_index.get((page, block_id))
            if block_bbox and _bbox_equal(block_bbox, bbox):
                continue
        word_text = str(item.get("text") or "")
        word_conf = float(as_float(item.get("ocr_conf"), default=0.0) or 0.0)
        word_entry: WordEntry = {
            "block_id": block_id,
            "page": page,
            "text": word_text,
            "bbox": bbox,
            "ocr_conf": word_conf,
        }
        words.append(word_entry)
    return words


def _load_zones(readers_dir: Path) -> List[ZoneEntry]:
    zones_path = readers_dir / "zones.jsonl"
    entries = _load_jsonl(zones_path)
    zones: List[ZoneEntry] = []
    for item in entries:
        zone: ZoneEntry = {
            "page": as_int(item.get("page")),
            "bbox": _float_list(item.get("bbox")),
            "type": str(item.get("type") or ""),
        }
        zones.append(zone)
    return zones


def _extract_page_geometry(summary: Dict[str, Any]) -> Dict[int, Dict[str, float]]:
    geometry: Dict[int, Dict[str, float]] = {}
    for key in ("page_geometry", "page_dimensions", "page_sizes", "page_metrics"):
        payload = summary.get(key)
        if isinstance(payload, dict):
            for page_key, entry in payload.items():
                page = as_int(page_key)
                if page <= 0 or not isinstance(entry, dict):
                    continue
                geom = geometry.setdefault(page, {})
                for field in ("width", "height", "rotation", "images_count", "graphics_objects_count"):
                    if entry.get(field) is not None:
                        geom[field] = float(as_float(entry.get(field)))
        elif isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                page = as_int(entry.get("page"))
                if page <= 0:
                    continue
                geom = geometry.setdefault(page, {})
                for field in ("width", "height", "rotation", "images_count", "graphics_objects_count"):
                    if entry.get(field) is not None:
                        geom[field] = float(as_float(entry.get(field)))
    return geometry


def _extract_multi_column_pages(summary: Dict[str, Any]) -> List[int]:
    pages: List[int] = []
    candidates = summary.get("multi_column_pages") or summary.get("pages_multi_column")
    if not candidates:
        return pages
    if isinstance(candidates, (list, tuple, set)):
        for item in candidates:
            page = as_int(item)
            if page > 0 and page not in pages:
                pages.append(page)
    return pages


def _group_blocks_by_page(blocks: List[TextBlock]) -> Dict[int, List[Dict[str, Any]]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for block in blocks:
        page = int(block.get("page", 0))
        if page <= 0:
            continue
        grouped.setdefault(page, []).append(dict(block))
    return grouped


def _normalise_tool_log(tool_log: Iterable[Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for entry in tool_log or []:
        if isinstance(entry, dict):
            records.append(dict(entry))
    return records


def _compute_avg_ocr_conf(per_page_stats: List[Dict[str, Any]], has_ocr: bool, summary: Dict[str, Any]) -> float:
    if not has_ocr:
        return 0.0
    values: List[float] = []
    for stat in per_page_stats:
        source = str(stat.get("source") or "")
        if "ocr" in source:
            val = as_float(stat.get("ocr_conf"), default=None)
            if val is not None:
                values.append(float(val))
    if not values:
        avg_conf = as_float(summary.get("avg_conf"), default=None)
        return round(float(avg_conf), 2) if avg_conf is not None else 0.0
    return round(sum(values) / max(len(values), 1), 2)


def _detect_ocr_version(engine: str) -> str:
    if engine != "tesseract":
        return "none"
    try:
        import pytesseract

        return str(pytesseract.get_tesseract_version())
    except Exception:
        return "unknown"


def _safe_content_hash(input_path: Path) -> str:
    try:
        data = input_path.read_bytes()
    except Exception:
        return "0" * 64
    return hashlib.sha256(data).hexdigest()


def _resolve_preprocess(summary: Dict[str, Any], readers_result: Dict[str, Any]) -> List[str]:
    steps_raw = summary.get("preprocess_applied")
    if steps_raw is None:
        steps_raw = readers_result.get("preprocess_applied") or readers_result.get("preprocess")
    if steps_raw is None:
        return []
    if isinstance(steps_raw, str):
        return [steps_raw] if steps_raw else []
    if isinstance(steps_raw, (list, tuple, set)):
        return [str(step) for step in steps_raw if isinstance(step, str) and step]
    return []


def build_doc_meta(
    *,
    input_path: Path,
    detect_meta: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    readers_result: Dict[str, Any],
    timings: Dict[str, Any],
) -> DocMeta:
    readers_dir = Path(str(readers_result.get("outdir") or (input_path.parent / "readers")))
    summary_result = dict(readers_result.get("summary") or {})
    tool_log: List[Dict[str, Any]] = _normalise_tool_log(readers_result.get("tool_log") or [])

    summary_payload: Dict[str, Any] = {"summary": summary_result}
    if summary_result.get("qa") is not None:
        summary_payload["qa"] = summary_result.get("qa")
    if summary_result.get("flags") is not None:
        summary_payload["flags"] = summary_result.get("flags")

    summary_path = readers_dir / "readers_summary.json"
    if summary_path.exists():
        try:
            on_disk = json.loads(summary_path.read_text(encoding="utf-8"))
            disk_summary = dict(on_disk.get("summary") or {})
            merged_summary = {**summary_result, **disk_summary}
            summary_result = merged_summary
            summary_payload["summary"] = merged_summary
            if on_disk.get("qa") is not None:
                summary_payload["qa"] = on_disk.get("qa")
            if on_disk.get("flags") is not None:
                summary_payload["flags"] = on_disk.get("flags")
            disk_tool_log = _normalise_tool_log(on_disk.get("tool_log") or [])
            if disk_tool_log:
                if tool_log:
                    tool_log.extend(disk_tool_log)
                else:
                    tool_log = disk_tool_log
        except Exception:
            summary_payload["summary"] = summary_result
    else:
        summary_payload["summary"] = summary_result

    warnings = [str(item) for item in summary_result.get("warnings") or [] if str(item)]
    encoded = normalize_encoding(encoding_meta or {})

    fallback_langs = _fallback_lang_tokens(detect_meta.get("lang"), summary_result.get("lang_per_page"))
    detected_languages = build_detected_languages(summary_payload, fallback=fallback_langs)
    locale_hints = build_locale_hints(summary_payload)

    page_geometry = _extract_page_geometry(summary_result)
    text_blocks = build_text_blocks(readers_dir, page_geometry=page_geometry or None)
    blocks_by_page = _group_blocks_by_page(text_blocks)
    multi_column_pages = set(_extract_multi_column_pages(summary_result))

    per_page_stats = build_per_page_stats(
        summary_payload,
        page_geometry=page_geometry or None,
        lang_fallback=fallback_langs,
        multi_column_pages=multi_column_pages,
        blocks_by_page=blocks_by_page,
    )

    artifacts = load_artifacts(readers_dir)
    words = _load_words(readers_dir, page_geometry, blocks_by_page)
    zones = _load_zones(readers_dir)

    for artifact in artifacts:
        page = as_int(artifact.get("page"))
        page_info = page_geometry.get(page) or {}
        height = page_info.get("height")
        bbox = artifact.get("bbox")
        if height and isinstance(bbox, list) and len(bbox) == 4:
            artifact["bbox"] = to_bottom_left(bbox, float(height))

    for zone in zones:
        page = as_int(zone.get("page"))
        page_info = page_geometry.get(page) or {}
        height = page_info.get("height")
        bbox = zone.get("bbox")
        if height and isinstance(bbox, list) and len(bbox) == 4:
            zone["bbox"] = to_bottom_left(bbox, float(height))

    timings_payload = prepare_timings(timings or {}, summary_result.get("timings_ms") or {})

    page_decisions = [str(entry) for entry in summary_result.get("page_decisions") or []]
    has_ocr = any("ocr" in decision.lower() for decision in page_decisions)
    avg_ocr_conf = _compute_avg_ocr_conf(per_page_stats, has_ocr, summary_result)

    processing_log = _normalise_tool_log(tool_log)
    logs = summarise_logs(processing_log)
    mapped_file_type = _map_file_type(detect_meta.get("file_type"))
    coordinate_unit = "pdf_points"

    ocr_engine = "tesseract" if has_ocr else "none"
    ocr_engine_version = _detect_ocr_version(ocr_engine)
    ocr_langs = str(detect_meta.get("lang") or "+".join(fallback_langs) or _DEFAULT_OCR_LANGS)

    preprocess_applied = _resolve_preprocess(summary_result, readers_result)
    content_hash = _safe_content_hash(input_path)
    has_text_layer = bool(as_int(summary_result.get("text_blocks_count")))

    pages_count = as_int(summary_result.get("page_count"))
    if pages_count <= 0:
        pages_count = max(len(page_decisions), as_int(summary_result.get("pages_count")))

    doc_meta: DocMeta = {
        "file_name": input_path.name,
        "file_type": mapped_file_type,
        "pages_count": pages_count,
        "detected_encodings": encoded,
        "detected_languages": detected_languages,
        "has_ocr": has_ocr,
        "avg_ocr_conf": avg_ocr_conf,
        "coordinate_unit": coordinate_unit,
        "bbox_origin": "bottom-left",
        "pdf_locked": bool(summary_result.get("pdf_locked", False)),
        "ocr_engine": ocr_engine,
        "ocr_engine_version": ocr_engine_version,
        "ocr_langs": ocr_langs,
        "reader_version": READER_VERSION,
        "preprocess_applied": preprocess_applied,
        "content_hash": content_hash,
        "has_text_layer": has_text_layer,
        "timings_ms": timings_payload,
        "per_page_stats": per_page_stats,
        "text_blocks": text_blocks,
        "words": words,
        "zones": zones,
        "artifacts": artifacts,
        "locale_hints": locale_hints,
        "warnings": warnings,
        "logs": logs,
        "processing_log": processing_log,
        "visual_artifacts_path": str(readers_dir / "visual_artifacts.jsonl"),
        "text_blocks_path": str(readers_dir / "text_blocks.jsonl"),
    }

    return doc_meta
