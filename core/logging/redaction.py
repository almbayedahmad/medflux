from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List
import hashlib

from core.policy_utils import load_policy_with_overrides


class RedactionFilter(logging.Filter):
    """Redact sensitive values by key and by regex patterns.

    Controlled by policy file `observability/redaction_rules.yaml` and env `MEDFLUX_LOG_REDACTION`.
    """

    _rules_loaded = False
    _keys: List[str] = []
    _patterns: List[re.Pattern[str]] = []
    _replacement: str = "[REDACTED]"
    _never: List[str] = []
    _hash_keys: List[str] = []

    def __init__(self) -> None:
        super().__init__()
        if not RedactionFilter._rules_loaded:
            self._load_rules()

    @classmethod
    def _load_rules(cls) -> None:
        try:
            policy = load_policy_with_overrides("observability/logging/redaction_rules.yaml")
            data: Dict[str, Any] = policy if isinstance(policy, dict) else {}
            cls._keys = [str(k).lower() for k in (data.get("keys") or [])]
            cls._patterns = [re.compile(p) for p in (data.get("patterns") or [])]
            cls._replacement = str(data.get("replacement") or "[REDACTED]")
            cls._never = [str(k).lower() for k in (data.get("never") or [])]
            cls._hash_keys = [str(k).lower() for k in (data.get("hash_keys") or [])]
        except Exception:
            cls._keys = []
            cls._patterns = []
            cls._replacement = "[REDACTED]"
            cls._never = []
            cls._hash_keys = []
        cls._rules_loaded = True

    def _redact_value(self, key: str, value: Any) -> Any:
        if value is None:
            return value
        kl = key.lower()
        if kl in RedactionFilter._never:
            return value
        if kl in RedactionFilter._hash_keys:
            try:
                salt = os.environ.get("MEDFLUX_LOG_HASH_SALT", "")
                h = hashlib.sha256((salt + str(value)).encode("utf-8", errors="ignore")).hexdigest()
                return h
            except Exception:
                return RedactionFilter._replacement
        if kl in RedactionFilter._keys:
            return RedactionFilter._replacement
        if isinstance(value, str):
            text = value
            for pat in RedactionFilter._patterns:
                try:
                    text = pat.sub(RedactionFilter._replacement, text)
                except Exception:
                    continue
            return text
        return value

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if os.environ.get("MEDFLUX_LOG_REDACTION", "1") not in {"", "0", "false", "False"}:
            # scrub message
            try:
                if isinstance(record.msg, str):
                    record.msg = self._redact_value("message", record.msg)
            except Exception:
                pass
            # scrub extras
            try:
                items = list(record.__dict__.items())
                for k, v in items:
                    if k.startswith("_"):
                        continue
                    nv = self._redact_value(k, v)
                    if nv is not v:
                        record.__dict__[k] = nv
            except Exception:
                pass
        return True
