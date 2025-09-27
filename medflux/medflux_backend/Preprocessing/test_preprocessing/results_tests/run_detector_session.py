import argparse, json, time
from pathlib import Path
from medflux_backend.Preprocessing.phase_00_detect_type.file_type_detector import detect_file_type

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outroot", type=str, default="out/tests", help="Root dir for outputs")
    ap.add_argument("inputs", nargs="+", help="Input files to run detection on")
    args = ap.parse_args()

    # create session folder
    ts = time.strftime("session_%Y%m%d_%H%M%S_detector")
    outdir = Path(args.outroot) / ts
    outdir.mkdir(parents=True, exist_ok=True)

    decisions = []
    for ip in args.inputs:
        ip = Path(ip)
        if not ip.exists():
            continue
        meta = detect_file_type(ip)
        fdir = outdir / ip.stem / "detection"
        fdir.mkdir(parents=True, exist_ok=True)
        outf = fdir / "detection_result.json"
        outf.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        decisions.append({"file": str(ip), "meta": meta})

    (outdir / "session_report.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    print({"session": ts, "outdir": str(outdir), "count": len(decisions)})

if __name__ == "__main__":
    main()
