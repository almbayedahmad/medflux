from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from core.policy_utils import load_policy_with_overrides


@dataclass
class ValidationIssue:
    scope: str  # e.g., 'config', 'input', 'output'
    path: str   # dot path or identifier
    message: str


class ValidationEngine:
    """Policy-driven validation.

    Loads rules from `core/policy/validation/validation_rules.yaml` with optional
    overrides from `rules.local.yaml`. Implements a pragmatic subset of checks
    that are unambiguous from the policy file:

    - Config: required keys (dot paths), numeric ranges, and simple type checks
    - Input: file format checks by extension
    """

    def __init__(self, rules: Optional[Mapping[str, Any]] = None) -> None:
        if rules is None:
            doc = load_policy_with_overrides("validation/validation_rules.yaml", section="validation")
            rules = doc.get("validation", doc) if isinstance(doc, Mapping) else {}
        self.rules: Mapping[str, Any] = rules

    # ---------- Public API ----------
    def validate_config(self, cfg: Mapping[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        issues += self._check_required_keys(cfg)
        issues += self._check_value_ranges(cfg)
        issues += self._check_types(cfg)
        return issues

    def validate_input_files(self, files: Iterable[str]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        issues += self._check_file_formats(files)
        return issues

    # ---------- Helpers ----------
    @staticmethod
    def _get_by_path(data: Mapping[str, Any], path: str) -> Tuple[bool, Optional[Any]]:
        cur: Any = data
        for part in path.split("."):
            if not isinstance(cur, Mapping) or part not in cur:
                return False, None
            cur = cur[part]
        return True, cur

    def _check_required_keys(self, cfg: Mapping[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        req = (
            self.rules.get("config_validation", {})
            .get("required_keys", {})
            .get("keys", [])
        )
        if isinstance(req, list):
            for key in req:
                if isinstance(key, str):
                    ok, _ = self._get_by_path(cfg, key)
                    if not ok:
                        issues.append(ValidationIssue("config", key, "missing required key"))
        return issues

    def _check_value_ranges(self, cfg: Mapping[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        ranges = (
            self.rules.get("config_validation", {})
            .get("value_validation", {})
            .get("ranges", {})
        )
        if isinstance(ranges, Mapping):
            for key, bounds in ranges.items():
                if not isinstance(key, str) or not (isinstance(bounds, list) and len(bounds) == 2):
                    continue
                ok, val = self._get_by_path(cfg, key)
                if not ok:
                    continue
                lo, hi = bounds[0], bounds[1]
                try:
                    v = float(val)
                    vlo = float(lo)
                    vhi = float(hi)
                except Exception:
                    issues.append(ValidationIssue("config", key, f"non-numeric value '{val}' for numeric range {bounds}"))
                    continue
                if not (vlo <= v <= vhi):
                    issues.append(ValidationIssue("config", key, f"value {v} outside range [{vlo}, {vhi}]"))
        return issues

    def _check_types(self, cfg: Mapping[str, Any]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        mapping = (
            self.rules.get("config_validation", {})
            .get("type_validation", {})
            .get("types", {})
        )
        type_map = {
            "integer": int,
            "float": (int, float),  # allow ints for float fields
            "string": str,
            "boolean": bool,
        }
        if isinstance(mapping, Mapping):
            for key, typname in mapping.items():
                if not isinstance(key, str) or not isinstance(typname, str):
                    continue
                ok, val = self._get_by_path(cfg, key)
                if not ok:
                    continue
                expected = type_map.get(typname.lower())
                if expected is None:
                    continue
                if not isinstance(val, expected):
                    issues.append(ValidationIssue("config", key, f"type {type(val).__name__} != {typname}"))
        return issues

    def _check_file_formats(self, files: Iterable[str]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        file_fmt = (
            self.rules.get("input_validation", {})
            .get("file_format", {})
        )
        if not (isinstance(file_fmt, Mapping) and file_fmt.get("enabled")):
            return issues
        allowed = file_fmt.get("supported_formats", [])
        allowed_set = {str(ext).lower().lstrip(".") for ext in (allowed or [])}
        if not allowed_set:
            return issues
        for f in files:
            low = str(f).lower()
            ext = low.rsplit(".", 1)[-1] if "." in low else ""
            if ext not in allowed_set:
                issues.append(ValidationIssue("input", str(f), f"unsupported file extension '{ext}'"))
        return issues
