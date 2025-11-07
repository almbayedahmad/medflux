from __future__ import annotations

"""Core business logic for document metadata computation in the readers stage."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.preprocessing.cross_phase.helpers.main_pre_helpers_geom import to_bottom_left
from core.preprocessing.cross_phase.helpers.main_pre_helpers_lang import normalise_lang
from core.preprocessing.cross_phase.helpers.main_pre_helpers_num import as_float, as_int

from ..schemas.readers_schema_types import (
    Artifact,
    DocMeta,
    ReadersOutput,
    TextBlock,
    WordEntry,
    ZoneEntry,
)
from ..schemas.readers_schema_output import SCHEMA_VERSION

READER_VERSION = "unified-readers-v1"
_DEFAULT_OCR_LANGS = "deu+eng"


def compute_readers_file_type(raw: Any) -> str:
    """Compute standardized file type from raw detection result."""
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


def compute_readers_coordinate_unit(file_type: str) -> str:
    """Determine coordinate unit based on file type."""
    if file_type.startswith("pdf"):
        return "pdf_points"
    if file_type == "docx":
        return "docx_emus"
    if file_type == "image":
        return "image_pixels"
    return "unknown"


def compute_readers_fallback_lang_tokens(*values: Any) -> List[str]:
    """Extract and normalize language tokens from various input sources."""
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
            if token == "unknown":
                continue
            if token not in {"de", "en", "mixed", "de+en"}:
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


def compute_readers_float_list(value: Any) -> List[float]:
    """Convert any value to list of floats."""
    if not isinstance(value, list):
        return []
    floats: List[float] = []
    for item in value:
        try:
            floats.append(float(item))
        except Exception:
            continue
    return floats


def get_readers_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of dictionaries."""
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


def get_readers_word_entries(
    readers_dir: Path,
    page_geometry: Dict[int, Dict[str, float]],
    blocks_lookup: Dict[int, List[Dict[str, Any]]],
) -> List[WordEntry]:
    """Load and process word entries from JSONL file."""
    words_path = readers_dir / "words.jsonl"
    entries = get_readers_jsonl_rows(words_path)
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
        bbox_raw = compute_readers_float_list(item.get("bbox"))
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


def get_readers_zone_entries(readers_dir: Path) -> List[ZoneEntry]:
    """Load zone entries from JSONL file."""
    zones_path = readers_dir / "zones.jsonl"
    entries = get_readers_jsonl_rows(zones_path)
    zones: List[ZoneEntry] = []
    for item in entries:
        zone: ZoneEntry = {
            "page": as_int(item.get("page")),
            "bbox": compute_readers_float_list(item.get("bbox")),
            "type": str(item.get("type") or ""),
        }
        zones.append(zone)
    return zones


def compute_readers_fallback_per_page_stats(
    summary: Dict[str, Any],
    page_geometry: Dict[int, Dict[str, float]],
    fallback_langs: List[str],
) -> List[Dict[str, Any]]:
    """Generate fallback per-page statistics when detailed stats are unavailable."""
    fallback_lang = fallback_langs[0] if fallback_langs else "de"
    decisions = [str(decision or "text") for decision in summary.get("page_decisions") or []]
    pages = as_int(summary.get("page_count")) or len(decisions) or 1
    fallback_stats: List[Dict[str, Any]] = []
    for index in range(1, pages + 1):
        decision = decisions[index - 1] if index - 1 < len(decisions) else "text"
        decision_lower = decision.lower()
        if "ocr" in decision_lower and "native" in decision_lower:
            source = "mixed"
        elif "ocr" in decision_lower:
            source = "ocr"
        else:
            source = "text"
        geometry = page_geometry.get(index) or {}
        page_size = {
            "width": float(geometry.get("width") or 0.0),
            "height": float(geometry.get("height") or 0.0),
        }
        fallback_stats.append({
            "page": index,
            "source": source,
            "chars": 0,
            "lang": fallback_lang,
            "lang_share": {fallback_lang: 1.0},
            "ocr_conf": 0.0,
            "ocr_words": 0,
            "tables_found": 0,
            "table_cells": 0,
            "flags": [],
            "rotation_deg": int(float(geometry.get("rotation") or 0.0)),
            "skew_deg": 0.0,
            "is_multi_column": False,
            "columns_count": 1,
            "page_size": page_size,
            "noise_score": 0.0,
            "text_density": 0.0,
            "has_header_footer": False,
            "has_images": bool(geometry.get("images_count")),
            "images_count": int(geometry.get("images_count") or 0),
            "graphics_objects_count": int(geometry.get("graphics_objects_count") or 0),
            "time_ms": 0.0,
            "locale": fallback_lang,
            "decision": decision,
            "has_table": False,
        })
    return fallback_stats


