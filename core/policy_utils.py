from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def repo_root() -> Path:
    # core/policy_utils.py -> core -> repo root
    return Path(__file__).resolve().parents[1]


def get_policy_path(relative: str) -> Path:
    path = repo_root() / "core" / "policy" / relative
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return path


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load policy YAML files") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def load_yaml_policy(relative: str) -> Dict[str, Any]:
    return _load_yaml(get_policy_path(relative))


def load_policy_with_overrides(relative: str, section: Optional[str] = None) -> Dict[str, Any]:
    """Load a policy YAML and overlay keys from rules.local.yaml if present.

    - relative: path under core/policy (e.g., 'validation/validation_rules.yaml')
    - section: optional top-level key to overlay from overrides (e.g., 'validation')
    """
    base = load_yaml_policy(relative)
    overrides_path = repo_root() / "core" / "policy" / "rules.local.yaml"
    if overrides_path.exists():
        try:
            overrides = _load_yaml(overrides_path)
        except Exception:
            overrides = {}
        if section and isinstance(overrides.get(section), dict):
            base_section = base.get(section)
            if isinstance(base_section, dict):
                base_section.update(overrides[section])
            else:
                base[section] = overrides[section]
        elif isinstance(overrides, dict):
            base.update(overrides)
    return base
