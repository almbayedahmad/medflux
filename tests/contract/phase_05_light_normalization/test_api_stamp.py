# PURPOSE:
#   Contract test ensuring light_normalization API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_05_light_normalization.api import run_light_normalization


pytestmark = pytest.mark.contract


def test_light_normalization_api_top_level_versioning_stamp() -> None:
    result = run_light_normalization([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_05_light_normalization_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
