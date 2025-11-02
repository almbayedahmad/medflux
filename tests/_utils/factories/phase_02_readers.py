from __future__ import annotations

from typing import Any, Dict


def make_phase02_input_minimal() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120202-deadbeef",
        "items": [
            {"path": "C:/docs/sample.pdf"},
        ],
    }


def make_phase02_input_ok() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120202-deadbeef",
        "items": [
            {"path": "C:/docs/sample.pdf"},
            {"path": "C:/docs/another.pdf"},
        ],
    }


def make_phase02_input_invalid() -> Dict[str, Any]:
    return {
        "run_id": "",
        "items": [],
    }


def make_phase02_output_ok() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120202-deadbeef",
        "items": [
            {"input": "C:/docs/sample.pdf", "outdir": "C:/out/sample"},
        ],
        "stage_stats": {
            "documents": 1,
            "items_processed": 1,
            "avg_conf": None,
            "warnings": 0,
        },
        "versioning": {"app_version": "0.1.0", "schema_version": "0.1.0"},
    }