def get_readers_table_candidates(readers_dir: Path, page_geometry: Dict[int, Dict[str, float]]) -> List[Dict[str, Any]]:
    """Load table candidates from JSONL file."""
    path = readers_dir / "table_candidates.jsonl"
    entries = get_readers_jsonl_rows(path)
    candidates: List[Dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        candidate = dict(item)
        page = as_int(candidate.get("page"))
        geometry = page_geometry.get(page) if page_geometry else None
        height = float(geometry.get("height")) if geometry and geometry.get("height") is not None else None
        bbox = candidate.get("bbox")
        if height and isinstance(bbox, list) and len(bbox) == 4:
            candidate["bbox"] = to_bottom_left(bbox, height)
        candidates.append(candidate)
    return candidates


def compute_readers_page_geometry(summary: Dict[str, Any]) -> Dict[int, Dict[str, float]]:
    """Extract page geometry information from summary data."""
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


def compute_readers_multi_column_pages(summary: Dict[str, Any]) -> List[int]:
    """Extract multi-column page numbers from summary data."""
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


def compute_readers_blocks_by_page(blocks: List[TextBlock]) -> Dict[int, List[Dict[str, Any]]]:
    """Group text blocks by page number."""
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for block in blocks:
        page = int(block.get("page", 0))
        if page <= 0:
            continue
        grouped.setdefault(page, []).append(dict(block))
    return grouped


def normalize_readers_tool_log(tool_log: Iterable[Any]) -> List[Dict[str, Any]]:
    """Normalize tool log entries to list of dictionaries."""
    records: List[Dict[str, Any]] = []
    for entry in tool_log or []:
        if isinstance(entry, dict):
            records.append(dict(entry))
    return records


def compute_readers_avg_ocr_conf(per_page_stats: List[Dict[str, Any]], has_ocr: bool, summary: Dict[str, Any]) -> float:
    """Compute average OCR confidence from per-page statistics."""
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


def compute_readers_ocr_version(engine: str) -> str:
    """Detect OCR engine version."""
    if engine != "tesseract":
        return "none"
    try:
        import pytesseract
        return str(pytesseract.get_tesseract_version())
    except Exception:
        return "unknown"


def compute_readers_content_hash(input_path: Path) -> str:
    """Compute SHA256 hash of input file."""
    try:
        data = input_path.read_bytes()
    except Exception:
        return "0" * 64
    return hashlib.sha256(data).hexdigest()


def compute_readers_preprocess_steps(summary: Dict[str, Any], readers_result: Dict[str, Any]) -> List[str]:
    """Extract preprocessing steps from summary or result data."""
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


def compute_readers_doc_meta_payload(
    *,
    input_path: Path,
    detect_meta: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    readers_result: Dict[str, Any],
    timings: Dict[str, Any],
    run_id: str,
    pipeline_id: str = "preprocessing.readers",
) -> ReadersOutput:
    """Main orchestrator function to build complete document metadata payload."""
    # Import here to avoid circular imports
    from ..core_functions.readers_core_components import (
        compute_readers_detected_languages,
        compute_readers_locale_hints,
        get_readers_artifacts,
        normalize_readers_encoding,
        compute_readers_prepare_timings,
        summarize_readers_logs,
    )
    from ..core_functions.readers_core_stats import compute_readers_per_page_stats
    from ..core_functions.readers_core_text_blocks import compute_readers_text_blocks

    readers_dir = Path(str(readers_result.get("outdir") or (input_path.parent / "readers")))
    has_processed_pages = (readers_dir / "unified_text.jsonl").exists()
    summary_result = dict(readers_result.get("summary") or {})
    tool_log: List[Dict[str, Any]] = normalize_readers_tool_log(readers_result.get("tool_log") or [])

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
            disk_tool_log = normalize_readers_tool_log(on_disk.get("tool_log") or [])
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
    encoded = normalize_readers_encoding(encoding_meta or {})

    fallback_langs = compute_readers_fallback_lang_tokens(detect_meta.get("lang"), summary_result.get("lang_per_page"))
    detected_languages = compute_readers_detected_languages(summary_payload, fallback=fallback_langs)
    locale_hints = compute_readers_locale_hints(summary_payload)

    page_geometry = compute_readers_page_geometry(summary_result)
    text_blocks = compute_readers_text_blocks(readers_dir, page_geometry=page_geometry or None)
    blocks_by_page = compute_readers_blocks_by_page(text_blocks)
    multi_column_pages = set(compute_readers_multi_column_pages(summary_result))

    artifacts = get_readers_artifacts(readers_dir)
    words = get_readers_word_entries(readers_dir, page_geometry, blocks_by_page)
    zones = get_readers_zone_entries(readers_dir)

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

    zones_by_page: Dict[int, List[str]] = {}
    for zone in zones:
        page_idx = as_int(zone.get("page"))
        zone_type = str(zone.get("type") or "").lower()
        if page_idx > 0 and zone_type:
            zones_by_page.setdefault(page_idx, []).append(zone_type)
    per_page_stats = compute_readers_per_page_stats(
        summary_payload,
        page_geometry=page_geometry or None,
        lang_fallback=fallback_langs,
        multi_column_pages=multi_column_pages,
        blocks_by_page=blocks_by_page,
        zones_by_page=zones_by_page,
    )
    if not per_page_stats and has_processed_pages:
        per_page_stats = compute_readers_fallback_per_page_stats(summary_result, page_geometry or {}, fallback_langs)

    table_candidates = get_readers_table_candidates(readers_dir, page_geometry or {})

    timings_payload = compute_readers_prepare_timings(timings or {}, summary_result.get("timings_ms") or {})

    page_decisions = [str(entry) for entry in summary_result.get("page_decisions") or []]
    has_ocr = any("ocr" in decision.lower() for decision in page_decisions)
    avg_ocr_conf = compute_readers_avg_ocr_conf(per_page_stats, has_ocr, summary_result)

    processing_log = normalize_readers_tool_log(tool_log)
    logs = summarize_readers_logs(processing_log)
    structured_logs = get_readers_jsonl_rows(readers_dir / "structured_logs.jsonl")
    mapped_file_type = compute_readers_file_type(detect_meta.get("file_type"))
    coordinate_unit = "pdf_points"

    ocr_engine = "tesseract" if has_ocr else "none"
    ocr_engine_version = compute_readers_ocr_version(ocr_engine)
    ocr_langs = str(detect_meta.get("lang") or "+".join(fallback_langs) or _DEFAULT_OCR_LANGS)

    preprocess_applied = compute_readers_preprocess_steps(summary_result, readers_result)
    content_hash = compute_readers_content_hash(input_path)
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
        "words": words,
        "artifacts": artifacts,
        "locale_hints": locale_hints,
        "warnings": warnings,
        "logs": logs,
        "processing_log": processing_log,
        "visual_artifacts_path": str(readers_dir / "visual_artifacts.jsonl"),
        "text_blocks_path": str(readers_dir / "text_blocks.jsonl"),
    }

    readers_payload: ReadersOutput = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "pipeline_id": pipeline_id,
        "doc_meta": doc_meta,
        "per_page_stats": per_page_stats,
        "text_blocks": text_blocks,
        "warnings": warnings,
        "logs": logs,
    }
    if table_candidates:
        readers_payload["table_candidates"] = table_candidates
    if zones:
        readers_payload["zones"] = zones
    if structured_logs:
        readers_payload["logs_structured"] = structured_logs
    return readers_payload


