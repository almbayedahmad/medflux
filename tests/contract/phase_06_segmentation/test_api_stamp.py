# PURPOSE:
#   Contract test ensuring segmentation API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_06_segmentation.api import run_segmentation


pytestmark = pytest.mark.contract


def test_segmentation_api_top_level_versioning_stamp() -> None:
    result = run_segmentation([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_06_segmentation_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
