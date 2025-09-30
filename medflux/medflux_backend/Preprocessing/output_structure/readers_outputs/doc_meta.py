from __future__ import annotations

import json
try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from .components import (
    build_detected_languages,
    build_locale_hints,
    build_qa,
    load_artifacts,
    load_tables_raw,
    normalize_encoding,
    prepare_timings,
    summarise_logs,
)
from .per_page_stats import build_per_page_stats
from .text_blocks import build_text_blocks
from .types import DocMeta

import hashlib


def _tokenise_langs(raw: str) -> List[str]:
    tokens: List[str] = []
    if not raw:
        return tokens
    for part in str(raw).replace(',', '+').split('+'):
        token = part.strip()
        if token:
            tokens.append(token)
    return tokens


def _collect_ocr_langs(tool_log: Iterable[Dict[str, Any]], fallback: str | None = None) -> str:
    seen: Set[str] = set()
    ordered: List[str] = []
    for event in tool_log or []:
        if not isinstance(event, dict):
            continue
        details = event.get('details') or {}
        if not isinstance(details, dict):
            continue
        lang_value = details.get('lang')
        if not lang_value:
            continue
        for token in _tokenise_langs(str(lang_value)):
            if token not in seen:
                seen.add(token)
                ordered.append(token)
    if not ordered and fallback:
        for token in _tokenise_langs(str(fallback)):
            if token not in seen:
                seen.add(token)
                ordered.append(token)
    return '+'.join(ordered) if ordered else ''


def _collect_preprocess_steps(tool_log: Iterable[Dict[str, Any]]) -> List[str]:
    seen: Set[str] = set()
    steps: List[str] = []
    for event in tool_log or []:
        if not isinstance(event, dict):
            continue
        details = event.get('details') or {}
        if not isinstance(details, dict):
            continue
        pre_value = details.get('pre')
        if not pre_value:
            continue
        for token in str(pre_value).replace(';', ',').split(','):
            step = token.strip()
            if step and step not in seen:
                seen.add(step)
                steps.append(step)
    return steps


