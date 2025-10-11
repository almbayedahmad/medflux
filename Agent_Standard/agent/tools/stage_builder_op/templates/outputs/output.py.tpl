import json
import pathlib
import time

def save_{{ stage_name }}_doc(doc: dict, cfg: dict) -> None:
    out = pathlib.Path(cfg["io"]["out_doc_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

def save_{{ stage_name }}_stats(stats: dict, cfg: dict) -> None:
    payload = {"ts": int(time.time() * 1000), **stats}
    out = pathlib.Path(cfg["io"]["out_stats_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
