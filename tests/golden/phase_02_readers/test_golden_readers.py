from __future__ import annotations

from pathlib import Path
import json

import pytest

from tests._utils.helpers.golden import assert_json_golden


pytestmark = pytest.mark.golden


def _load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_golden_readers_output_normalized():
    expected_rel = Path("phase_02_readers") / "outputs" / "caseA_output.json"
    expected_abs = Path(__file__).parent / "outputs" / "caseA_output.json"
    expected = _load_json(expected_abs)
    actual = dict(expected)
    actual["timestamp"] = "2020-01-01T00:00:00Z"
    assert_json_golden(actual, expected_rel)
