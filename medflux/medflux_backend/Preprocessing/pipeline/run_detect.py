# -*- coding: utf-8 -*-
"""
run_detect.py
Simple runner for the improved detector with CLI flags to tune sampling and sensitivity.
"""

import json
import argparse
from ..phase_00_detect_type.file_type_detector import (
    detect_many,
    DEFAULT_SAMPLE_PAGES,
    DEFAULT_TOPK_IMAGE_PAGES,
    DEFAULT_IMG_AREA_THR,
    DEFAULT_TEXT_LEN_THR,
    DEFAULT_WORDS_THR,
    DEFAULT_BLOCKS_THR,
)

def main():
    ap = argparse.ArgumentParser(description="Improved File Type Detection")
    ap.add_argument("paths", nargs="+", help="File paths")
    ap.add_argument("--sample-pages", type=int, default=DEFAULT_SAMPLE_PAGES)
    ap.add_argument("--topk-image-pages", type=int, default=DEFAULT_TOPK_IMAGE_PAGES)
    ap.add_argument("--img-area-th", type=float, default=DEFAULT_IMG_AREA_THR)
    ap.add_argument("--text-len-th", type=int, default=DEFAULT_TEXT_LEN_THR)
    ap.add_argument("--words-th", type=int, default=DEFAULT_WORDS_THR)
    ap.add_argument("--blocks-th", type=int, default=DEFAULT_BLOCKS_THR)
    args = ap.parse_args()

    res = detect_many(
        args.paths,
        sample_pages=args.sample_pages,
        topk_image_pages=args.topk_image_pages,
        img_area_thr=args.img_area_th,
        text_len_thr=args.text_len_th,
        words_thr=args.words_th,
        blocks_thr=args.blocks_th,
    )
    print(json.dumps([r.to_dict() for r in res], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

