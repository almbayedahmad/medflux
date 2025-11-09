# PURPOSE:
#   Contract test ensuring provenance API stamps versioning with schema info.
# OUTCOME:
#   Validates top-level result contains schema_name/version matching registry.

from __future__ import annotations

import pytest

from backend.Preprocessing.phase_09_provenance.api import run_provenance


pytestmark = pytest.mark.contract


def test_provenance_api_top_level_versioning_stamp() -> None:
    result = run_provenance([])
    assert "versioning" in result
    v = result["versioning"]
    assert v.get("schema_name") == "phase_09_provenance_output"
    assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
