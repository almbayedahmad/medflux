from __future__ import annotations

"""Runtime data models for the readers stage."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Summary:
    files: List[str]
    page_count: int
    avg_conf: float
    warnings: List[str]
    timings_ms: Dict[str, float]
    page_decisions: List[str]


@dataclass
class PageRecord:
    file: str
    page: int
    source: str
    text: str
    conf: float = 0.0
    time_ms: float = 0.0
    words: int = 0
    chars: int = 0
    ocr_conf_avg: Optional[float] = None


@dataclass
class TableRecord:
    file: str
    page: int
    rows: List[List[str]]
    decision: str
    metrics: Optional[Dict[str, float]] = None


__all__ = ["Summary", "PageRecord", "TableRecord"]
