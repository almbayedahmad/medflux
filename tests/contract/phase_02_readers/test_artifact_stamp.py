# PURPOSE:
#   Contract tests for readers artifacts stamping.
# OUTCOME:
#   Ensures doc_meta, stage_stats, and summary artifacts include versioning
#   with expected schema names and versions.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.Preprocessing.phase_02_readers.io.writer import (
    save_readers_doc_meta,
    save_readers_stage_stats,
    save_readers_summary,
)


pytestmark = pytest.mark.contract


def test_readers_writers_stamp_versioning(tmp_path: Path) -> None:
    doc_path = tmp_path / "readers_doc_meta.json"
    stats_path = tmp_path / "readers_stage_stats.json"
    summary_path = tmp_path / "readers_summary.json"

    save_readers_doc_meta({"documents": []}, doc_path)
    save_readers_stage_stats({"stage": "readers"}, stats_path)
    save_readers_summary({"warnings": []}, summary_path)

    cases = [
        (doc_path, "readers_doc_meta"),
        (stats_path, "readers_stage_stats"),
        (summary_path, "readers_summary"),
    ]
    for p, expected_name in cases:
        data = json.loads(p.read_text(encoding="utf-8"))
        assert "versioning" in data
        v = data["versioning"]
        assert v.get("schema_name") == expected_name
        assert isinstance(v.get("schema_version"), str) and "." in v["schema_version"]
