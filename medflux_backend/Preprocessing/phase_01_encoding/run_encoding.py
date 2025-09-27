import json
import argparse
import os
from .encoding_detector import detect_text_encoding
from .encoding_normalizer import convert_to_utf8

def _dest_path_for(outdir: str, src_path: str) -> str:
    base = os.path.basename(src_path)
    stem, ext = os.path.splitext(base)
    if not ext:
        ext = ".txt"
    os.makedirs(outdir, exist_ok=True)
    return os.path.join(outdir, f"{stem}.utf8{ext}")

def main():
    ap = argparse.ArgumentParser(description="Detect/normalize text encoding (phase_01_encoding)")
    ap.add_argument("paths", nargs="+", help="Input text files")
    ap.add_argument("--normalize", action="store_true", help="Convert to UTF-8 and write *.utf8.* files")
    ap.add_argument("--newline", choices=["lf","crlf"], default="lf", help="Newline normalization policy")
    ap.add_argument("--errors", choices=["strict","replace","ignore"], default="strict", help="Decoding error policy")
    ap.add_argument("--outdir", default=None, help="Write outputs to this directory instead of beside input file")
    args = ap.parse_args()

    # Filter out accidental empty path placeholders
    paths = [p for p in args.paths if p and str(p).strip() and p not in ("\\", "/")]

    out = []
    for p in paths:
        if args.normalize:
            dest_path = None
            if args.outdir:
                dest_path = _dest_path_for(args.outdir, p)
            res = convert_to_utf8(p, dest_path=dest_path, newline_policy=args.newline, errors=args.errors)
        else:
            info = detect_text_encoding(p)
            res = {
                "file_path": p,
                "detected_encoding": info.encoding,
                "confidence": info.confidence,
                "bom": info.bom,
                "is_utf8": info.is_utf8,
                "sample_len": info.sample_len,
            }
        out.append(res)

    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()


