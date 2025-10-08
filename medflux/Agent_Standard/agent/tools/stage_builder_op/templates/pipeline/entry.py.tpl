
def run_{{ stage_name }}_pipeline(cfg: dict) -> None:
    from connecters.{{ stage_name }}_config_connector import connect_{{ stage_name }}_config_connector
    from outputs.{{ stage_name }}_output import save_{{ stage_name }}_doc, save_{{ stage_name }}_stats

    data = {"items": []}
    save_{{ stage_name }}_doc(data, cfg)
    save_{{ stage_name }}_stats({"processed_items_count": 0}, cfg)
