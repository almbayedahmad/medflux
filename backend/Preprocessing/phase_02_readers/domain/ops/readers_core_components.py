# PURPOSE:
#   Component-level helpers and transformations for readers.
#
# OUTCOME:
#   Provides reusable building blocks used by the orchestrator and meta/stats
#   modules to construct structured outputs.
#
# INPUTS:
#   - Intermediate structures (blocks, tables, page records), numeric/text data.
#
# OUTPUTS:
#   - Pure-Python transformed values appended to readers data structures.
#
# DEPENDENCIES:
#   - Local readers schemas and ops; standard library only.
from __future__ import annotations

"""Core business logic for component processing in the readers stage."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.preprocessing.cross_phase.helpers.main_pre_helpers_lang import collapse_doc_lang, normalise_lang
from core.preprocessing.cross_phase.helpers.main_pre_helpers_num import as_float

from ...schemas.readers_schema_types import (
    Artifact,
    DetectedLanguages,
    LocaleHints,
    QASection,
    RawTable,
    TimingBreakdown,
)

_TIMING_KEYS = {
    "detect",
    "encoding",
    "readers",
    "text_extract",
    "ocr",
    "table_detect",
    "table_detect_light",
    "table_extract",
    "lang_detect",
    "cleaning",
    "merge",
    "summarize",
}

_ALLOWED_LANGS = ("de", "en")
_DEFAULT_LANG = "de"


def compute_readers_flatten_lang_values(value: Any) -> List[str]:
    """Flatten language values from various input formats."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        flattened: List[str] = []
        for item in value:
            flattened.extend(compute_readers_flatten_lang_values(item))
        return flattened
    text_value = str(value)
    if not text_value:
        return []
    parts = []
    for part in text_value.replace(",", "+").split("+"):
        stripped = part.strip()
        if stripped:
            parts.append(stripped)
    return parts


def compute_readers_collect_lang_tokens(raw_values: Iterable[Any] | None) -> List[str]:
    """Collect and normalize language tokens from raw values."""
    tokens: List[str] = []
    for raw in raw_values or []:
        for part in compute_readers_flatten_lang_values(raw):
            mapped = normalise_lang(part)
            if mapped in _ALLOWED_LANGS:
                if mapped not in tokens:
                    tokens.append(mapped)
            elif mapped == "mixed":
                for alias in _ALLOWED_LANGS:
                    if alias not in tokens:
                        tokens.append(alias)
    return tokens


def compute_readers_collapse_lang_tokens(tokens: Iterable[str]) -> str:
    """Collapse language tokens into a single language identifier."""
    token_list = [token for token in tokens if token in _ALLOWED_LANGS]
    if not token_list:
        return _DEFAULT_LANG
    share = {lang: (1.0 if lang in token_list else 0.0) for lang in _ALLOWED_LANGS}
    collapsed = collapse_doc_lang(share)
    return collapsed or _DEFAULT_LANG


