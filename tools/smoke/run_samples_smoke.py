# PURPOSE:
#   Run lightweight smoke checks across selected preprocessing phases using
#   repository sample files to validate end-to-end wiring (connectors → domain
#   → io) and artifact generation.
#
# OUTCOME:
#   Generates a concise JSON summary under `.artifacts/smoke/` with per-file,
#   per-phase results and emits policy-compliant logs. Designed for quick
#   operator sanity checks without heavy test harnesses.
#
# INPUTS:
#   CLI flags:
#     --phases: subset of phases to run (default: detect,encoding,readers)
#     --out-root: output root directory (default: ./.artifacts/smoke)
#     --limit: maximum files per sample group (default: 2)
#     --export-xlsx: enable XLSX export for readers
#
# OUTPUTS:
#   Writes `{out_root}/smoke_summary.json` and per-phase artifacts via io
#   overrides. Logs progress via the central logging policy.

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from core.logging import configure_logging, get_logger
from core.preprocessing.output.output_router import OutputRouter


def _pick_samples(globs: Sequence[str], *, limit: int) -> List[Path]:
    found: List[Path] = []
    for g in globs:
        for p in Path().glob(g):
            if p.is_file():
                found.append(p)
    found = sorted(found)[: max(0, int(limit))]
    return found


def _as_items(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    return [{"path": str(p)} for p in paths]


def _run_detect(files: List[Path], outdir: Path) -> Dict[str, Any]:
    from backend.Preprocessing.phase_00_detect_type.api import run_detect_type

    outdir.mkdir(parents=True, exist_ok=True)
    overrides: Dict[str, Any] = {
        "io": {
            "out_doc_path": str(outdir / "detect_type_unified_document.json"),
            "out_stats_path": str(outdir / "detect_type_stage_stats.json"),
        }
    }
    payload = run_detect_type(_as_items(files), config_overrides=overrides)
    return payload


def _run_encoding(files: List[Path], outdir: Path, *, normalize: bool) -> Dict[str, Any]:
    from backend.Preprocessing.phase_01_encoding.api import run_encoding

    outdir.mkdir(parents=True, exist_ok=True)
    overrides: Dict[str, Any] = {
        "io": {
            "out_doc_path": str(outdir / "encoding_unified_document.json"),
            "out_stats_path": str(outdir / "encoding_stage_stats.json"),
        },
    }
    if normalize:
        overrides["normalization"] = {
            "enabled": True,
            "out_dir": str(outdir / "normalized"),
            "newline_policy": "lf",
            "errors": "replace",
        }
    items = [{"path": str(p), "normalize": bool(normalize)} for p in files]
    payload = run_encoding(items, config_overrides=overrides)
    return payload


def _run_readers(files: List[Path], outdir: Path, *, export_xlsx: bool) -> Dict[str, Any]:
    from backend.Preprocessing.phase_02_readers.api import run_readers

    outdir.mkdir(parents=True, exist_ok=True)
    overrides: Dict[str, Any] = {
        "io": {
            "out_doc_path": str(outdir / "readers_doc_meta.json"),
            "out_stats_path": str(outdir / "readers_stage_stats.json"),
            "out_summary_path": str(outdir / "readers_summary.json"),
        },
        "options": {"export_xlsx": bool(export_xlsx)},
    }
    payload = run_readers(_as_items(files), config_overrides=overrides)
    return payload


def main() -> None:
    ap = argparse.ArgumentParser(description="Run sample-based smoke checks for selected phases")
    ap.add_argument(
        "--phases",
        nargs="+",
        default=["detect", "encoding", "readers"],
        help="Phases to run (subset of: detect, encoding, readers)",
    )
    ap.add_argument("--out-root", default=".artifacts/smoke", help="Output root directory")
    ap.add_argument("--limit", type=int, default=2, help="Max files per sample group")
    ap.add_argument("--export-xlsx", action="store_true", help="Readers: export XLSX tables")
    args = ap.parse_args()

    # Configure logging (dev profile by default); honor MEDFLUX_LOG_* env toggles
    os.environ.setdefault("MEDFLUX_LOG_PROFILE", "dev")
    configure_logging(force=False)
    log = get_logger("cli")

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    router = OutputRouter(root=out_root, create_session_subdir=False)

    # Collect sample files
    txt_files = _pick_samples(["samples/txt_samples/*.txt", "samples/hello.txt"], limit=args.limit)
    pdf_files = _pick_samples(["samples/pdf_samples/*.pdf"], limit=args.limit)
    img_files = _pick_samples(["samples/image_samples/*.*"], limit=args.limit)

    summary: Dict[str, Any] = {
        "phases": args.phases,
        "out_root": str(out_root),
        "results": [],
    }

    try:
        if "detect" in args.phases:
            det_dir = router.stage_dir("detector")
            payload = _run_detect(txt_files + pdf_files + img_files, det_dir)
            summary["results"].append({"phase": "detect", "ok": True, "io": payload.get("io")})
            log.info("smoke.detect.ok", extra={"count": len((payload.get("unified_document") or {}).get("items", []))})
    except Exception as exc:
        import traceback as _tb
        log.error("smoke.detect.failed", extra={"err": str(exc)}, exc_info=True)
        summary["results"].append({"phase": "detect", "ok": False, "error": str(exc), "trace": _tb.format_exc()})

    try:
        if "encoding" in args.phases and txt_files:
            enc_dir = router.stage_dir("encoder")
            payload = _run_encoding(txt_files, enc_dir, normalize=True)
            summary["results"].append({"phase": "encoding", "ok": True, "io": payload.get("io")})
            log.info("smoke.encoding.ok", extra={"normalized": (payload.get("stage_stats") or {}).get("normalized_success")})
    except Exception as exc:
        import traceback as _tb
        log.error("smoke.encoding.failed", extra={"err": str(exc)}, exc_info=True)
        summary["results"].append({"phase": "encoding", "ok": False, "error": str(exc), "trace": _tb.format_exc()})

    try:
        if "readers" in args.phases and (pdf_files or img_files or txt_files):
            rdr_dir = router.stage_dir("readers")
            # Prefer PDFs/images; fallback to txt
            candidates = pdf_files or img_files or txt_files
            payload = _run_readers(candidates, rdr_dir, export_xlsx=bool(args.export_xlsx))
            summary["results"].append({"phase": "readers", "ok": True, "io": payload.get("io")})
            log.info("smoke.readers.ok", extra={"has_summary": bool((rdr_dir / "readers_summary.json").exists())})
    except Exception as exc:
        import traceback as _tb
        log.error("smoke.readers.failed", extra={"err": str(exc)}, exc_info=True)
        summary["results"].append({"phase": "readers", "ok": False, "error": str(exc), "trace": _tb.format_exc()})

    # Persist summary for later inspection
    (out_root / "smoke_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
