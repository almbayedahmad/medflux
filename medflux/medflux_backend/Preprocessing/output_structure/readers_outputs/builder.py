from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .components import (
    build_detected_languages,
    build_locale_hints,
    build_qa,
    collect_per_page_stats,
    load_artifacts,
    load_tables_raw,
    load_text_blocks,
    normalize_encoding,
    prepare_timings,
    summarise_logs,
)
from .types import DocMetaPayload


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
) -> DocMetaPayload:
    readers_dir = Path(readers_result.get("outdir") or readers_result.get("readers_outdir") or input_path.parent / "readers")
    summary_payload = _load_summary_payload(readers_dir)
    summary = summary_payload.get("summary", {}) or {}

    summary_timings = summary.get("timings_ms") or {}
    timing_payload = prepare_timings(timings, summary_timings)

    per_page_stats = collect_per_page_stats(summary_payload)
    detected_langs = build_detected_languages(summary_payload, fallback=[detect_meta.get("lang") or ""])
    locale_hints = build_locale_hints(summary_payload)

    warnings = list(summary.get("warnings") or [])
    qa_section = build_qa(summary_payload, warnings)

    text_blocks = load_text_blocks(readers_dir) if inline_blocks else []
    tables_raw = load_tables_raw(readers_dir) if inline_tables else []
    artifacts = load_artifacts(readers_dir) if inline_artifacts else []

    tool_log = summary.get("tool_log") or []
    log_strings = summarise_logs(tool_log)

    has_ocr = any("ocr" in (stat["source"].lower() if stat.get("source") else "") for stat in per_page_stats)
    ocr_conf_values = [stat.get("ocr_conf_avg") for stat in per_page_stats if isinstance(stat, dict) and stat.get("ocr_conf_avg") is not None]
    avg_ocr_conf = round(sum(float(value) for value in ocr_conf_values) / len(ocr_conf_values), 2) if ocr_conf_values else 0.0

    doc_meta: DocMetaPayload = {
        "file_name": input_path.name,
        "file_type": detect_meta.get("file_type") or "unknown",
        "pages_count": int(summary.get("page_count") or detect_meta.get("pages_count") or readers_result.get("pages_count") or 0),
        "detected_encodings": normalize_encoding(encoding_meta),
        "detected_languages": detected_langs,
        "has_ocr": has_ocr,
        "avg_ocr_conf": avg_ocr_conf,
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
