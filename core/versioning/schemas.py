from __future__ import annotations

from importlib import resources
from typing import Any, Dict, Mapping, Optional, Tuple


def _load_yaml(text: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load schemas.yaml") from exc
    data = yaml.safe_load(text)
    return data or {}


def _schemas() -> Dict[str, Any]:
    with resources.files(__package__).joinpath("schemas.yaml").open("r", encoding="utf-8") as f:
        return _load_yaml(f.read())


def get_schema_version(name: str, *, kind: str = "contracts") -> Optional[str]:
    sch = _schemas()
    try:
        return str(sch["schemas"][kind][name])
    except Exception:
        return None


def _extract_version_from_doc(doc: Mapping[str, Any]) -> Optional[str]:
    # Try common locations for schema version markers
    for path in (
        ("stage_contract", "versioning", "schema_version"),
        ("versioning", "schema_version"),
        ("schema_version",),
    ):
        cur: Any = doc
        for key in path:
            if not isinstance(cur, Mapping) or key not in cur:  # type: ignore[arg-type]
                cur = None
                break
            cur = cur[key]  # type: ignore[index]
        if isinstance(cur, (str, int, float)):
            return str(cur)
    return None


def validate_contract_version(contract_name: str, doc: Mapping[str, Any]) -> Tuple[bool, str]:
    expected = get_schema_version(contract_name, kind="contracts")
    if not expected:
        return True, "no-expected-version"
    found = _extract_version_from_doc(doc)
    if not found:
        return False, f"missing schema_version; expected {expected}"
    if str(found) != str(expected):
        return False, f"schema_version mismatch: found {found}, expected {expected}"
    return True, "ok"
