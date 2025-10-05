import json
import sys
from pathlib import Path

import pytest

from medflux_backend.Preprocessing.pipeline import detect_and_read
from medflux_backend.Preprocessing.phase_02_readers.outputs import readers_output_meta as doc_meta_module
from medflux_backend.Preprocessing.phase_02_readers.schemas.readers_output_schema import SCHEMA_VERSION


_ALLOWED_FILE_TYPES = {"pdf_text", "pdf_scan", "pdf_scan_hybrid", "docx", "image"}
_ALLOWED_LANGS = {"de", "en", "de+en"}
_ALLOWED_COORD_UNITS = {"pdf_points", "docx_emus", "image_pixels", "unknown"}
_PIPELINE_ID = "preprocessing.run_readers"


def _write_summary_payload(path: Path, summary: dict) -> None:
    payload = {"summary": summary}
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

    payload_json = json.loads(doc_meta_path.read_text(encoding="utf-8"))
    assert payload_json["schema_version"] == SCHEMA_VERSION
    assert isinstance(payload_json["run_id"], str)
    assert payload_json["pipeline_id"] == _PIPELINE_ID

    doc_meta_json = payload_json["doc_meta"]
    per_page_stats = payload_json["per_page_stats"]
    text_blocks = payload_json["text_blocks"]
    warnings = payload_json["warnings"]
    logs = payload_json["logs"]
    logs_structured = payload_json.get("logs_structured", [])
    zones_top = payload_json.get("zones", [])

    assert doc_meta_json["file_name"] == sample.name
    assert doc_meta_json["file_type"] in _ALLOWED_FILE_TYPES
    assert doc_meta_json["detected_encodings"] in {None, "utf-8"}
    assert doc_meta_json["timings_ms"]["total_ms"] >= 0
    assert doc_meta_json["coordinate_unit"] in _ALLOWED_COORD_UNITS
    assert doc_meta_json["bbox_origin"] == "bottom-left"
    assert doc_meta_json["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_json["timings_ms"]
    for key in ("readers", "ocr", "lang_detect"):
        assert key in doc_meta_json["timings_ms"]
    assert doc_meta_json["ocr_engine"] in {"tesseract", "none"}
    assert isinstance(doc_meta_json["ocr_engine_version"], str)
    assert isinstance(doc_meta_json["ocr_langs"], str)
    assert isinstance(doc_meta_json["preprocess_applied"], list)
    assert all(isinstance(step, str) for step in doc_meta_json["preprocess_applied"])
    assert isinstance(doc_meta_json["content_hash"], str)
    assert doc_meta_json["content_hash"]
    assert isinstance(doc_meta_json["has_text_layer"], bool)

    assert per_page_stats
    first_page = per_page_stats[0]
    assert first_page["source"] in {"text", "ocr", "mixed"}
    assert first_page["lang"] in _ALLOWED_LANGS
    assert isinstance(first_page["lang_share"], dict)
    assert isinstance(first_page["flags"], list)
    assert isinstance(first_page["rotation_deg"], int)
    assert isinstance(first_page["skew_deg"], float)
    assert isinstance(first_page["page_size"], dict)
    assert {"width", "height"}.issubset(first_page["page_size"].keys())
    assert isinstance(first_page["is_multi_column"], bool)
    assert isinstance(first_page["columns_count"], int)
    assert isinstance(first_page["has_header_footer"], bool)
    assert isinstance(first_page["has_images"], bool)

    assert isinstance(text_blocks, list)
    if text_blocks:
        first_block = text_blocks[0]
        assert isinstance(first_block["text_lines"], list)
        assert isinstance(first_block["ocr_conf_avg"], float)
        assert isinstance(first_block["font_size"], float)
        assert isinstance(first_block["is_bold"], bool)
        assert isinstance(first_block["is_upper"], bool)
        assert isinstance(first_block["paragraph_style"], str)
        assert isinstance(first_block["list_level"], int)

    assert "per_page_stats" not in doc_meta_json
    assert "text_blocks" not in doc_meta_json

    assert isinstance(doc_meta_json["artifacts"], list)
    assert isinstance(doc_meta_json["words"], list)
    if doc_meta_json["words"]:
        first_word = doc_meta_json["words"][0]
        assert {"block_id", "page", "text", "bbox", "ocr_conf"}.issubset(first_word.keys())
        assert isinstance(first_word["bbox"], list)
        assert isinstance(first_word["ocr_conf"], float)

    assert isinstance(logs_structured, list)
    if logs_structured:
        first_structured = logs_structured[0]
        assert {"ts", "stage", "code"}.issubset(first_structured.keys())

    assert isinstance(zones_top, list)
    if zones_top:
        first_zone = zones_top[0]
        assert {"page", "bbox", "type"}.issubset(first_zone.keys())
        assert isinstance(first_zone["bbox"], list)

    detected = doc_meta_json["detected_languages"]
    assert all(isinstance(lang, str) for lang in detected["by_page"])
    assert detected["doc"] in _ALLOWED_LANGS
    assert isinstance(doc_meta_json["locale_hints"]["by_page"], list)
    assert isinstance(doc_meta_json["processing_log"], list)
    assert isinstance(logs, list)
    assert isinstance(warnings, list)
    assert Path(doc_meta_json["text_blocks_path"]).exists()
    assert Path(doc_meta_json["visual_artifacts_path"]).exists()

    table_candidates_path = Path(outdir / sample.stem / "readers" / "table_candidates.jsonl")
    assert table_candidates_path.exists()
    candidates = payload_json.get("table_candidates", [])
    if candidates:
        first_candidate = candidates[0]
        expected_keys = {"page", "bbox", "confidence", "cues", "overlaps_text", "method", "gridlines_h", "gridlines_v", "rotation_deg"}
        assert expected_keys.issubset(first_candidate.keys())


def _baseline_summary(pages: int) -> dict:
    return {
        "page_count": pages,
        "page_decisions": ["native"] * pages,
        "avg_conf": 90.0,
        "text_blocks_count": 0,
        "table_pages": [],
        "lang_per_page": [],
        "locale_per_page": [],
        "timings_ms": {"total_ms": 10.0},
        "warnings": [],
        "tool_log": [],
        "per_page_stats": [],
        "visual_artifacts_count": 0,
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
    payload = doc_meta_module.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
        run_id="unit-test",
        pipeline_id="test.pipeline",
    )
    doc_meta_payload = payload["doc_meta"]
    assert doc_meta_payload["coordinate_unit"] == "pdf_points"
    assert doc_meta_payload["bbox_origin"] == "bottom-left"
    assert doc_meta_payload["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_payload["timings_ms"]
    assert doc_meta_payload["ocr_engine"] == "none"
    assert doc_meta_payload["ocr_engine_version"] == "none"
    assert isinstance(doc_meta_payload["ocr_langs"], str)
    assert isinstance(doc_meta_payload["preprocess_applied"], list)
    assert isinstance(doc_meta_payload["content_hash"], str)
    assert doc_meta_payload["has_text_layer"] is False
    assert doc_meta_payload["detected_languages"]["overall"] == ["de", "en"]
    assert doc_meta_payload["detected_languages"]["by_page"] == ["de+en", "de+en"]
    assert doc_meta_payload["processing_log"] == []
    assert doc_meta_payload["artifacts"] == []
    assert doc_meta_payload["words"] == []
    assert payload.get("zones", []) == []
    assert payload["per_page_stats"] == []


def test_doc_meta_replaces_unknown_page_hints_with_fallback(tmp_path):
    readers_dir = tmp_path / "readers"
    readers_dir.mkdir()
    summary = _baseline_summary(pages=1)
    summary["lang_per_page"] = [{"page": 1, "lang": "unknown"}]
    _write_summary_payload(readers_dir / "readers_summary.json", summary)

    detect_meta = {"file_type": "pdf_text", "lang": "deu+eng"}
    payload = doc_meta_module.build_doc_meta(
        input_path=tmp_path / "sample.pdf",
        detect_meta=detect_meta,
        encoding_meta=_baseline_encoding_meta(),
        readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": []},
        timings=_baseline_timings(),
        run_id="unit-test",
        pipeline_id="test.pipeline",
    )
    doc_meta_payload = payload["doc_meta"]
    assert doc_meta_payload["coordinate_unit"] == "pdf_points"
    assert doc_meta_payload["bbox_origin"] == "bottom-left"
    assert doc_meta_payload["pdf_locked"] is False
    assert "table_detect_light" in doc_meta_payload["timings_ms"]
    assert doc_meta_payload["ocr_engine"] == "none"
    assert doc_meta_payload["ocr_engine_version"] == "none"
    assert isinstance(doc_meta_payload["ocr_langs"], str)
    assert isinstance(doc_meta_payload["preprocess_applied"], list)
    assert isinstance(doc_meta_payload["content_hash"], str)
    assert doc_meta_payload["has_text_layer"] is False
    assert doc_meta_payload["detected_languages"]["overall"] == ["de", "en"]
    assert doc_meta_payload["detected_languages"]["by_page"] == ["de+en"]
    assert payload["warnings"] == []
    assert doc_meta_payload["words"] == []
    assert payload.get("zones", []) == []
