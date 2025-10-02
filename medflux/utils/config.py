import os
import yaml


def load_cfg(path: str | None = None):
    cfg_path = path or os.getenv("MEDFLUX_READERS_CFG", "configs/readers.yaml")
    with open(cfg_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


CFG = load_cfg()
