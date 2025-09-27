import argparse, json, time
from pathlib import Path
import unicodedata

def encode_text(text: str) -> str:
    """Normalize text to NFC and enforce UTF-8 encoding."""
    return unicodedata.normalize("NFC", text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outroot", type=str, default="out/tests", help="Root dir for outputs")
    ap.add_argument("inputs", nargs="+", help="Input text files to encode")
    args = ap.parse_args()

    ts = time.strftime("session_%Y%m%d_%H%M%S_encoder")
    outdir = Path(args.outroot) / ts
    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for ip in args.inputs:
        ip = Path(ip)
        if not ip.exists():
            continue
        text = ip.read_text(encoding="utf-8", errors="ignore")
        encoded = encode_text(text)

        fdir = outdir / ip.stem / "encoding"
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / "text_utf8_nfc.txt").write_text(encoded, encoding="utf-8")

        stats = {"file": str(ip), "orig_len": len(text), "enc_len": len(encoded)}
        (fdir / "encoding_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(stats)

    (outdir / "session_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print({"session": ts, "outdir": str(outdir), "count": len(results)})

if __name__ == "__main__":
    main()
