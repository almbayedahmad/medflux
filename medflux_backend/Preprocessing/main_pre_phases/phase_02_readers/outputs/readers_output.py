from __future__ import annotations

"""Output writers for the readers stage."""

import json
from pathlib import Path
from typing import Any, Dict


def save_readers_doc_meta(doc_meta: Dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(doc_meta, ensure_ascii=False, indent=2), encoding="utf-8")


def save_readers_stage_stats(stage_stats: Dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(stage_stats, ensure_ascii=False, indent=2), encoding="utf-8")


def save_readers_summary(summary_payload: Dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
