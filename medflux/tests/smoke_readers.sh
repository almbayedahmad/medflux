#!/usr/bin/env bash
set -e

python run_readers.py --input samples/Sample_pdftext.pdf --out out/json1
python run_readers.py --input samples/sample_pdfscanned.pdf --out out/json2
python run_readers.py --input samples/Sample_pdfmixed.pdf --out out/json3
python run_readers.py --input samples/demo_vertrag.docx --out out/json4
python run_readers.py --input samples/image_page.png --out out/json5
