"""
Module: pipeline_config_schema

Layer: MAIN (Preprocessing)

Role: Pipeline configuration schema

Reused by: main_pre_pipeline modules

Notes: Configuration structure for multi-phase pipelines
"""

from typing import TypedDict, Dict, Any

class PipelineConfig(TypedDict):
    phase_sequence: list[str]
    io_config: Dict[str, Any]
    options_config: Dict[str, Any]
