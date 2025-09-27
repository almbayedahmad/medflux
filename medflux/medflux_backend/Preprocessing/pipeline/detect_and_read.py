from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medflux_backend.Preprocessing.phase_02_readers.readers_core import ReaderOptions, UnifiedReaders
from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type


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


def run_one(input_path: Path, outdir_base: Path, params: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
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

    result = UnifiedReaders(outdir, options).process([input_path])
    decision = {"file": str(input_path), **params, "summary": result.get("summary", {})}
    (outdir / "detect_decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    return decision


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

    decisions = []
    for raw_input in args.inputs:
        input_path = Path(raw_input)
        meta = quick_detect(input_path)
        params = decide_params(meta, args)
        decisions.append(run_one(input_path, outdir_base, params, args))

    report_path = outdir_base / "detect_and_read_report.json"
    report_path.write_text(json.dumps({"decisions": decisions}, ensure_ascii=False, indent=2), encoding="utf-8")
    print({"outdir": str(outdir_base), "count": len(decisions)})


if __name__ == "__main__":
    main()
