from __future__ import annotations

from pathlib import Path

from medflux_backend.Preprocessing.phase_01_encoding.pipeline_workflow.encoding_pipeline import (
    run_encoding_pipeline,
)


def test_encoding_pipeline_detect_only(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hallo", encoding="iso-8859-1")

    payload = run_encoding_pipeline(
        generic_items=[{"path": str(sample)}],
        config_overrides={
            "io": {
                "out_doc_path": str(tmp_path / "doc.json"),
                "out_stats_path": str(tmp_path / "stats.json"),
            },
            "normalization": {"enabled": False},
        },
    )

    doc_items = payload["unified_document"]["items"]
    assert doc_items, "expected at least one item"
    assert doc_items[0]["detection"]["encoding"]


def test_encoding_pipeline_with_normalization(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("Grüße", encoding="latin-1")

    out_dir = tmp_path / "normalized"

    payload = run_encoding_pipeline(
        generic_items=[{"path": str(sample), "normalize": True}],
        config_overrides={
            "io": {
                "out_doc_path": str(tmp_path / "doc.json"),
                "out_stats_path": str(tmp_path / "stats.json"),
            },
            "normalization": {
                "enabled": True,
                "out_dir": str(out_dir),
                "newline_policy": "lf",
                "errors": "replace",
            },
        },
    )

    doc_items = payload["unified_document"]["items"]
    norm = doc_items[0].get("normalization")
    assert norm and norm["ok"]
    assert Path(norm["normalized_path"]).exists()