def _resolve_ocr_engine(tool_log: Iterable[Dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    has_ocr_event = any(isinstance(event, dict) and event.get("step") == "ocr_runner" for event in tool_log or [])
    if not has_ocr_event:
        return None, None
    engine = 'tesseract'
    version: Optional[str] = None
    try:
        import pytesseract  # type: ignore

        getter = getattr(pytesseract, 'get_tesseract_version', None)
        if callable(getter):
            value = getter()
            version = str(value) if value is not None else None
    except Exception:
        version = None
    return engine, version


def _compute_content_hash(path: Path, chunk_size: int = 65536) -> Optional[str]:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except Exception:
        return None


def _infer_has_text_layer(per_page_stats: Iterable[Dict[str, Any]]) -> bool:
    for entry in per_page_stats or []:
        source = str(entry.get("source") or "").lower()
        decision = str(entry.get("decision") or "").lower()
        if source in {"text", "mixed"} or 'native' in decision:
            return True
    return False


def _infer_coordinate_unit(file_type: str) -> str:
    lowered = (file_type or "").lower()
    if lowered.startswith("pdf"):
        return "pdf_points"
    if lowered in {"image", "png", "jpg", "jpeg", "tiff", "tif"}:
        return "image_pixels"
    if lowered == "docx":
        return "docx_emus"
    return "unknown"



_ALLOWED_FILE_TYPES = {"pdf_text", "pdf_scan", "pdf_scan_hybrid", "docx", "image"}


def _normalise_file_type(raw: str) -> str:
    lowered = (raw or "").lower()
    if lowered in _ALLOWED_FILE_TYPES:
        return lowered
    if lowered.startswith("pdf"):
        if "hybrid" in lowered or "mixed" in lowered:
            return "pdf_scan_hybrid"
        if any(token in lowered for token in ("scan", "image", "ocr")):
            return "pdf_scan"
        return "pdf_text"
    if lowered in {"doc", "docm", "docx"}:
        return "docx"
    if lowered in {"txt", "text"}:
        return "docx"
    if lowered in {"png", "jpg", "jpeg", "tiff", "tif", "bmp"}:
        return "image"
    return "pdf_text"


def _extract_pdf_page_geometry(input_path: Path) -> Dict[int, Dict[str, float]]:
    if fitz is None:
        return {}
    try:
        doc = fitz.open(str(input_path))
    except Exception:  # pragma: no cover - optional dependency
        return {}
    geometries: Dict[int, Dict[str, float]] = {}
    try:
        for index, page in enumerate(doc, start=1):
            rect = getattr(page, 'rect', None)
            if rect is None:
                continue
            geometries[index] = {
                'width': float(rect.width),
                'height': float(rect.height),
                'rotation': float(getattr(page, 'rotation', 0) or 0),
            }
    finally:
        try:
            doc.close()
        except Exception:
            pass
    return geometries



def _group_blocks_by_page(blocks: Iterable[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for block in blocks or []:
        page = int(block.get('page') or 0)
        grouped.setdefault(page, []).append(block)
    return grouped



def _detect_multi_column(
    grouped: Dict[int, List[Dict[str, Any]]],
    page_geometry: Dict[int, Dict[str, float]],
) -> Set[int]:
    multi: Set[int] = set()
    for page, blocks in grouped.items():
        centers: List[float] = []
        for block in blocks:
            bbox = block.get('bbox') or []
            if isinstance(bbox, list) and len(bbox) >= 4:
                try:
                    x0 = float(bbox[0])
                    x1 = float(bbox[2])
                except Exception:
                    continue
                centers.append((x0 + x1) / 2.0)
        if len(centers) < 6:
            continue
        width = page_geometry.get(page, {}).get('width')
        if width and width > 0:
            norm = [max(0.0, min(center / width, 1.0)) for center in centers]
        else:
            min_c = min(centers)
            max_c = max(centers)
            span = max(max_c - min_c, 1.0)
            norm = [(center - min_c) / span for center in centers]
        left = [value for value in norm if value < 0.45]
        right = [value for value in norm if value > 0.55]
        if not left or not right:
            continue
        left_ratio = len(left) / len(norm)
        right_ratio = len(right) / len(norm)
        if left_ratio < 0.25 or right_ratio < 0.25:
            continue
        left_mean = sum(left) / len(left)
        right_mean = sum(right) / len(right)
        if abs(left_mean - right_mean) >= 0.15:
            multi.add(page)
    return multi





def _load_summary_payload(readers_dir: Path) -> Dict[str, Any]:
    summary_path = readers_dir / "readers_summary.json"
    if not summary_path.exists():
        return {"summary": {}}
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return {"summary": {}}


def build_doc_meta(
    input_path: Path,
    detect_meta: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    readers_result: Dict[str, Any],
    timings: Dict[str, Any],
    *,
    inline_blocks: bool = True,
    inline_tables: bool = True,
    inline_artifacts: bool = True,
) -> DocMeta:
    readers_dir = Path(readers_result.get("outdir") or readers_result.get("readers_outdir") or input_path.parent / "readers")
    summary_payload = _load_summary_payload(readers_dir)
    summary = summary_payload.get("summary", {}) or {}

    reader_version = str(
        readers_result.get("reader_version")
        or summary.get("reader_version")
        or summary_payload.get("reader_version")
        or readers_result.get("version")
        or "unknown"
    )

    summary_timings = summary.get("timings_ms") or {}
    timing_payload = prepare_timings(timings, summary_timings)

    if "table_detect_light" not in timing_payload:
        value = summary_timings.get("table_detect_light") if isinstance(summary_timings, dict) else None
        if value is not None:
            try:
                timing_payload["table_detect_light"] = round(float(value), 2)
            except Exception:
                timing_payload["table_detect_light"] = 0.0
        else:
            timing_payload["table_detect_light"] = 0.0

    raw_file_type = str(detect_meta.get("file_type") or "")
    file_type_lower = raw_file_type.lower()
    coordinate_unit = _infer_coordinate_unit(raw_file_type)
    page_geometry = _extract_pdf_page_geometry(input_path) if file_type_lower.startswith("pdf") else {}

    text_blocks = build_text_blocks(readers_dir, page_geometry=page_geometry) if inline_blocks else []
    blocks_by_page: Dict[int, List[Dict[str, Any]]] = _group_blocks_by_page(text_blocks)
    detected_langs = build_detected_languages(summary_payload, fallback=[detect_meta.get("lang") or ""])
    locale_hints = build_locale_hints(summary_payload)
    multi_column_pages = _detect_multi_column(blocks_by_page, page_geometry)
    per_page_stats = build_per_page_stats(
        summary_payload,
        page_geometry=page_geometry,
        lang_fallback=detected_langs.get("overall"),
        multi_column_pages=multi_column_pages,
        blocks_by_page=blocks_by_page,
    )

    pagewise_timings: List[Dict[str, float]] = []
    for stat in per_page_stats:
        if not isinstance(stat, dict):
            continue
        page_value = stat.get("page")
        if page_value is None:
            continue
        try:
            page_number = int(page_value)
        except Exception:
            continue
        time_value = stat.get("time_ms")
        if time_value is None:
            continue
        try:
            time_ms = round(float(time_value), 2)
        except Exception:
            time_ms = 0.0
        pagewise_timings.append({"page": page_number, "time_ms": time_ms})
    if pagewise_timings:
        timing_payload["pagewise"] = pagewise_timings
    else:
        timing_payload.setdefault("pagewise", [])

    warnings = list(summary.get("warnings") or [])
    qa_section = build_qa(summary_payload, warnings)

    tables_raw = load_tables_raw(readers_dir) if inline_tables else []
    artifacts = load_artifacts(readers_dir) if inline_artifacts else []

    tool_log = summary.get("tool_log") or []
    ocr_engine, ocr_engine_version = _resolve_ocr_engine(tool_log)
    ocr_langs = _collect_ocr_langs(tool_log, detect_meta.get("lang"))
    preprocess_steps = _collect_preprocess_steps(tool_log)
    dpi_value = detect_meta.get("dpi") if isinstance(detect_meta, dict) else None
    if isinstance(dpi_value, int) and dpi_value > 0:
        preprocess_steps.append(f"dpi_{dpi_value}")
    preprocess_steps = list(dict.fromkeys(step for step in preprocess_steps if step))
    content_hash_value = _compute_content_hash(input_path)
    content_hash = f"sha256:{content_hash_value}" if content_hash_value else ""
    has_text_layer = _infer_has_text_layer(per_page_stats)
    log_strings = summarise_logs(tool_log)

    has_ocr = any((stat.get("source") or "").lower() in {"ocr", "mixed"} for stat in per_page_stats)
    ocr_conf_values = [stat.get("ocr_conf") for stat in per_page_stats if isinstance(stat, dict) and stat.get("ocr_conf") is not None]
    avg_ocr_conf = round(sum(float(value) for value in ocr_conf_values) / len(ocr_conf_values), 2) if ocr_conf_values else 0.0

    ocr_engine_final = ocr_engine if ocr_engine is not None else ("tesseract" if has_ocr else "none")
    if ocr_engine_final == "none":
        ocr_engine_version = "none"
    elif not ocr_engine_version:
        ocr_engine_version = "unknown"
    else:
        ocr_engine_version = str(ocr_engine_version)

    preprocess_applied = list(preprocess_steps)
    ocr_langs = str(ocr_langs) if ocr_langs else ""

    detect_details = detect_meta.get("details") if isinstance(detect_meta, dict) else {}
    if not isinstance(detect_details, dict):
        detect_details = {}
    pdf_locked = bool(summary.get("pdf_locked") or detect_details.get("pdf_locked") or detect_details.get("locked") or detect_details.get("encrypted"))

    pages_count = int(summary.get("page_count") or detect_meta.get("pages_count") or readers_result.get("pages_count") or 0)
    normalised_file_type = _normalise_file_type(raw_file_type)

    by_page_langs = detected_langs.get("by_page")
    if not isinstance(by_page_langs, list):
        by_page_langs = []
    doc_lang_default = detected_langs.get("doc") or (detected_langs.get("overall") or ["de"])[0]
    if pages_count > 0:
        if not by_page_langs:
            by_page_langs = [doc_lang_default] * pages_count
        elif len(by_page_langs) < pages_count:
            last_lang = by_page_langs[-1] if by_page_langs else doc_lang_default
            by_page_langs.extend([last_lang] * (pages_count - len(by_page_langs)))
        elif len(by_page_langs) > pages_count:
            by_page_langs = by_page_langs[:pages_count]
        detected_langs["by_page"] = by_page_langs

    for key in ("readers", "ocr", "lang_detect", "table_detect_light"):
        timing_payload.setdefault(key, 0.0)

    doc_meta: DocMeta = {
        "file_name": input_path.name,
        "file_type": normalised_file_type,
        "pages_count": pages_count,
        "detected_encodings": normalize_encoding(encoding_meta),
        "detected_languages": detected_langs,
        "has_ocr": has_ocr,
        "avg_ocr_conf": avg_ocr_conf,
        "coordinate_unit": coordinate_unit,
        "bbox_origin": "top-left",
        "pdf_locked": pdf_locked,
        "ocr_engine": ocr_engine_final,
        "ocr_engine_version": ocr_engine_version,
        "ocr_langs": ocr_langs,
        "reader_version": reader_version,
        "preprocess_applied": preprocess_applied,
        "content_hash": content_hash,
        "has_text_layer": has_text_layer,
        "timings_ms": timing_payload,
        "per_page_stats": per_page_stats,
        "text_blocks": text_blocks,
        "tables_raw": tables_raw,
        "artifacts": artifacts,
        "locale_hints": locale_hints,
        "qa": qa_section,
        "warnings": warnings,
        "logs": log_strings,
        "processing_log": tool_log,
        "visual_artifacts_path": str(readers_dir / "visual_artifacts.jsonl"),
        "text_blocks_path": str(readers_dir / "text_blocks.jsonl"),
        "tables_raw_path": str(readers_dir / "tables_raw.jsonl"),
    }
    return doc_meta










