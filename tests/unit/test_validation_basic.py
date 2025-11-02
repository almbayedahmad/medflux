from __future__ import annotations

import pytest

from core.validation import validate_input, validate_output, ValidationError


def _run_id() -> str:
    # Matches core.validation.formats _RUN_ID_RE
    return "20250101T000000-deadbeef"


@pytest.mark.unit
def test_validate_input_detect_type_ok() -> None:
    payload = {"run_id": _run_id(), "items": [{"path": "file.txt"}]}
    validate_input("phase_00_detect_type", payload)


@pytest.mark.unit
def test_validate_input_detect_type_fail() -> None:
    # Missing required 'items'
    payload = {"run_id": _run_id()}
    with pytest.raises(ValidationError):
        validate_input("phase_00_detect_type", payload)


@pytest.mark.unit
def test_validate_output_detect_type_ok() -> None:
    payload = {
        "run_id": _run_id(),
        "unified_document": {
            "stage": "detect_type",
            "items": [],
            "source": {"items_received": 1, "items_included": 1},
        },
        "stage_stats": {"stage": "detect_type", "total_items": 0},
        "versioning": {"app_version": "0.0.0"},
    }
    validate_output("phase_00_detect_type", payload)


@pytest.mark.unit
def test_validate_output_detect_type_missing_versioning() -> None:
    payload = {
        "run_id": _run_id(),
        "unified_document": {
            "stage": "detect_type",
            "items": [],
            "source": {"items_received": 1, "items_included": 1},
        },
        "stage_stats": {"stage": "detect_type", "total_items": 1},
    }
    with pytest.raises(ValidationError):
        validate_output("phase_00_detect_type", payload)
