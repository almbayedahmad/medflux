from __future__ import annotations

import json
from pathlib import Path

from core.cli.medflux import main as medflux_main


def _run(argv: list[str]) -> str:
    import io
    import sys

    old = sys.stdout
    buf = io.StringIO()
    try:
        sys.stdout = buf
        rc = medflux_main(argv)
        assert rc == 0
        return buf.getvalue()
    finally:
        sys.stdout = old


def test_phase_list_prints_json() -> None:
    out = _run(["phase-list"])
    data = json.loads(out)
    assert isinstance(data, dict)
    assert "phases" in data
    assert any(p.startswith("phase_") for p in data.get("phases", []))


def test_phase_detect_runs_with_temp_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")
    out = _run([
        "phase-detect",
        "--inputs",
        str(sample),
        "--output-root",
        str(tmp_path / "out"),
    ])
    data = json.loads(out)
    assert data.get("phase") == "phase_00_detect_type"


def test_phase_encoding_runs_with_temp_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hallo", encoding="iso-8859-1")
    out = _run([
        "phase-encoding",
        "--inputs",
        str(sample),
        "--output-root",
        str(tmp_path / "out"),
    ])
    data = json.loads(out)
    assert data.get("phase") == "phase_01_encoding"


def test_phase_readers_runs_with_temp_text(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("simple text content", encoding="utf-8")
    out = _run([
        "phase-readers",
        "--inputs",
        str(sample),
        "--output-root",
        str(tmp_path / "out"),
    ])
    data = json.loads(out)
    assert data.get("phase") == "phase_02_readers"
