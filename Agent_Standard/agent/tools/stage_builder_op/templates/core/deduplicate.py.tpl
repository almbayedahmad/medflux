def deduplicate_{{ stage_name }}_deduplicate(items: list, cfg: dict) -> list:
    return list(dict.fromkeys(items))
