from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.policy_utils import load_policy_with_overrides


def _load_rules() -> Dict[str, Any]:
    override = (
        os.environ.get("MEDFLUX_VALIDATION_POLICY", "")
        or os.environ.get("MFLUX_VALIDATION_POLICY", "")
    ).strip()
    if override:
        p = Path(override)
        if p.exists():
            # Mimic policy file structure when using a direct override
            import yaml  # type: ignore

            return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    try:
        return load_policy_with_overrides("validation/validation_rules.yaml", section=None)
    except Exception:
        return {}


def demotion_rules() -> Dict[str, Any]:
    rules = _load_rules()
    return rules.get("demotions", {}) if isinstance(rules, dict) else {}


def should_demote(error: Any, rules: Dict[str, Any]) -> bool:
    """Return True if a jsonschema error should be downgraded to a warning.

    Supports rules:
      - by_validator: list of validator names to demote (e.g., ["additionalProperties"]).
      - by_schema_path_contains: list of substrings; if contained in error.schema_path, demote.
    """
    try:
        by_validator: List[str] = list(rules.get("by_validator") or [])
        if error.validator in by_validator:
            return True
        path_str = "/".join(str(x) for x in list(error.schema_path))
        substrs: List[str] = list(rules.get("by_schema_path_contains") or [])
        if any(s in path_str for s in substrs):
            return True
    except Exception:
        return False
    return False
