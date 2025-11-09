# PURPOSE:
#   Contract test ensuring offsets API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_10_offsets.api import run_offsets


pytestmark = pytest.mark.contract


def test_offsets_api_top_level_versioning_stamp() -> None:
    result = run_offsets([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_10_offsets_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
