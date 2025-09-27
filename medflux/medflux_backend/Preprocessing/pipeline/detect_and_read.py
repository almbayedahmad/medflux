from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medflux_backend.Preprocessing.phase_02_readers.readers_core import ReaderOptions, UnifiedReaders
from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type
from medflux_backend.Preprocessing.phase_01_encoding.encoding_detector import detect_text_encoding


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
    has_ocr = any("ocr" in (entry or "").lower() for entry in page_decisions)
    avg_conf_all = float(reader_summary.get("avg_conf") or 0.0)
    avg_ocr_conf = avg_conf_all if has_ocr else 0.0

    lang_field = decision.get("lang") or detect_meta.get("lang") or ""
    languages_overall = [entry.strip() for entry in lang_field.split("+") if entry.strip()]
    if not languages_overall:
        languages_overall = ["und"]
    languages_by_page = [
        {"page": idx + 1, "languages": languages_overall}
        for idx in range(pages_count)
    ]

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
        "has_ocr": has_ocr,
        "avg_ocr_conf": avg_ocr_conf,
        "table_pages": reader_summary.get("table_pages", []),
        "text_blocks_count": text_blocks_count,
        "text_blocks_path": "readers/text_blocks.jsonl",
        "timings_ms": timings_payload,
    }
    if reader_summary.get("table_stats") is not None:
        doc_meta["table_stats"] = reader_summary.get("table_stats")
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
    decision = {"file": str(input_path), **params, "summary": readers_result.get("summary", {})}
    (outdir / "detect_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return decision, readers_result, outdir


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
