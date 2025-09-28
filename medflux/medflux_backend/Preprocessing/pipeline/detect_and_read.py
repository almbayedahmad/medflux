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
from medflux_backend.Preprocessing.output_structure.readers_outputs.builder import build_doc_meta



def quick_detect(input_path: Path) -> Dict[str, Any]:
    result = detect_file_type(str(input_path))
    recommended = result.recommended or {}
    return {
        "detected_mode": recommended.get("mode"),
        "lang": recommended.get("lang") or "deu+eng",
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

        doc_meta = build_doc_meta(
            input_path=input_path,
            detect_meta=detect_meta,
            encoding_meta=encoding_meta,
            readers_result=readers_result,
            timings=timings,
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

