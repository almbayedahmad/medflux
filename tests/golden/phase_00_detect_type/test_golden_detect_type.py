from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests._utils.helpers.golden import assert_json_golden


pytestmark = pytest.mark.golden


def _load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_unified_document_normalized():
    expected_rel = Path("phase_00_detect_type") / "outputs" / "caseA_unified.json"
    expected_abs = Path(__file__).parent / "outputs" / "caseA_unified.json"
    expected = _load_json(expected_abs)
    actual = dict(expected)
    # Change volatile fields; normalization should ignore or mask these
    actual["timestamp"] = "2023-01-01T00:00:00Z"
    actual["uuid"] = "123e4567-e89b-12d3-a456-426614174000"
    assert_json_golden(actual, expected_rel)


def test_golden_stage_stats_normalized():
    expected_rel = Path("phase_00_detect_type") / "outputs" / "caseA_stats.json"
    expected_abs = Path(__file__).parent / "outputs" / "caseA_stats.json"
    expected = _load_json(expected_abs)
    actual = dict(expected)
    actual["timestamp"] = "2023-01-01T00:00:00Z"
    assert_json_golden(actual, expected_rel)
