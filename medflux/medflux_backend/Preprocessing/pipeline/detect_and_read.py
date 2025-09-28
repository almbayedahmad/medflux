from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medflux_backend.Preprocessing.phase_02_readers.readers_core import ReaderOptions, UnifiedReaders
from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type
from medflux_backend.Preprocessing.phase_01_encoding.encoding_detector import detect_text_encoding


LANG_ALIAS_MAP = {
    "deu": "de",
    "ger": "de",
    "german": "de",
    "de": "de",
    "eng": "en",
    "english": "en",
    "en": "en",
}


def _normalise_lang_code(raw: str) -> str:
    value = (raw or "").strip().lower()
    if not value:
        return ""
    if value in {"und", "unknown"}:
        return "unknown"
    if value == "mixed":
        return "mixed"
    return LANG_ALIAS_MAP.get(value, value)


def _split_lang_field(raw: Any) -> List[str]:
    tokens: List[str] = []
    if isinstance(raw, str):
        parts = re.split(r"[+;,/\\s]+", raw)
        for part in parts:
            normalised = _normalise_lang_code(part)
            if normalised:
                tokens.append(normalised)
    elif isinstance(raw, (list, tuple, set)):
        for item in raw:
            normalised = _normalise_lang_code(str(item))
            if normalised:
                tokens.append(normalised)
    return tokens


def quick_detect(input_path: Path) -> Dict[str, Any]:
    result = detect_file_type(str(input_path))
    recommended = result.recommended or {}
    return {
        "detected_mode": recommended.get("mode"),
        "lang": "deu+eng",
        "dpi": recommended.get("dpi", 300),
        "psm": recommended.get("psm", 6),
        "tables_mode": recommended.get("tables_mode", "light"),
        "file_type": result.file_type.value,
        "confidence": result.confidence,
        "details": result.details or {},
    }


