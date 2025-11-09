# PURPOSE:
#   Contract test ensuring merge API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_03_merge.api import run_merge


pytestmark = pytest.mark.contract


def test_merge_api_top_level_versioning_stamp() -> None:
    result = run_merge([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_03_merge_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
