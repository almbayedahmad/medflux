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
    assert doc_meta["detected_languages"]["by_page"]
    assert doc_meta["locale_hints"]["by_page"]
    assert "qa" in doc_meta
    assert isinstance(doc_meta["qa"]["warnings"], list)
    assert "processing_log" in doc_meta
    assert isinstance(doc_meta["processing_log"], list)
    artifacts_file = (outdir / sample.stem / doc_meta["visual_artifacts_path"]).resolve()
    assert artifacts_file.exists()
    assert doc_meta["visual_artifacts_count"] >= 0
    assert doc_meta.get("per_page_stats")
    assert "chars" in doc_meta["per_page_stats"][0]


def _baseline_reader_summary(pages: int) -> dict:
    return {
        "page_count": pages,
        "page_decisions": ["native"] * pages,
        "avg_conf": 90.0,
        "text_blocks_count": 0,
        "tables_raw_count": 0,
        "table_pages": [],
        "lang_per_page": [],
        "locale_per_page": [],
        "timings_ms": {"total_ms": 10.0},
        "warnings": [],
        "tool_log": [],
        "qa_flags": {"manual_review": False, "pages": []},
        "per_page_stats": [],
        "thresholds": {},
    }


def _baseline_encoding_meta() -> dict:
    return {
        "primary": None,
        "confidence": None,
        "bom": False,
        "is_utf8": None,
        "sample_len": 0,
    }


def _baseline_timings() -> dict:
    return {
        "detect": 1.0,
        "encoding": 0.5,
        "readers": 2.0,
        "cleaning": None,
        "normalization": None,
        "segmentation": None,
        "merge": None,
    }


def test_doc_meta_falls_back_to_decision_language(tmp_path):
    summary = _baseline_reader_summary(pages=2)
    doc_meta = detect_and_read.assemble_doc_meta(
        input_path=tmp_path / 'sample.pdf',
        detect_meta={"file_type": "pdf_text"},
        decision={"lang": "deu+eng"},
        encoding_meta=_baseline_encoding_meta(),
        reader_summary=summary,
        timings_ms=_baseline_timings(),
    )

    assert doc_meta["detected_languages"]["overall"] == ["de", "en"]
    for entry in doc_meta["detected_languages"]["by_page"]:
        assert entry["languages"] == ["de", "en"]
    assert doc_meta["qa"]["needs_review"] is False
    assert doc_meta["processing_log"] == []
    assert doc_meta["visual_artifacts_count"] == 0
    assert doc_meta.get("per_page_stats") == []


def test_doc_meta_replaces_unknown_page_hints_with_fallback(tmp_path):
    summary = _baseline_reader_summary(pages=1)
    summary["lang_per_page"] = [{"page": 1, "lang": "unknown"}]
    doc_meta = detect_and_read.assemble_doc_meta(
        input_path=tmp_path / 'sample.pdf',
        detect_meta={"file_type": "pdf_text"},
        decision={"lang": "deu+eng"},
        encoding_meta=_baseline_encoding_meta(),
        reader_summary=summary,
        timings_ms=_baseline_timings(),
    )

    assert doc_meta["detected_languages"]["overall"] == ["de", "en"]
    assert doc_meta["detected_languages"]["by_page"][0]["languages"] == ["de", "en"]
    assert doc_meta["qa"]["needs_review"] is False
    assert doc_meta["processing_log"] == []
    assert doc_meta["visual_artifacts_count"] == 0
    assert doc_meta.get("per_page_stats") == []


def test_split_lang_field_aliases():
    assert detect_and_read._split_lang_field('deu+eng') == ['de', 'en']
    assert detect_and_read._split_lang_field(['english', 'de']) == ['en', 'de']
    assert detect_and_read._split_lang_field('') == []
