from __future__ import annotations

import io
import json
import sys

import pytest

from core.versioning.__main__ import main


@pytest.mark.unit
def test_version_main_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert isinstance(data.get("version"), str)
