def connect_{{ stage_name }}_config_connector(stage: str) -> dict:
    import pathlib
    import yaml

    cfg_path = pathlib.Path("config") / f"{stage}.yaml"
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