def _bbox_equal(bbox1: List[float], bbox2: List[float], tolerance: float = 1e-6) -> bool:
    """Check if two bounding boxes are equal within tolerance."""
    if len(bbox1) != 4 or len(bbox2) != 4:
        return False
    return all(abs(a - b) < tolerance for a, b in zip(bbox1, bbox2))


# Backwards-compatible aliases
map_file_type = compute_readers_file_type
coordinate_unit = compute_readers_coordinate_unit
fallback_lang_tokens = compute_readers_fallback_lang_tokens
float_list = compute_readers_float_list
load_jsonl = get_readers_jsonl_rows
load_words = get_readers_word_entries
load_zones = get_readers_zone_entries
fallback_per_page_stats = compute_readers_fallback_per_page_stats
load_table_candidates = get_readers_table_candidates
extract_page_geometry = compute_readers_page_geometry
extract_multi_column_pages = compute_readers_multi_column_pages
group_blocks_by_page = compute_readers_blocks_by_page
normalise_tool_log = normalize_readers_tool_log
compute_avg_ocr_conf = compute_readers_avg_ocr_conf
detect_ocr_version = compute_readers_ocr_version
safe_content_hash = compute_readers_content_hash
resolve_preprocess = compute_readers_preprocess_steps
build_doc_meta = compute_readers_doc_meta_payload


__all__ = [
    "compute_readers_file_type",
    "compute_readers_coordinate_unit",
    "compute_readers_fallback_lang_tokens",
    "compute_readers_float_list",
    "get_readers_jsonl_rows",
    "get_readers_word_entries",
    "get_readers_zone_entries",
    "compute_readers_fallback_per_page_stats",
    "get_readers_table_candidates",
    "compute_readers_page_geometry",
    "compute_readers_multi_column_pages",
    "compute_readers_blocks_by_page",
    "normalize_readers_tool_log",
    "compute_readers_avg_ocr_conf",
    "compute_readers_ocr_version",
    "compute_readers_content_hash",
    "compute_readers_preprocess_steps",
    "compute_readers_doc_meta_payload",
    # Backwards-compatible aliases
    "map_file_type",
    "coordinate_unit",
    "fallback_lang_tokens",
    "float_list",
    "load_jsonl",
    "load_words",
    "load_zones",
    "fallback_per_page_stats",
    "load_table_candidates",
    "extract_page_geometry",
    "extract_multi_column_pages",
    "group_blocks_by_page",
    "normalise_tool_log",
    "compute_avg_ocr_conf",
    "detect_ocr_version",
    "safe_content_hash",
    "resolve_preprocess",
    "build_doc_meta",
]
