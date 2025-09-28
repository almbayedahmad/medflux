import json
import sys
from pathlib import Path

import pytest

from medflux_backend.Preprocessing.pipeline import detect_and_read
from medflux_backend.Preprocessing.output_structure.readers_outputs import builder


def _write_summary_payload(path: Path, summary: dict) -> None:
    payload = {
        "summary": summary,
        "qa": summary.get("qa", {}),
        "flags": summary.get("flags", {}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    assert doc_meta["detected_encodings"] in {None, "utf-8"}
    assert doc_meta["timings_ms"]["total_ms"] >= 0
    assert doc_meta["per_page_stats"]
    assert isinstance(doc_meta["text_blocks"], list)
    assert isinstance(doc_meta["tables_raw"], list)
    assert isinstance(doc_meta["artifacts"], list)
    assert doc_meta["detected_languages"]["by_page"]
    assert doc_meta["locale_hints"]["by_page"]
    assert "qa" in doc_meta
    assert isinstance(doc_meta["qa"]["warnings"], list)
    assert isinstance(doc_meta["processing_log"], list)
    assert isinstance(doc_meta["logs"], list)
    assert Path(doc_meta["text_blocks_path"]).exists()
    assert Path(doc_meta["tables_raw_path"]).exists()
    assert Path(doc_meta["visual_artifacts_path"]).exists()


def _baseline_summary(pages: int) -> dict:
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
        "per_page_stats": [],
        "visual_artifacts_count": 0,
        "qa": {"needs_review": False, "low_conf_pages": [], "low_text_pages": [], "tables_fail": False, "reasons": []},
        "flags": {"manual_review": False, "pages": []},
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
        "cleaning": 0.0,
        "normalization": 0.0,
        "segmentation": 0.0,
        "merge": 0.0,
    }


def test_doc_meta_falls_back_to_decision_language(tmp_path):
    readers_dir = tmp_path / "readers"
    readers_dir.mkdir()
    summary = _baseline_summary(pages=2)
    _write_summary_payload(readers_dir / "readers_summary.json", summary)

    detect_meta = {"file_type": "pdf_text", "lang": "deu+eng"}
    doc_meta = builder.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
    )

    assert doc_meta["detected_languages"]["overall"] == ["de", "en"]
    assert all(entry["languages"] == ["de", "en"] for entry in doc_meta["detected_languages"]["by_page"] or [])
    assert doc_meta["qa"]["needs_review"] is False
    assert doc_meta["processing_log"] == []
    assert doc_meta["artifacts"] == []
    assert doc_meta["per_page_stats"] == []


def test_doc_meta_replaces_unknown_page_hints_with_fallback(tmp_path):
    readers_dir = tmp_path / "readers"
    readers_dir.mkdir()
    summary = _baseline_summary(pages=1)
    summary["lang_per_page"] = [{"page": 1, "lang": "unknown"}]
    _write_summary_payload(readers_dir / "readers_summary.json", summary)

    detect_meta = {"file_type": "pdf_text", "lang": "deu+eng"}
    doc_meta = builder.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
    )

    assert doc_meta["detected_languages"]["overall"] == ["de", "en"]
    assert doc_meta["detected_languages"]["by_page"][0]["languages"] == ["de", "en"]
    assert doc_meta["qa"]["needs_review"] is False
    assert doc_meta["warnings"] == []
