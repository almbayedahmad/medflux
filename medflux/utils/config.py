from __future__ import annotations

from pathlib import Path
import os
import yaml


def load_cfg() -> dict:
    profile = (os.getenv("READERS_PROFILE", "prod") or "prod").strip().lower()
    if profile == "prod":
        cfg_path = Path("configs/readers.yaml")
    else:
        cfg_path = Path(f"configs/readers.{profile}.yaml")
        if not cfg_path.exists():
            raise FileNotFoundError(f"Unknown readers profile '{profile}' (expected {cfg_path.name})")
    with cfg_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


CFG = load_cfg()
