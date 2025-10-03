from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type
from medflux_backend.Preprocessing.phase_01_encoding.encoding_detector import detect_text_encoding
from medflux_backend.Preprocessing.phase_02_readers.readers_core import ReaderOptions, UnifiedReaders
from readers_outputs.doc_meta import build_doc_meta
from utils.config import CFG


def _quick_detect(input_path: Path) -> Dict[str, Any]:
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


def _decide_params(meta: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
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


def _detect_encoding_meta(input_path: Path, file_type: str) -> Dict[str, Any]:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("run_readers", description="FluxAI Readers - unified runner")
    parser.add_argument("inputs", nargs="*")
    parser.add_argument("--input", dest="input_flags", action="append", default=[])
    parser.add_argument("--out", "--outdir", dest="outdir", required=True)
    parser.add_argument("--mode", "--mode-default", dest="mode_default", default="mixed")
    parser.add_argument("--lang", "--lang-default", dest="lang_default", default="deu+eng")
    parser.add_argument("--dpi", "--dpi-default", dest="dpi_default", type=int, default=300)
    parser.add_argument("--psm", "--psm-default", dest="psm_default", type=int, default=6)
    parser.add_argument("--blocks-threshold", type=int, default=3)
    parser.add_argument("--oem", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--pre", action="store_true")
    parser.add_argument("--export-xlsx", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--tables", "--tables-default", dest="tables_default", default=CFG["features"]["tables_mode"])
    parser.add_argument("--save-table-crops", action="store_true")
    parser.add_argument("--tables-min-words", type=int, default=12)
    parser.add_argument("--table-detect-min-area", type=float, default=9000.0)
    parser.add_argument("--table-detect-max-cells", type=int, default=600)
    parser.add_argument("--native-ocr-overlay", action="store_true")
    parser.add_argument("--overlay-area-thr", type=float, default=0.35)
    parser.add_argument("--overlay-min-images", type=int, default=1)
    parser.add_argument("--overlay-if-any-image", action="store_true")
    return parser.parse_args()


def _reader_options(params: Dict[str, Any], args: argparse.Namespace) -> ReaderOptions:
    tables_mode = params.get("tables_mode", args.tables_default)
    if tables_mode == "light":
        tables_mode = "detect"
    elif tables_mode == "full":
        tables_mode = "extract"
    return ReaderOptions(
        mode=params.get("mode", args.mode_default),
        lang=params.get("lang", args.lang_default),
        dpi_mode="auto",
        dpi=params.get("dpi", args.dpi_default),
        psm=params.get("psm", args.psm_default),
        oem=args.oem,
        workers=args.workers,
        use_pre=args.pre,
        export_xlsx=args.export_xlsx,
        verbose=args.verbose,
        tables_mode=tables_mode,
        save_table_crops=args.save_table_crops,
        tables_min_words=args.tables_min_words,
        table_detect_min_area=args.table_detect_min_area,
        table_detect_max_cells=args.table_detect_max_cells,
        blocks_threshold=params.get("blocks_threshold", args.blocks_threshold),
        native_ocr_overlay=args.native_ocr_overlay,
        overlay_area_thr=args.overlay_area_thr,
        overlay_min_images=args.overlay_min_images,
        overlay_if_any_image=args.overlay_if_any_image,
    )


def _process_input(
    input_path: Path,
    outdir_base: Path,
    args: argparse.Namespace,
    run_id: str,
    pipeline_id: str,
) -> Dict[str, Any]:
    file_outdir = outdir_base / input_path.stem
    file_outdir.mkdir(parents=True, exist_ok=True)

    timings: Dict[str, Any] = {
        "cleaning": None,
        "normalization": None,
        "segmentation": None,
        "merge": None,
    }

    detect_start = time.perf_counter()
    detect_meta = _quick_detect(input_path)
    timings["detect"] = (time.perf_counter() - detect_start) * 1000.0

    encoding_start = time.perf_counter()
    encoding_meta = _detect_encoding_meta(input_path, detect_meta.get("file_type", ""))
    timings["encoding"] = (time.perf_counter() - encoding_start) * 1000.0

    params = _decide_params(detect_meta, args)

    readers_start = time.perf_counter()
    options = _reader_options(params, args)
    runner = UnifiedReaders(file_outdir, options)
    readers_result = runner.process([input_path])
    readers_elapsed = (time.perf_counter() - readers_start) * 1000.0

    summary = dict(readers_result.get("summary") or {})
    timings["readers"] = summary.get("timings_ms", {}).get("total_ms", readers_elapsed)

    tool_log = list(readers_result.get("tool_log") or summary.get("tool_log") or [])
    if tool_log:
        summary["tool_log"] = tool_log

    readers_dir = Path(readers_result.get("outdir") or runner.readers_dir)
    doc_meta = build_doc_meta(
        input_path=input_path,
        detect_meta=detect_meta,
        encoding_meta=encoding_meta,
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": tool_log},
        timings=timings,
        run_id=run_id,
        pipeline_id=pipeline_id,
    )
    (file_outdir / "doc_meta.json").write_text(
        json.dumps(doc_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "input": str(input_path),
        "outdir": str(file_outdir),
        "doc_meta": doc_meta,
    }


def main() -> None:
    args = parse_args()
    outdir_base = Path(args.outdir)
    outdir_base.mkdir(parents=True, exist_ok=True)

    run_id = f"readers-{uuid.uuid4().hex}"
    pipeline_id = "preprocessing.run_readers"

    inputs = list(args.inputs) + list(args.input_flags or [])
    if not inputs:
        raise SystemExit("No input files provided. Use positional arguments or --input flags.")

    results: List[Dict[str, Any]] = []
    for raw_input in inputs:
        input_path = Path(raw_input)
        results.append(_process_input(input_path, outdir_base, args, run_id, pipeline_id))

    print(
        json.dumps(
            {
                "outdir": str(outdir_base),
                "run_id": run_id,
                "pipeline_id": pipeline_id,
                "count": len(results),
            }
        )
    )


if __name__ == "__main__":
    main()
