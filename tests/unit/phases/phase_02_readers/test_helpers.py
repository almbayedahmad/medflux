from __future__ import annotations

from backend.Preprocessing.phase_02_readers.domain.ops.readers_core_params import (
    compute_readers_params,
    get_readers_options,
)
from core.preprocessing.services.readers import ReadersService


def test_compute_readers_params_promotes_mixed_mode_for_low_conf_pdf() -> None:
    detect_meta = {
        "detected_mode": "native",
        "file_type": "pdf_text",
        "confidence": 0.5,
        "lang": "deu+eng",
        "dpi": 200,
        "psm": 4,
        "tables_mode": "light",
    }
    config_options = {
        "mode": "native",
        "lang": "deu+eng",
        "dpi": 300,
        "psm": 6,
        "tables_mode": "detect",
        "blocks_threshold": 3,
    }
    params = compute_readers_params(detect_meta, config_options)
    assert params["mode"] == "mixed"
    assert params["lang"] == "deu+eng"
    assert params["dpi"] == 200
    assert params["psm"] == 4


def test_get_readers_options_builds_reader_options_instance() -> None:
    params = {
        "mode": "mixed",
        "lang": "deu+eng",
        "dpi": 400,
        "psm": 5,
        "tables_mode": "full",
        "blocks_threshold": 2,
    }
    config_options = {
        "oem": 1,
        "workers": 2,
        "use_pre": False,
        "export_xlsx": False,
        "verbose": False,
        "save_table_crops": False,
        "tables_min_words": 8,
        "table_detect_min_area": 8000.0,
        "table_detect_max_cells": 300,
        "native_ocr_overlay": True,
        "overlay_area_thr": 0.25,
        "overlay_min_images": 2,
        "overlay_if_any_image": True,
    }
    overrides = {"workers": 6, "export_xlsx": True}
    options = get_readers_options(params, config_options, overrides)
    assert options.mode == "mixed"
    assert options.tables_mode == "extract"
    assert options.blocks_threshold == 2
    assert options.workers == 6
    assert options.export_xlsx is True
    assert options.native_ocr_overlay is True


def test_compute_readers_run_metadata_uses_override_pipeline() -> None:
    run_meta = ReadersService.compute_run_metadata(pipeline_id="custom.pipeline")
    assert run_meta["pipeline_id"] == "custom.pipeline"
    assert run_meta["run_id"].startswith("readers-")
