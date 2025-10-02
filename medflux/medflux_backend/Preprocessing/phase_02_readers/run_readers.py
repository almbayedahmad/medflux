from __future__ import annotations
import argparse
from pathlib import Path
from .readers_core import UnifiedReaders, ReaderOptions
from utils.config import CFG


def parse_args():
    p = argparse.ArgumentParser(prog="run_readers", description="FluxAI Readers - unified runner")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--outdir","--outroot", required=True)
    p.add_argument("--mode", choices=["native","ocr","mixed"], default="mixed")
    p.add_argument("--lang", default="deu+eng")
    p.add_argument("--dpi-mode", default="auto")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--psm", type=int, default=6)
    p.add_argument("--oem", type=int, default=3)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--pre", action="store_true")
    p.add_argument("--export-xlsx", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--tables", choices=["off","detect","extract","light","full"], default=CFG["features"]["tables_mode"])
    p.add_argument("--save-table-crops", action="store_true")
    p.add_argument("--tables-min-words", type=int, default=12)
    p.add_argument("--blocks-threshold", type=int, default=3)
    # Overlay controls
    p.add_argument("--native-ocr-overlay", action="store_true")
    p.add_argument("--overlay-area-thr", type=float, default=0.35)
    p.add_argument("--overlay-min-images", type=int, default=1)
    p.add_argument("--overlay-if-any-image", action="store_true")  # NEW
    return p.parse_args()

def main():
    args = parse_args()
    tables_mode = args.tables
    if tables_mode == "light":
        tables_mode = "detect"
    elif tables_mode == "full":
        tables_mode = "extract"

    opts = ReaderOptions(
        mode=args.mode, lang=args.lang, dpi_mode=args.dpi_mode, oem=args.oem,
        dpi=args.dpi, psm=args.psm, workers=args.workers, use_pre=args.pre,
        export_xlsx=args.export_xlsx, verbose=args.verbose, tables_mode=tables_mode,
        save_table_crops=args.save_table_crops, tables_min_words=args.tables_min_words,
        blocks_threshold=args.blocks_threshold,
        native_ocr_overlay=args.native_ocr_overlay,
        overlay_area_thr=args.overlay_area_thr,
        overlay_min_images=args.overlay_min_images,
        overlay_if_any_image=args.overlay_if_any_image,   # NEW
    )
    runner = UnifiedReaders(Path(args.outdir), opts)
    print(runner.process([Path(x) for x in args.inputs]))

if __name__ == "__main__":
    main()

