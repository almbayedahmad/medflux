from __future__ import annotations

import json
import os

from core.versioning import get_version, get_version_info, make_artifact_stamp


def test_get_version_and_info_env_overrides(monkeypatch):
    monkeypatch.setenv("BUILD_GIT_SHA", "abcdef123456")
    monkeypatch.setenv("BUILD_NUMBER", "42")
    monkeypatch.setenv("BUILD_DATE", "2025-01-01")
    info = get_version_info()
    assert info["version"] == get_version()
    assert info["git_sha"] == "abcdef1"
    assert info["build_number"] == "42"
    assert info["build_date"] == "2025-01-01"


def test_make_artifact_stamp_includes_schema_version():
    stamp = make_artifact_stamp(schema_name="stage_contract")
    # Basic structure
    assert "versioning" in stamp
    v = stamp["versioning"]
    assert v.get("app_version") == get_version()
    assert v.get("schema_name") == "stage_contract"
    # schema version must be present and look like semver-ish
    sv = v.get("schema_version")
    assert isinstance(sv, str) and "." in sv
