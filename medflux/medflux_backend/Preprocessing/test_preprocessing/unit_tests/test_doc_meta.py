import json
import sys
from pathlib import Path

import pytest

from medflux_backend.Preprocessing.pipeline import detect_and_read


@pytest.mark.parametrize("payload", ["hello world", "quick brown fox"])
def test_doc_meta_written(tmp_path, payload):
    sample = tmp_path / "sample.txt"
    sample.write_text(payload, encoding="utf-8")

    outdir = tmp_path / "run"
    argv_backup = sys.argv[:]
    sys.argv = ["detect_and_read", str(sample), "--outdir", str(outdir)]
    try:
        detect_and_read.main()
    finally:
        sys.argv = argv_backup

    doc_meta_path = outdir / sample.stem / "doc_meta.json"
    assert doc_meta_path.exists()

    doc_meta = json.loads(doc_meta_path.read_text(encoding="utf-8"))
    assert doc_meta["file_name"] == sample.name
    assert doc_meta["file_type"] in {"txt", "pdf_text", "docx", "pdf_scan", "pdf_scan_hybrid", "image"}
    assert doc_meta["timings_ms"]["detect"] is not None
    assert doc_meta["detected_encodings"]["primary"] in {"utf-8", None}
    text_blocks_file = (outdir / sample.stem / doc_meta["text_blocks_path"]).resolve()
    assert text_blocks_file.exists()
    assert doc_meta["text_blocks_count"] >= 1
    tables_raw_file = (outdir / sample.stem / doc_meta["tables_raw_path"]).resolve()
    assert tables_raw_file.exists()
    assert doc_meta["tables_raw_count"] >= 0
