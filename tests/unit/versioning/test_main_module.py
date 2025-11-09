from __future__ import annotations

import json
import logging

import pytest

from core.versioning.__main__ import main


@pytest.mark.unit
def test_version_main_emits_json_log(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    main()
    # Find the latest record containing a JSON object with a 'version' key
    msg = None
    for rec in caplog.records:
        text = rec.getMessage()
        if '"version"' in text:
            msg = text
    assert msg, "No version JSON log emitted"
    data = json.loads(msg)
    assert isinstance(data.get("version"), str)
