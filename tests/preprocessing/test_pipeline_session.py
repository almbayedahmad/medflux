import argparse
import json
import mimetypes
import unicodedata
from dataclasses import asdict
from pathlib import Path

from core.preprocessing.output.output_router import OutputRouter

# ===================== Utilities =====================

def _convert(obj):
    """Make objects JSON-serializable (convert Path to str, recurse dict/list)."""
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def _encode_text(text: str) -> str:
    """Normalize text to NFC; caller should save as UTF-8."""
    return unicodedata.normalize("NFC", text or "")


def _load_unified_text(readers_dir: Path) -> str:
    """Prefer unified_text.txt; fallback to building from unified_text.jsonl."""
    txt = readers_dir / "unified_text.txt"
    if txt.exists():
        return txt.read_text(encoding="utf-8", errors="ignore")
    jl = readers_dir / "unified_text.jsonl"
    if jl.exists():
        lines = []
        for line in jl.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                obj = json.loads(line)
                text_value = obj.get("text", "")
                if text_value:
                    lines.append(str(text_value))
            except Exception:
                continue
        return "\n".join(lines)
    return ""


# ===================== Detection import (robust) =====================
from core.preprocessing.services.detect import DetectService


def run_detection(file_path: Path) -> dict:
    result = DetectService.detect_file(str(file_path))
    return _convert(result)


# ===================== Readers via v2 API =====================
from backend.Preprocessing.phase_02_readers.api import run_readers as run_readers_api


def run_readers(file_path: Path, outdir: Path, rec: dict, export_xlsx: bool) -> dict:
    readers_root = outdir / "readers"
    readers_root.mkdir(parents=True, exist_ok=True)
    overrides = {
        "io": {
            "out_doc_path": str(readers_root / "readers_doc_meta.json"),
            "out_stats_path": str(readers_root / "readers_stage_stats.json"),
            "out_summary_path": str(readers_root / "readers_summary.json"),
        },
        "options": {
            # Map detection recommendations when present
            "mode": rec.get("mode") or "mixed",
            "lang": rec.get("lang") or "deu+eng",
            # Best-effort export flag pass-through
            "export_xlsx": bool(export_xlsx),
        },
    }
    items = [{"path": str(file_path)}]
    # Execute readers via standardized API; writers persist outputs based on overrides
    run_readers_api(items, config_overrides=overrides)
    summary_path = readers_root / "readers_summary.json"
    if summary_path.exists():
        try:
            return json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def run_encoding(readers_dir: Path, outdir: Path, file_path: Path | None = None) -> dict:
    # Use v2 API; readers_dir not required anymore.
    if file_path is None:
        return {}
    from backend.Preprocessing.phase_01_encoding.api import run_encoding as run_encoding_api

    normalized_dir = outdir / "normalized"
    overrides = {
        "io": {
            "out_doc_path": str(outdir / "encoding_unified_document.json"),
            "out_stats_path": str(outdir / "encoding_stage_stats.json"),
        },
        "normalization": {
            "enabled": True,
            "out_dir": str(normalized_dir),
            "errors": "replace",
            "newline_policy": "lf",
        },
    }
    payload = run_encoding_api(
        generic_items=[{"path": str(file_path), "normalize": True}],
        config_overrides=overrides,
    )
    # Files are already written by the writer; still return the unified doc
    unified = _convert(payload.get("unified_document") or {})
    return unified


# ===================== Main =====================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Results test pipeline session: detection + readers + encoding",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input files (PDF/DOCX/Images)",
    )
    parser.add_argument(
        "--outroot",
        default=None,
        help=(
            "Optional base directory for smoke results. Defaults to "
            "`MEDFLUX_OUTPUT_ROOT` (or <repo>/outputs/preprocessing/pre_smoke_results`)."
        ),
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run identifier (defaults to timestamp).",
    )
    parser.add_argument(
        "--export-xlsx",
        action="store_true",
        help="Export tables to XLSX (if available)",
    )
    args = parser.parse_args()

    root_override: Path | None = None
    if args.outroot:
        root_override = Path(args.outroot).expanduser().resolve()
        root_override.mkdir(parents=True, exist_ok=True)

    router = OutputRouter(root=root_override, run_id=args.run_id)
    session_dir = router.all_phases_dir()
    detector_stage_root = router.stage_dir("detector")
    encoder_stage_root = router.stage_dir("encoder")
    readers_stage_root = router.stage_dir("readers")

    session_report = {
        "session": router.run_id,
        "files": [],
        "stages": {
            "detector": str(detector_stage_root),
            "encoder": str(encoder_stage_root),
            "readers": str(readers_stage_root),
        },
    }
    for raw in args.inputs:
        file_path = Path(raw).expanduser().resolve()
        if not file_path.exists():
            continue



        detector_dir = detector_stage_root / file_path.stem
        encoder_dir = encoder_stage_root / file_path.stem
        readers_dir = readers_stage_root / file_path.stem
        for directory in (detector_dir, encoder_dir, readers_dir):
            directory.mkdir(parents=True, exist_ok=True)

        # ---------- 1) Detection ----------
        detection_meta = run_detection(file_path)
        (detector_dir / "detection_result.json").write_text(
            json.dumps(detection_meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # ---------- 2) Readers -----------
        recommended = detection_meta.get("recommended", {}) if isinstance(detection_meta, dict) else {}
        readers_summary = run_readers(
            file_path,
            readers_dir,
            recommended,
            args.export_xlsx,
        )

        # ---------- 3) Encoding ----------
        encoding_stats = run_encoding(
            readers_dir / "readers",
            encoder_dir,
            file_path,
        )

        session_report["files"].append(
            {
                "file": str(file_path),
                "mimetype": mimetypes.guess_type(file_path.name)[0],
                "detection": detection_meta,
                "readers_summary": readers_summary,
                "encoding": encoding_stats,
                "detector_dir": str(detector_dir),
                "readers_dir": str(readers_dir),
                "encoder_dir": str(encoder_dir),
            }
        )

    summary_path = session_dir / "session_report.json"
    summary_path.write_text(
        json.dumps(_convert(session_report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print({
        "session": router.run_id,
        "outdir": str(session_dir),
        "count": len(session_report["files"]),
        "summary": str(summary_path),
    })


if __name__ == "__main__":
    main()
