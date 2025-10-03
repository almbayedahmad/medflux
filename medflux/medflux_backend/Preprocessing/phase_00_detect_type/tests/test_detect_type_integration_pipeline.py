from __future__ import annotations

from pathlib import Path

from medflux_backend.Preprocessing.phase_00_detect_type.pipeline_workflow.detect_type_pipeline import (
    run_detect_type_pipeline,
)


def test_detect_type_integration_pipeline(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.txt"
    sample_path.write_text("hello", encoding="utf-8")

    out_doc = tmp_path / "doc.json"
    out_stats = tmp_path / "stats.json"

    payload = run_detect_type_pipeline(
        generic_items=[{"path": str(sample_path)}],
        config_overrides={
            "io": {
                "out_doc_path": str(out_doc),
                "out_stats_path": str(out_stats),
            }
        },
    )

    assert payload["unified_document"]["items"], "expected at least one detection entry"
    assert out_doc.exists()
    assert out_stats.exists()
