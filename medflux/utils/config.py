from __future__ import annotations

from pathlib import Path
import os
import yaml


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROFILES_DIR = _PROJECT_ROOT / "medflux_backend" / "Preprocessing" / "phase_02_readers" / "config" / "profiles"
_LEGACY_CONFIGS_DIR = _PROJECT_ROOT / "configs"


def _candidate_paths(profile: str) -> list[Path]:
    filename = "readers.yaml" if profile == "prod" else f"readers.{profile}.yaml"
    override = os.getenv("READERS_CONFIG_PATH")
    candidates = []
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
    candidates = _candidate_paths(profile)
    for candidate in candidates:
        if candidate.exists():
            return _load_yaml(candidate)
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Unknown readers profile '{profile}' (searched: {searched})")


CFG = load_cfg()

