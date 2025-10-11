"""
Module: output_format_schema

Layer: MAIN (Preprocessing)

Role: Standardized output format definitions

Reused by: ALL phases

Notes: Common output structure for all stages
"""

from typing import TypedDict, Dict, Any, List

class StageStats(TypedDict):
    processed_items_count: int
    avg_latency_per_unit_ms: float
    error_count: int
    warning_count: int