def decide_params(meta: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    mode = (meta.get("detected_mode") or args.mode_default).lower()
    file_type = (meta.get("file_type") or "").lower()
    confidence = float(meta.get("confidence") or 0.0)

    if file_type.startswith("pdf") and confidence < 0.7:
        mode = "mixed"

    return {
        "mode": mode,
        "lang": meta.get("lang") or args.lang_default,
        "dpi": int(meta.get("dpi", args.dpi_default)),
        "psm": int(meta.get("psm", args.psm_default)),
        "tables_mode": meta.get("tables_mode") or args.tables_default,
        "blocks_threshold": args.blocks_threshold,
    }


def detect_encoding_meta(input_path: Path, file_type: str) -> Dict[str, Any]:
    """Return a normalised encoding payload for doc_meta."""
    payload: Dict[str, Any] = {
        "primary": None,
        "confidence": None,
        "bom": False,
        "is_utf8": None,
        "sample_len": 0,
    }
    if file_type in {"txt"}:
        info = detect_text_encoding(str(input_path))
        payload.update(
            {
                "primary": info.encoding,
                "confidence": info.confidence,
                "bom": info.bom,
                "is_utf8": info.is_utf8,
                "sample_len": info.sample_len,
            }
        )
    return payload


def map_file_type_for_meta(raw: str) -> str:
    mapping = {
        "pdf_text": "pdf_text",
        "pdf_scanned": "pdf_scan",
        "pdf_mixed": "pdf_scan_hybrid",
        "docx": "docx",
        "image": "image",
        "txt": "txt",
    }
    return mapping.get((raw or "").lower(), raw or "unknown")



def assemble_doc_meta(
    input_path: Path,
    detect_meta: Dict[str, Any],
    decision: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    reader_summary: Dict[str, Any],
    timings_ms: Dict[str, Any],
) -> Dict[str, Any]:
    pages_count = int(reader_summary.get("page_count") or 0)
    page_decisions: List[str] = list(reader_summary.get("page_decisions") or [])
    text_blocks_count = int(reader_summary.get("text_blocks_count") or 0)
    tables_raw_count = int(reader_summary.get("tables_raw_count") or 0)
    has_ocr = any("ocr" in (entry or "").lower() for entry in page_decisions)
    avg_conf_all = float(reader_summary.get("avg_conf") or 0.0)
    avg_ocr_conf = avg_conf_all if has_ocr else 0.0

    fallback_langs = _split_lang_field(decision.get("lang")) or _split_lang_field(
        detect_meta.get("lang")
    )
    if not fallback_langs:
        fallback_langs = ["und"]

    lang_per_page = reader_summary.get("lang_per_page") or []
    locale_per_page = reader_summary.get("locale_per_page") or []

    languages_by_page: List[Dict[str, Any]] = []
    lang_values: List[str] = []
    if lang_per_page:
        for idx, item in enumerate(lang_per_page):
            page_no = int(item.get("page") or idx + 1)
            page_langs = _split_lang_field(item.get("lang"))
            if not page_langs or all(val in {"unknown", "und"} for val in page_langs):
                page_langs = list(fallback_langs)
            languages_by_page.append({"page": page_no, "languages": page_langs})
            lang_values.extend(page_langs)
    else:
        for idx in range(pages_count):
            languages_by_page.append({"page": idx + 1, "languages": list(fallback_langs)})
        lang_values.extend(fallback_langs)

    filtered_langs = [val for val in lang_values if val not in {"unknown", "und"}]
    if filtered_langs:
        languages_overall = sorted(set(filtered_langs))
    else:
        languages_overall = sorted(set(fallback_langs)) or ["und"]

    locale_by_page: List[Dict[str, Any]] = []
    locale_values: List[str] = []
    if locale_per_page:
        for item in locale_per_page:
            page_no = int(item.get("page") or len(locale_by_page) + 1)
            loc = item.get("locale") or "unknown"
            locale_values.append(loc)
            locale_by_page.append({"page": page_no, "locale": loc})
    else:
        locale_by_page = [
            {"page": idx + 1, "locale": "unknown"}
            for idx in range(pages_count)
        ]
    overall_locale = "unknown"
    locale_filtered = [val for val in locale_values if val not in ("unknown", "mixed")]
    if locale_filtered:
        overall_locale = sorted(set(locale_filtered))[0]
    elif locale_values:
        overall_locale = "mixed" if len(set(locale_values)) > 1 else locale_values[0]

    timings_payload: Dict[str, Any] = {
        "detect": _maybe_round(timings_ms.get("detect")),
        "encoding": _maybe_round(timings_ms.get("encoding")),
        "readers": _maybe_round(timings_ms.get("readers")),
        "cleaning": timings_ms.get("cleaning"),
        "normalization": timings_ms.get("normalization"),
        "segmentation": timings_ms.get("segmentation"),
        "merge": timings_ms.get("merge"),
    }
    total_ms = sum(
        value for value in timings_payload.values() if isinstance(value, (int, float))
    )
    timings_payload["total"] = _maybe_round(total_ms)

    doc_meta = {
        "file_name": input_path.name,
        "file_type": map_file_type_for_meta(detect_meta.get("file_type")),
        "pages_count": pages_count,
        "detected_encodings": encoding_meta,
        "detected_languages": {
            "overall": languages_overall,
            "by_page": languages_by_page,
        },
        "locale_hints": {
            "overall": overall_locale,
            "by_page": locale_by_page,
        },
        "has_ocr": has_ocr,
        "avg_ocr_conf": avg_ocr_conf,
        "table_pages": reader_summary.get("table_pages", []),
        "text_blocks_count": text_blocks_count,
        "text_blocks_path": "readers/text_blocks.jsonl",
        "tables_raw_count": tables_raw_count,
        "tables_raw_path": "readers/tables_raw.jsonl",
        "visual_artifacts_count": int(reader_summary.get("visual_artifacts_count") or 0),
        "visual_artifacts_path": "readers/visual_artifacts.jsonl",
        "timings_ms": timings_payload,
    }
    if reader_summary.get("table_stats") is not None:
        doc_meta["table_stats"] = reader_summary.get("table_stats")

    qa_flags = dict(reader_summary.get("qa_flags") or {})
    warnings_list = list(reader_summary.get("warnings") or [])
    qa_payload = dict(reader_summary.get("qa") or {})

    doc_meta["qa"] = {
        "needs_review": bool(qa_flags.get("manual_review")),
        "pages": list(qa_flags.get("pages") or []),
        "warnings": warnings_list,
        "low_conf_pages": list(qa_payload.get("low_conf_pages") or []),
        "low_text_pages": list(qa_payload.get("low_text_pages") or []),
        "tables_fail": bool(qa_payload.get("tables_fail")),
        "reasons": list(qa_payload.get("reasons") or []),
    }

    doc_meta["processing_log"] = list(reader_summary.get("tool_log") or [])
    if reader_summary.get("per_page_stats") is not None:
        doc_meta["per_page_stats"] = reader_summary.get("per_page_stats")
    if reader_summary.get("thresholds") is not None:
        doc_meta["thresholds"] = reader_summary.get("thresholds")
    return doc_meta


def _maybe_round(value: Any, digits: int = 2) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    return value



def run_one(
    input_path: Path,
    outdir_base: Path,
    params: Dict[str, Any],
    args: argparse.Namespace,
) -> Tuple[Dict[str, Any], Dict[str, Any], Path]:
    outdir = outdir_base / input_path.stem
    outdir.mkdir(parents=True, exist_ok=True)

    options = ReaderOptions(
        mode=params.get("mode", "mixed"),
        lang=params.get("lang", args.lang_default),
        dpi_mode="auto",
        dpi=params.get("dpi", args.dpi_default),
        psm=params.get("psm", args.psm_default),
        oem=args.oem,
        workers=args.workers,
        use_pre=args.pre,
        export_xlsx=args.export_xlsx,
        verbose=args.verbose,
        tables_mode=params.get("tables_mode", args.tables_default),
        save_table_crops=args.save_table_crops,
        tables_min_words=args.tables_min_words,
        table_detect_min_area=args.table_detect_min_area,
        table_detect_max_cells=args.table_detect_max_cells,
        blocks_threshold=params.get("blocks_threshold", args.blocks_threshold),
        native_ocr_overlay=True,
        overlay_area_thr=0.12,
        overlay_min_images=1,
        overlay_if_any_image=True,
    )

    readers_result = UnifiedReaders(outdir, options).process([input_path])
    summary: Dict[str, Any] = dict(readers_result.get("summary", {}) or {})
    tool_log = list(readers_result.get("tool_log") or summary.get("tool_log") or [])
    if tool_log:
        summary["tool_log"] = tool_log

    summary_path = outdir / "readers" / "readers_summary.json"
    qa_flags: Dict[str, Any] = {}
    qa_payload: Dict[str, Any] = {}

    if summary_path.exists():
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            summary = dict(payload.get("summary", summary) or summary)

            disk_tool_log = payload.get("tool_log")
            if disk_tool_log:
                tool_log = list(disk_tool_log)
                summary["tool_log"] = tool_log

            qa_flags = dict(payload.get("flags", {}) or {})
            qa_payload = dict(payload.get("qa", {}) or {})

            if "thresholds" in payload:
                summary.setdefault("thresholds", payload.get("thresholds"))
            if "per_page_stats" in payload:
                summary.setdefault("per_page_stats", payload.get("per_page_stats"))
        except Exception:
            qa_flags = {}
            qa_payload = {}

    summary.setdefault("warnings", list(summary.get("warnings", [])))
    summary["qa_flags"] = qa_flags
    summary.setdefault("qa", qa_payload)
    summary.setdefault("tool_log", tool_log)

    visual_count = int(
        summary.get("visual_artifacts_count")
        or readers_result.get("visual_artifacts_count")
        or 0
    )
    summary["visual_artifacts_count"] = visual_count

    decision = {"file": str(input_path), **params, "summary": summary}
    (outdir / "detect_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return decision, {**readers_result, "summary": summary, "tool_log": tool_log}, outdir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("detect_and_read", description="Auto-detect then run readers")
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--mode-default", default="mixed")
    parser.add_argument("--lang-default", default="deu+eng")
    parser.add_argument("--dpi-default", type=int, default=300)
    parser.add_argument("--psm-default", type=int, default=6)
    parser.add_argument("--blocks-threshold", type=int, default=3)
    parser.add_argument("--oem", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--pre", action="store_true")
    parser.add_argument("--export-xlsx", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--tables-default", default="detect")
    parser.add_argument("--save-table-crops", action="store_true")
    parser.add_argument("--tables-min-words", type=int, default=12)
    parser.add_argument("--table-detect-min-area", type=float, default=9000.0)
    parser.add_argument("--table-detect-max-cells", type=int, default=600)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outdir_base = Path(args.outdir)
    outdir_base.mkdir(parents=True, exist_ok=True)

    decisions: List[Dict[str, Any]] = []
    metadata_entries: List[Dict[str, Any]] = []

    for raw_input in args.inputs:
        input_path = Path(raw_input)

        timings: Dict[str, Any] = {
            "cleaning": None,
            "normalization": None,
            "segmentation": None,
            "merge": None,
        }

        detect_start = time.perf_counter()
        detect_meta = quick_detect(input_path)
        timings["detect"] = (time.perf_counter() - detect_start) * 1000.0

        encoding_start = time.perf_counter()
        encoding_meta = detect_encoding_meta(input_path, detect_meta.get("file_type", ""))
        timings["encoding"] = (time.perf_counter() - encoding_start) * 1000.0

        params = decide_params(detect_meta, args)

        readers_start = time.perf_counter()
        decision, readers_result, file_outdir = run_one(input_path, outdir_base, params, args)
        readers_elapsed = (time.perf_counter() - readers_start) * 1000.0
        summary = decision.get("summary", {})
        timings["readers"] = summary.get("timings_ms", {}).get("total_ms", readers_elapsed)

        doc_meta = assemble_doc_meta(
            input_path=input_path,
            detect_meta=detect_meta,
            decision=decision,
            encoding_meta=encoding_meta,
            reader_summary=summary,
            timings_ms=timings,
        )
        (file_outdir / "doc_meta.json").write_text(
            json.dumps(doc_meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        decisions.append(decision)
        metadata_entries.append(doc_meta)

    report_path = outdir_base / "detect_and_read_report.json"
    report_path.write_text(
        json.dumps({"decisions": decisions, "doc_meta": metadata_entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print({"outdir": str(outdir_base), "count": len(decisions)})


if __name__ == "__main__":
    main()
