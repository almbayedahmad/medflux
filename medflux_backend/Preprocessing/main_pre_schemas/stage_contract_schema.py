"""
Module: stage_contract_schema

Layer: MAIN (Preprocessing)

Role: Stage contract definitions for pipeline coordination

Reused by: ALL phases

Notes: Defines input/output contracts between phases
"""

from typing import TypedDict, List, Dict, Any

class StageInput(TypedDict):
    name: str
    type: str
    description: str
    required: bool

class StageOutput(TypedDict):
    name: str
    type: str
    description: str