def get_readers_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of dictionaries."""
    if not path.exists():
        return []
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def compute_readers_prepare_timings(cli_timings: Dict[str, Any], summary_timings: Dict[str, Any]) -> TimingBreakdown:
    """Prepare timing breakdown from CLI and summary timing data."""
    payload: TimingBreakdown = {}

    total = as_float(summary_timings.get("total_ms"), default=None)
    if total is None:
        total = as_float(cli_timings.get("total_ms"), default=None)
    if total is not None:
        payload["total_ms"] = round(total, 2)

    for key in _TIMING_KEYS:
        value = as_float(cli_timings.get(key), default=None)
        if value is not None and value >= 0:
            payload[key] = round(value, 2)

    for key, value in (summary_timings or {}).items():
        if key == "total_ms":
            continue
        if key not in _TIMING_KEYS:
            continue
        val = as_float(value, default=None)
        if val is not None and val >= 0:
            payload[key] = round(val, 2)

    pagewise_entries: List[Dict[str, Any]] = []
    raw_pagewise = summary_timings.get("pagewise") or cli_timings.get("pagewise")
    if isinstance(raw_pagewise, list):
        for entry in raw_pagewise:
            if not isinstance(entry, dict):
                continue
            page = entry.get("page")
            time_value = as_float(entry.get("time_ms"), default=None)
            if page is None or time_value is None:
                continue
            try:
                page_number = int(page)
            except Exception:
                continue
            pagewise_entries.append({"page": page_number, "time_ms": round(time_value, 2)})
    if pagewise_entries:
        payload["pagewise"] = pagewise_entries
    else:
        payload["pagewise"] = []

    for key in ("readers", "ocr", "lang_detect", "table_detect_light"):
        payload.setdefault(key, 0.0)

    return payload


def normalize_readers_encoding(encoding_meta: Dict[str, Any]) -> str | None:
    """Normalize encoding metadata to standard format."""
    primary = encoding_meta.get("primary")
    if isinstance(primary, str) and primary.strip():
        return primary.strip().lower()
    if encoding_meta.get("is_utf8"):
        return "utf-8"
    return None


def compute_readers_detected_languages(summary_payload: Dict[str, Any], fallback: Iterable[str] | None = None) -> DetectedLanguages:
    """Compute detected languages from summary payload."""
    summary = summary_payload.get("summary", {}) or {}
    detected = summary.get("detected_languages")
    if isinstance(detected, dict) and detected:
        overall = list(detected.get("overall") or [])
        by_page = list(detected.get("by_page") or [])
        doc_lang = str(detected.get("doc") or "")
        conf_doc = detected.get("conf_doc")
        try:
            conf_value = float(conf_doc) if conf_doc is not None else None
        except Exception:
            conf_value = None
        if not overall:
            overall = [_DEFAULT_LANG]
        if not by_page and overall:
            by_page = overall[:]
        if not doc_lang and overall:
            doc_lang = compute_readers_collapse_lang_tokens(overall)
        return {
            "overall": overall,
            "by_page": by_page,
            "doc": doc_lang,
            "conf_doc": round(conf_value, 2) if conf_value is not None else 0.0,
        }

    lang_per_page = summary.get("lang_per_page") or []

    fallback_tokens = compute_readers_collect_lang_tokens(fallback) or [_DEFAULT_LANG]

    page_langs: Dict[int, str] = {}
    for entry in lang_per_page:
        if not isinstance(entry, dict):
            continue
        page_raw = entry.get("page")
        try:
            page_number = int(page_raw)
        except Exception:
            continue
        if page_number <= 0:
            continue
        tokens = compute_readers_collect_lang_tokens([entry.get("lang"), entry.get("languages")])
        if not tokens:
            tokens = fallback_tokens
        page_langs[page_number] = compute_readers_collapse_lang_tokens(tokens)

    try:
        page_count = int(summary.get("page_count") or 0)
    except Exception:
        page_count = 0

    default_page_lang = compute_readers_collapse_lang_tokens(fallback_tokens)
    if page_count > 0:
        by_page = [page_langs.get(page, default_page_lang) for page in range(1, page_count + 1)]
    else:
        ordered_pages = sorted(page_langs)
        by_page = [page_langs[page] for page in ordered_pages]

    overall_tokens = compute_readers_collect_lang_tokens(by_page)
    if not overall_tokens:
        overall_tokens = fallback_tokens

    overall: List[str] = []
    for candidate in _ALLOWED_LANGS:
        if candidate in overall_tokens and candidate not in overall:
            overall.append(candidate)
    if not overall:
        overall = [_DEFAULT_LANG]

    doc_lang = compute_readers_collapse_lang_tokens(overall_tokens)
    conf_doc = as_float(summary.get("avg_conf"), default=None)
    if conf_doc is None:
        conf_doc = as_float(summary.get("lang_conf"), default=None)
    conf_doc_value = round(conf_doc, 2) if conf_doc is not None else 0.0

    payload: DetectedLanguages = {
        "overall": overall,
        "by_page": by_page,
        "doc": doc_lang,
        "conf_doc": conf_doc_value,
    }
    return payload


def compute_readers_locale_hints(summary_payload: Dict[str, Any]) -> LocaleHints:
    """Compute locale hints from summary payload."""
    summary = summary_payload.get("summary", {}) or {}
    locale_per_page = summary.get("locale_per_page") or []
    per_page: List[Dict[str, Any]] = []
    overall_candidates: List[str] = []
    for entry in locale_per_page:
        page = int(entry.get("page") or 0)
        locale = str(entry.get("locale") or "unknown")
        per_page.append({"page": page, "locale": locale})
        if locale and locale not in {"unknown", "mixed"}:
            overall_candidates.append(locale)
    overall = overall_candidates[0] if overall_candidates else (summary.get("locale") or "unknown")
    return {
        "overall": overall or "unknown",
        "by_page": per_page,
        "numbers_locale": overall or "unknown",
        "dates_locale": overall or "unknown",
    }


def get_readers_tables_raw(readers_dir: Path) -> List[RawTable]:
    """Load raw table data from JSONL file."""
    items = get_readers_jsonl_rows(readers_dir / "tables_raw.jsonl")
    tables: List[RawTable] = []
    for item in items:
        table: RawTable = {
            "id": str(item.get("id") or ""),
            "page": int(item.get("page") or 0),
            "extraction_tool": str(item.get("extraction_tool") or ""),
            "status": str(item.get("status") or ""),
        }
        bbox = item.get("bbox")
        if isinstance(bbox, list):
            table["bbox"] = [float(x) for x in bbox]
        if item.get("cells"):
            cells_payload = []
            for cell in item.get("cells") or []:
                cell_entry = {
                    "row": int(cell.get("row") or 0),
                    "col": int(cell.get("col") or 0),
                    "text": str(cell.get("text") or ""),
                }
                if cell.get("bbox"):
                    cell_entry["bbox"] = [float(x) for x in cell.get("bbox")]
                if cell.get("row_span") is not None:
                    cell_entry["row_span"] = int(cell.get("row_span") or 1)
                if cell.get("col_span") is not None:
                    cell_entry["col_span"] = int(cell.get("col_span") or 1)
                cells_payload.append(cell_entry)
            table["cells"] = cells_payload
        if item.get("table_text"):
            table["table_text"] = str(item.get("table_text"))
        tables.append(table)
    return tables


def get_readers_artifacts(readers_dir: Path) -> List[Artifact]:
    """Load visual artifacts from JSONL file."""
    items = get_readers_jsonl_rows(readers_dir / "visual_artifacts.jsonl")
    artifacts: List[Artifact] = []
    for item in items:
        bbox = item.get("bbox") or []
        artifact: Artifact = {
            "page": int(item.get("page") or 0),
            "bbox": [float(x) for x in bbox] if isinstance(bbox, list) else [],
            "kind": str(item.get("kind") or "unknown"),
            "confidence": float(item.get("confidence") or 0.0),
            "source": str(item.get("source") or ""),
        }
        artifacts.append(artifact)
    return artifacts


def summarize_readers_logs(tool_log: List[Dict[str, Any]]) -> List[str]:
    """Summarize tool log entries into human-readable strings."""
    summaries: List[str] = []
    for event in tool_log:
        step = str(event.get("step") or "")
        status = str(event.get("status") or "")
        page = event.get("page")
        details = event.get("details") or {}
        suffix = ""
        if isinstance(details, dict) and details:
            summary_parts = [f"{key}={value}" for key, value in sorted(details.items())]
            suffix = " " + ", ".join(summary_parts)
        if page is not None:
            summaries.append(f"{step} {status} p={page}{suffix}")
        else:
            summaries.append(f"{step} {status}{suffix}")
    return summaries


def compute_readers_qa_section(summary_payload: Dict[str, Any], warnings: List[str]) -> QASection:
    """Compute QA section from summary payload and warnings."""
    qa_data = summary_payload.get("qa") or {}
    flags = summary_payload.get("flags") or {}
    low_conf = list(qa_data.get("low_conf_pages") or [])
    low_text = list(qa_data.get("low_text_pages") or [])
    tables_fail = bool(qa_data.get("tables_fail"))
    reasons = list(qa_data.get("reasons") or [])
    flagged_pages = set(low_conf) | set(flags.get("pages") or [])
    needs_review = bool(qa_data.get("needs_review")) or bool(flags.get("manual_review")) or bool(warnings) or tables_fail
    summary_parts: List[str] = []
    if low_conf:
        summary_parts.append(f"low_conf_page={','.join(str(p) for p in low_conf)}")
    if low_text:
        summary_parts.append(f"low_text_page={','.join(str(p) for p in low_text)}")
    if tables_fail:
        summary_parts.append("table_extract_error")
    qa_section: QASection = {
        "needs_review": needs_review,
        "pages": sorted(flagged_pages),
        "warnings": warnings,
        "low_conf_pages": low_conf,
        "low_text_pages": low_text,
        "tables_fail": tables_fail,
        "reasons": reasons,
    }
    if summary_parts:
        qa_section["summary"] = "; ".join(summary_parts)
    return qa_section


# Backwards-compatible aliases
prepare_timings = compute_readers_prepare_timings
normalize_encoding = normalize_readers_encoding
build_detected_languages = compute_readers_detected_languages
build_locale_hints = compute_readers_locale_hints
load_tables_raw = get_readers_tables_raw
load_artifacts = get_readers_artifacts
summarise_logs = summarize_readers_logs
build_qa = compute_readers_qa_section


__all__ = [
    "compute_readers_flatten_lang_values",
    "compute_readers_collect_lang_tokens",
    "compute_readers_collapse_lang_tokens",
    "get_readers_jsonl_rows",
    "compute_readers_prepare_timings",
    "normalize_readers_encoding",
    "compute_readers_detected_languages",
    "compute_readers_locale_hints",
    "get_readers_tables_raw",
    "get_readers_artifacts",
    "summarize_readers_logs",
    "compute_readers_qa_section",
    # Backwards-compatible aliases
    "prepare_timings",
    "normalize_encoding",
    "build_detected_languages",
    "build_locale_hints",
    "load_tables_raw",
    "load_artifacts",
    "summarise_logs",
    "build_qa",
]
