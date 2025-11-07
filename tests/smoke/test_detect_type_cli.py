from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.smoke
def test_detect_type_cli_on_sample(tmp_path: Path) -> None:
    samples = Path("samples")
    sample = samples / "hello.txt"
    if not sample.exists():
        pytest.skip("sample file not found")

    env = os.environ.copy()
    env.setdefault("PYTHONPATH", ".")
    # Prefer JSON logs to keep stderr tidy
    env.setdefault("MEDFLUX_LOG_FORMAT", "json")
    env["MEDFLUX_LOG_TO_STDERR"] = "1"
    cmd = [
        sys.executable,
        "-m",
        "backend.Preprocessing.phase_00_detect_type.pipeline_workflow.detect_type_cli",
        str(sample),
        "--log-level",
        "INFO",
        "--log-json",
        "--log-stderr",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
    out = proc.stdout.strip()
    assert out, "no JSON output captured from CLI"
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # Fallback: extract the last JSON object from stdout (in case logs leaked to stdout)
        lines = out.splitlines()
        data = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].lstrip().startswith("{"):
                candidate = "\n".join(lines[i:])
                try:
                    data = json.loads(candidate)
                    break
                except json.JSONDecodeError:
                    continue
        assert data is not None, f"Failed to parse JSON output. stdout was:\n{out}"
    # Minimal shape assertions
    assert isinstance(data, dict)
    assert data.get("run_id")
    assert data.get("unified_document")
    assert data.get("stage_stats")
    assert data.get("versioning")
