import argparse, time, json
from pathlib import Path
from dataclasses import asdict
from backend.Preprocessing.phase_02_readers.readers_core import UnifiedReaders, ReaderOptions


def _convert(obj):
    """Convert Path/dataclass objects into JSON-friendly structures"""
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert(v) for v in obj]
    elif hasattr(obj, "__dataclass_fields__"):
        return _convert(asdict(obj))
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outroot", type=str, required=True)
    parser.add_argument("inputs", nargs="+")
    args = parser.parse_args()

    outroot = Path(args.outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    # Create a fresh output directory for this session
    sid = time.strftime("session_%Y%m%d_%H%M%S")
    session_dir = outroot / sid
    session_dir.mkdir(parents=True, exist_ok=True)

    files_report = []

    # Run UnifiedReaders for each input file
    for f in args.inputs:
        fpath = Path(f)
        fname = fpath.stem
        outdir = session_dir / fname
        opts = ReaderOptions(mode="mixed", lang="deu+eng", native_ocr_overlay=True)

        rdr = UnifiedReaders(outdir, opts)
        result = rdr.process([fpath])

        # Load the file-specific readers_summary.json
        sum_path = outdir / "readers" / "readers_summary.json"
        summary = None
        if sum_path.exists():
            try:
                summary = json.loads(sum_path.read_text(encoding="utf-8"))
            except Exception as e:
                summary = {"error": str(e)}

        files_report.append({
            "file": str(fpath),
            "outdir": str(outdir),
            "readers_summary": summary,
            "stats": _convert(result)
        })

    # Produce the overall session report
    report = {
        "session": sid,
        "outdir": str(session_dir),
        "count": len(files_report),
        "files": files_report
    }

    (session_dir / "session_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps({"session": sid, "outdir": str(session_dir), "count": len(files_report)}))


if __name__ == "__main__":
    main()
