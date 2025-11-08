from __future__ import annotations

from pathlib import Path
import os
import yaml


_PHASE_CONFIG_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_PROFILES_DIR = _PHASE_CONFIG_DIR / "profiles"
_LEGACY_CONFIGS_DIR = _PROJECT_ROOT / "configs"


def _candidate_paths(profile: str) -> list[Path]:
    filename = "readers.yaml" if profile == "prod" else f"readers.{profile}.yaml"
    override = os.getenv("READERS_CONFIG_PATH")
    candidates: list[Path] = []
    if override:
        override_path = Path(override)
        if override_path.is_dir():
            candidates.append(override_path / filename)
        else:
            candidates.append(override_path)
    candidates.append(_PROFILES_DIR / filename)
    candidates.append(_LEGACY_CONFIGS_DIR / filename)
    return candidates


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Configuration at {path} must be a mapping, got {type(data)!r}")
    return data


def load_cfg() -> dict:
    profile = (os.getenv("READERS_PROFILE", "prod") or "prod").strip().lower()
    paths = _candidate_paths(profile)
    for candidate in paths:
        if candidate.exists():
            return _load_yaml(candidate)
    searched = ", ".join(str(candidate) for candidate in paths)
    raise FileNotFoundError(f"Unknown readers profile '{profile}' (searched: {searched})")


CFG = load_cfg()
