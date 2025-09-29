import json
import sys
from pathlib import Path

import pytest

from medflux_backend.Preprocessing.pipeline import detect_and_read
from medflux_backend.Preprocessing.output_structure.readers_outputs import doc_meta as doc_meta_module


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

    doc_meta_json = json.loads(doc_meta_path.read_text(encoding="utf-8"))
    assert doc_meta_json["file_name"] == sample.name
    assert doc_meta_json["file_type"] in {"txt", "pdf_text", "docx", "pdf_scan", "pdf_scan_hybrid", "image"}
    assert doc_meta_json["detected_encodings"] in {None, "utf-8"}
    assert doc_meta_json["timings_ms"]["total_ms"] >= 0
    assert doc_meta_json["coordinate_unit"] == "points"
    assert doc_meta_json["bbox_origin"] == "top-left"
    assert doc_meta_json["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_json["timings_ms"]
    assert doc_meta_json["ocr_engine"] in {"tesseract", "none"}
    assert isinstance(doc_meta_json["ocr_engine_version"], (str, type(None)))
    assert doc_meta_json["ocr_langs"] or doc_meta_json["ocr_engine"] == "none"
    assert isinstance(doc_meta_json["preprocess_applied"], list)
    assert isinstance(doc_meta_json["content_hash"], str)
    assert isinstance(doc_meta_json["has_text_layer"], bool)
    assert doc_meta_json["per_page_stats"]
    first_page = doc_meta_json["per_page_stats"][0]
    assert first_page["source"] in {"text", "ocr", "mixed"}
    if first_page["source"] == "ocr":
        assert "ocr_conf" in first_page
    page_size = first_page.get("page_size")
    if page_size:
        assert "width" in page_size and "height" in page_size
    if "rotation_deg" in first_page:
        assert isinstance(first_page["rotation_deg"], (int, float))
    assert isinstance(first_page.get("is_multi_column"), bool)
    assert isinstance(doc_meta_json["text_blocks"], list)
    if doc_meta_json["text_blocks"]:
        first_block = doc_meta_json["text_blocks"][0]
        assert isinstance(first_block.get("text_lines"), list)
        assert "font_size" in first_block or first_block.get("font_size") is None
        assert "paragraph_style" in first_block
        assert "list_level" in first_block
        assert "charmap_ref" in first_block
    assert isinstance(doc_meta_json["tables_raw"], list)
    assert isinstance(doc_meta_json["artifacts"], list)
    assert doc_meta_json["detected_languages"]["by_page"]
    assert doc_meta_json["locale_hints"]["by_page"]
    assert "qa" in doc_meta_json
    assert isinstance(doc_meta_json["qa"]["warnings"], list)
    assert isinstance(doc_meta_json["processing_log"], list)
    assert isinstance(doc_meta_json["logs"], list)
    assert doc_meta_json["ocr_engine"] in {"tesseract", "none"}
    assert isinstance(doc_meta_json["ocr_engine_version"], (str, type(None)))
    assert isinstance(doc_meta_json["ocr_langs"], str)
    assert "dpi_" in doc_meta_json["preprocess_applied"][0] if doc_meta_json["preprocess_applied"] else True
    assert isinstance(doc_meta_json["content_hash"], str) and doc_meta_json["content_hash"]
    assert isinstance(doc_meta_json["has_text_layer"], bool)
    assert Path(doc_meta_json["text_blocks_path"]).exists()
    assert Path(doc_meta_json["tables_raw_path"]).exists()
    assert Path(doc_meta_json["visual_artifacts_path"]).exists()


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
    doc_meta_payload = doc_meta_module.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
    )
    assert doc_meta_payload["coordinate_unit"] == "points"
    assert doc_meta_payload["bbox_origin"] == "top-left"
    assert doc_meta_payload["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_payload["timings_ms"]
    assert doc_meta_payload["ocr_engine"] == "none"
    assert doc_meta_payload["ocr_engine_version"] is None
    assert isinstance(doc_meta_payload["ocr_langs"], str)
    assert isinstance(doc_meta_payload["preprocess_applied"], list)
    assert isinstance(doc_meta_payload["content_hash"], str)
    assert doc_meta_payload["has_text_layer"] is False
    assert doc_meta_payload["detected_languages"]["overall"] == ["de", "en"]
    assert all(entry["languages"] == ["de", "en"] for entry in doc_meta_payload["detected_languages"]["by_page"] or [])
    assert doc_meta_payload["qa"]["needs_review"] is False
    assert doc_meta_payload["processing_log"] == []
    assert doc_meta_payload["artifacts"] == []
    assert doc_meta_payload["per_page_stats"] == []


def test_doc_meta_replaces_unknown_page_hints_with_fallback(tmp_path):
    readers_dir = tmp_path / "readers"
    readers_dir.mkdir()
    summary = _baseline_summary(pages=1)
    summary["lang_per_page"] = [{"page": 1, "lang": "unknown"}]
    _write_summary_payload(readers_dir / "readers_summary.json", summary)

    detect_meta = {"file_type": "pdf_text", "lang": "deu+eng"}
    doc_meta_payload = doc_meta_module.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
    )
    assert doc_meta_payload["coordinate_unit"] == "points"
    assert doc_meta_payload["bbox_origin"] == "top-left"
    assert doc_meta_payload["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_payload["timings_ms"]
    assert doc_meta_payload["ocr_engine"] == "none"
    assert doc_meta_payload["ocr_engine_version"] is None
    assert isinstance(doc_meta_payload["ocr_langs"], str)
    assert isinstance(doc_meta_payload["preprocess_applied"], list)
    assert isinstance(doc_meta_payload["content_hash"], str)
    assert doc_meta_payload["has_text_layer"] is False
    assert doc_meta_payload["detected_languages"]["overall"] == ["de", "en"]
    assert doc_meta_payload["detected_languages"]["by_page"][0]["languages"] == ["de", "en"]
    assert doc_meta_payload["qa"]["needs_review"] is False
    assert doc_meta_payload["warnings"] == []
