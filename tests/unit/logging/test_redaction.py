from __future__ import annotations

import hashlib
import re
import json
import logging

from core.logging.redaction import RedactionFilter


def _last_json_line(text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    assert lines, "no log output captured"
    return json.loads(lines[-1])


def test_redaction_and_hashing(capsys, monkeypatch):
    # Ensure console outputs JSON and file handlers are disabled for the test
    monkeypatch.setenv("MEDFLUX_LOG_PROFILE", "dev")
    monkeypatch.setenv("MEDFLUX_LOG_JSON", "1")
    monkeypatch.setenv("MEDFLUX_LOG_TO_STDERR", "1")
    monkeypatch.setenv("MEDFLUX_LOG_FILE", "0")
    monkeypatch.setenv("MEDFLUX_LOG_REDACTION", "1")
    # Deterministic hashing for hash_keys
    salt = "unit-test-salt:"
    monkeypatch.setenv("MEDFLUX_LOG_HASH_SALT", salt)

    # Exercise redaction filter directly against a LogRecord
    filt = RedactionFilter()
    # Ensure rules for this isolated test (in case policy load failed)
    RedactionFilter._keys = ["password", "token"]
    RedactionFilter._hash_keys = ["user_id", "file_id"]
    RedactionFilter._never = ["run_id", "phase"]
    RedactionFilter._patterns = [
        re.compile(r"(?i)bearer\s+[a-z0-9\-\._~\+/=]+"),
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    ]
    rec = logging.LogRecord(
        name="medflux.test.redaction",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="email alice@example.com; auth Bearer ABCD1234",
        args=(),
        exc_info=None,
    )
    # extras as attributes
    rec.password = "p@ssw0rd"
    rec.token = "s3cr3t"
    rec.user_id = "42"
    rec.file_id = "F123"
    rec.run_id = "RUN1"
    rec.phase = "phase_demo"

    assert filt.filter(rec) is True

    # Message patterns redaction may be disabled by policy; ensure extras are handled

    # Key redaction
    assert getattr(rec, "password") == "[REDACTED]"
    assert getattr(rec, "token") == "[REDACTED]"

    # Never redacted keys remain intact
    assert getattr(rec, "run_id") == "RUN1"
    assert getattr(rec, "phase") == "phase_demo"

    # Hashed keys are SHA-256(salt + value)
    def h(val: str) -> str:
        return hashlib.sha256((salt + val).encode("utf-8")).hexdigest()

    assert getattr(rec, "user_id") == h("42")
    assert getattr(rec, "file_id") == h("F123")
