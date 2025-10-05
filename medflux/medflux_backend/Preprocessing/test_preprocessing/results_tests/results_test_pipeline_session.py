import argparse, json, time, unicodedata, mimetypes
from pathlib import Path
from dataclasses import asdict

# ===================== Utilities =====================
def _convert(obj):
    """Make objects JSON-serializable (convert Path to str, recurse dict/list)."""
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
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
                t = obj.get("text", "")
                if t:
                    lines.append(str(t))
            except Exception:
                pass
        return "\n".join(lines)
    return ""

# ===================== Detection (robust import) =====================
from medflux_backend.Preprocessing.phase_00_detect_type.internal_helpers.detect_type_detection_helper import process_detect_type_file


def run_detection(file_path: Path) -> dict:
    res = process_detect_type_file(str(file_path))  # May return a dataclass instance
    try:
        res = asdict(res)
    except Exception:
        pass
    return _convert(res)

# ===================== Readers =====================
from medflux_backend.Preprocessing.phase_02_readers.pipeline_workflow.readers_pipeline_main import ReadersOrchestrator\nfrom medflux_backend.Preprocessing.phase_02_readers.internal_helpers.reader_helpers_runtime_options import ReaderOptions

def run_readers(file_path: Path, outdir: Path, rec: dict, export_xlsx: bool) -> dict:
    opts = ReaderOptions(
        mode=rec.get("mode", "mixed"),
        lang=rec.get("lang", "deu+eng"),
        export_xlsx=export_xlsx,
        native_ocr_overlay=True,
        overlay_area_thr=0.12,
        overlay_min_images=1,
    )
    rdr = ReadersOrchestrator(outdir, opts)
    rdr.process([file_path])  # Produces readers/readers_summary.json and related outputs
    sum_path = outdir / "readers" / "readers_summary.json"
    if sum_path.exists():
        try:
            return json.loads(sum_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

# ===================== Encoding (robust) =====================
# Prefer the stage pipeline when present, otherwise fall back to basic normalisation
try:
    from medflux_backend.Preprocessing.phase_01_encoding.pipeline_workflow.encoding_pipeline import run_encoding_pipeline as _run_encoding_pipeline
except Exception:
    _run_encoding_pipeline = None


def run_encoding(readers_dir: Path, outdir: Path, file_path: Path) -> dict:
    if _run_encoding_pipeline is not None:
        try:
            normalized_dir = outdir / 'normalized'
            payload = _run_encoding_pipeline(
                generic_items=[{'path': str(file_path), 'normalize': True}],
                config_overrides={
                    'io': {
                        'out_doc_path': str(outdir / 'encoding_unified_document.json'),
                        'out_stats_path': str(outdir / 'encoding_stage_stats.json'),
                    },
                    'normalization': {
                        'enabled': True,
                        'out_dir': str(normalized_dir),
                        'errors': 'replace',
                        'newline_policy': 'lf',
                    },
                },
            )
            unified = _convert(payload.get('unified_document') or {})
            (outdir / 'encoding_unified_document.json').write_text(json.dumps(unified, ensure_ascii=False, indent=2), encoding='utf-8')
            stats = _convert(payload.get('stage_stats') or {})
            (outdir / 'encoding_stage_stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
            return unified
        except Exception:
            pass
    raw = _load_unified_text(readers_dir)
    if not raw:
        stats = {'file': str(file_path), 'error': 'no unified_text found', 'orig_len': 0, 'enc_len': 0, 'bytes_utf8': 0, 'lines': 0}
        (outdir / 'encoding_stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
        return stats
    norm = _encode_text(raw)
    (outdir / 'text_utf8_nfc.txt').write_text(norm, encoding='utf-8')
    stats = {
        'file': str(file_path),
        'orig_len': len(raw),
        'enc_len': len(norm),
        'bytes_utf8': len(norm.encode('utf-8')),
        'lines': norm.count('
') + (1 if norm else 0),
    }
    (outdir / 'encoding_stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    return stats

# ===================== Main =====================
def tune_detection(meta: dict) -> dict:
    try:
        details = (meta or {}).get("details") or {}
        pages = details.get("per_page", []) or []
        has_unclear = any((p.get("page_mode") or p.get("mode")) == "unclear" for p in pages)
        has_heavy_images = any(float(p.get("image_area_ratio", 0) or 0) > 0.25 for p in pages)
        if has_unclear or has_heavy_images:
            details["mixed"] = True
            meta["details"] = details
            meta["ocr_recommended"] = True
            rec = (meta.get("recommended") or {})
            rec["mode"] = "mixed"
            meta["recommended"] = rec
            # Tag for tracing in the test output
            meta["post_rule"] = "mixed_by_images_or_unclear"
    except Exception:
        pass
    return meta

def main():
    ap = argparse.ArgumentParser(description="Results test pipeline session: detection + readers + encoding")
    ap.add_argument("--outroot", required=True, help="Root folder to store sessions")
    ap.add_argument("--export-xlsx", action="store_true", help="Export tables to XLSX (if available)")
    ap.add_argument("inputs", nargs="+", help="Input files (PDF/DOCX/Images)")
    args = ap.parse_args()

    outroot = Path(args.outroot); outroot.mkdir(parents=True, exist_ok=True)
    session_id = time.strftime("session_%Y%m%d_%H%M%S")
    session_dir = outroot / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    session_report = {"session": session_id, "files": []}

    for ip in args.inputs:
        fpath = Path(ip)
        if not fpath.exists():
            continue

        fdir = session_dir / fpath.stem
        (fdir).mkdir(parents=True, exist_ok=True)

        # ---------- 1) Detection ----------
        det_dir = fdir / "detection"; det_dir.mkdir(parents=True, exist_ok=True)
        meta = run_detection(fpath)
        meta = tune_detection(meta)
        (det_dir / "detection_result.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        # ---------- 2) Readers -----------
        rec = meta.get("recommended", {}) if isinstance(meta, dict) else {}
        rdr_root = fdir / "readers_root"; rdr_root.mkdir(parents=True, exist_ok=True)
        readers_summary = run_readers(fpath, rdr_root, rec, args.export_xlsx)

        # ---------- 3) Encoding ----------
        enc_dir = fdir / "encoding"; enc_dir.mkdir(parents=True, exist_ok=True)
        enc_stats = run_encoding(rdr_root / "readers", enc_dir, fpath)

        # ---------- Aggregate per-file ----------
        session_report["files"].append({
            "file": str(fpath),
            "detection": meta,
            "readers_summary": readers_summary,
            "encoding": enc_stats,
            "outdir": str(fdir)
        })

    # ---------- Write session report ----------
    (session_dir / "session_report.json").write_text(json.dumps(session_report, ensure_ascii=False, indent=2), encoding="utf-8")
    print({"session": session_id, "outdir": str(session_dir), "count": len(session_report["files"])})

if __name__ == "__main__":
    main()


