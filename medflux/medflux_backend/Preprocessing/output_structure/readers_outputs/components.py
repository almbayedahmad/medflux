from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .types import (
    Artifact,
    DetectedLanguages,
    LocaleHints,
    PerPageStat,
    QASection,
    RawTable,
    TextBlock,
    TimingBreakdown,
)

_TIMING_KEYS = {
    "detect",
    "encoding",
    "readers",
    "text_extract",
    "ocr",
    "table_detect",
    "table_extract",
    "lang_detect",
    "cleaning",
    "merge",
    "summarize",
}


_LANG_ALIAS = {
    "deu": "de",
    "ger": "de",
    "german": "de",
    "de": "de",
    "eng": "en",
    "english": "en",
    "en": "en",
}


def _normalize_lang_token(token: str) -> str:
    cleaned = (token or "").strip().lower()
    if not cleaned:
        return ""
    return _LANG_ALIAS.get(cleaned, cleaned)


def _safe_float(value: Any) -> float | None:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str) and value.strip():
            return float(value)
    except Exception:
        return None
    return None


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
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


def prepare_timings(cli_timings: Dict[str, Any], summary_timings: Dict[str, Any]) -> TimingBreakdown:
    payload: TimingBreakdown = {}
    total = _safe_float(summary_timings.get("total_ms")) or _safe_float(cli_timings.get("total_ms"))
    if total is not None:
        payload["total_ms"] = round(total, 2)
    for key in _TIMING_KEYS:
        value = _safe_float(cli_timings.get(key))
        if value is not None and value > 0:
            payload[key] = round(value, 2)
    for key, value in summary_timings.items():
        if key == "total_ms":
            continue
        if key not in _TIMING_KEYS:
            continue
        val = _safe_float(value)
        if val is not None and val >= 0:
            payload[key] = round(val, 2)
    return payload


def normalize_encoding(encoding_meta: Dict[str, Any]) -> str | None:
    primary = encoding_meta.get("primary")
    if isinstance(primary, str) and primary.strip():
        return primary.strip().lower()
    if encoding_meta.get("is_utf8"):
        return "utf-8"
    return None


def build_detected_languages(summary_payload: Dict[str, Any], fallback: Iterable[str] | None = None) -> DetectedLanguages:
    summary = summary_payload.get("summary", {}) or {}
    lang_per_page = summary.get("lang_per_page") or []
    per_page_languages: List[Dict[str, Any]] = []
    overall: List[str] = []
    for entry in lang_per_page:
        page = int(entry.get("page") or 0)
        lang = str(entry.get("lang") or "unknown")
        tokens = [tok for tok in lang.replace(",", "+").split("+") if tok]
        normalized_tokens = [_normalize_lang_token(tok) for tok in tokens]
        normalized_tokens = [tok for tok in normalized_tokens if tok and tok != "unknown"]
        if not normalized_tokens:
            fallback_tokens: List[str] = []
            if fallback:
                for item in fallback:
                    tokens = [tok for tok in str(item or "").replace(",", "+").split("+") if tok]
                    for tok in tokens:
                        norm = _normalize_lang_token(tok)
                        if norm:
                            fallback_tokens.append(norm)
            normalized_tokens = fallback_tokens or ["unknown"]
        per_page_languages.append({"page": page, "languages": normalized_tokens})
        overall.extend([tok for tok in normalized_tokens if tok not in {"unknown"}])
    if not overall and fallback:
        for item in fallback:
            tokens = [tok for tok in str(item or "").replace(",", "+").split("+") if tok]
            for tok in tokens:
                norm = _normalize_lang_token(tok)
                if norm:
                    overall.append(norm)
    normalized = sorted({lang for lang in overall if lang}) or ["und"]
    doc_lang = "+".join(normalized)
    return {"overall": normalized, "by_page": per_page_languages, "doc": doc_lang}


def build_locale_hints(summary_payload: Dict[str, Any]) -> LocaleHints:
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


def collect_per_page_stats(summary_payload: Dict[str, Any]) -> List[PerPageStat]:
    per_page_raw = summary_payload.get("per_page_stats")
    if per_page_raw is None:
        per_page_raw = (summary_payload.get("summary", {}) or {}).get("per_page_stats")
    stats: List[PerPageStat] = []
    for entry in per_page_raw or []:
        page = int(entry.get("page") or 0)
        source = str(entry.get("source") or "")
        stat: PerPageStat = {
            "page": page,
            "source": source,
            "conf": float(entry.get("conf") or 0.0),
            "ocr_words": int(entry.get("ocr_words") or 0),
            "chars": int(entry.get("chars") or 0),
            "has_table": bool(entry.get("has_table")),
            "tables_found": int(entry.get("tables_found") or 0),
            "table_cells": int(entry.get("table_cells") or 0),
            "decision": str(entry.get("decision") or source or "native"),
            "time_ms": float(entry.get("time_ms") or 0.0),
            "lang": str(entry.get("lang") or "unknown"),
            "locale": str(entry.get("locale") or "unknown"),
            "flags": list(entry.get("flags") or []),
        }
        if entry.get("ocr_conf_avg") is not None:
            stat["ocr_conf_avg"] = float(entry.get("ocr_conf_avg") or 0.0)
        stats.append(stat)
    return stats


def load_text_blocks(readers_dir: Path) -> List[TextBlock]:
    items = _load_jsonl(readers_dir / "text_blocks.jsonl")
    blocks: List[TextBlock] = []
    for index, item in enumerate(items):
        bbox = item.get("bbox") or []
        block: TextBlock = {
            "id": str(item.get("id") or f"b{index:04d}"),
            "page": int(item.get("page") or 0),
            "text_raw": str(item.get("text_raw") or item.get("text") or ""),
            "text_lines": str(item.get("text_lines") or item.get("text_raw") or ""),
            "bbox": [float(x) for x in bbox] if isinstance(bbox, list) else [],
        }
        if item.get("is_heading_like") is not None:
            block["is_heading_like"] = bool(item.get("is_heading_like"))
        if item.get("is_list_like") is not None:
            block["is_list_like"] = bool(item.get("is_list_like"))
        if item.get("lang"):
            block["lang"] = str(item.get("lang"))
        if item.get("ocr_conf_avg") is not None:
            block["ocr_conf_avg"] = float(item.get("ocr_conf_avg") or 0.0)
        if item.get("reading_order_index") is not None:
            block["reading_order_index"] = int(item.get("reading_order_index") or index)
        blocks.append(block)
    return blocks


def load_tables_raw(readers_dir: Path) -> List[RawTable]:
    items = _load_jsonl(readers_dir / "tables_raw.jsonl")
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


def load_artifacts(readers_dir: Path) -> List[Artifact]:
    items = _load_jsonl(readers_dir / "visual_artifacts.jsonl")
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


def summarise_logs(tool_log: List[Dict[str, Any]]) -> List[str]:
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


def build_qa(summary_payload: Dict[str, Any], warnings: List[str]) -> QASection:
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
