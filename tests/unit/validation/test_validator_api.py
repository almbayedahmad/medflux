from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pytest

from core.validation.validator import validate_input, validate_output, ValidationError


@pytest.mark.unit
def test_validate_input_ok() -> None:
    payload = {"run_id": "20250101T120000-deadbeef", "items": [{"path": "a.txt"}]}
    validate_input("phase_00_detect_type", payload)


@pytest.mark.unit
def test_validate_input_dryrun_logs(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("MEDFLUX_VALIDATION_DRYRUN", "1")
    payload = {"run_id": "", "items": []}  # invalid
    validate_input("phase_00_detect_type", payload)
    recs = [r for r in caplog.records if r.name == "medflux.validation" and getattr(r, "code", "") == "VL-W001"]
    assert recs, "expected dry-run warning VL-W001"


@pytest.mark.unit
def test_validate_output_ok() -> None:
    doc = {
        "run_id": "20250101T120000-deadbeef",
        "unified_document": {
            "stage": "detect_type",
            "items": [],
            "source": {"items_received": 0, "items_included": 0},
            "errors": []
        },
        "stage_stats": {
            "stage": "detect_type",
            "total_items": 0,
            "items_received": 0,
            "items_included": 0,
            "items_skipped": 0
        },
        "versioning": {"app_version": "0.1.0"}
    }
    validate_output("phase_00_detect_type", doc)


@pytest.mark.unit
def test_validate_output_soft(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    doc = json.loads(Path("outputs/detect_type_unified_document.json").read_text(encoding="utf-8"))
    # Remove a required key to trigger errors, but soft=True downgrades to warning
    doc.pop("unified_document", None)
    validate_output("phase_00_detect_type", doc, soft=True)
    assert any(r for r in caplog.records if r.name == "medflux.validation" and r.levelno >= logging.WARNING)
