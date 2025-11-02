from __future__ import annotations

from typing import Any, Dict, List


def make_phase01_input_minimal() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120101-deadbeef",
        "items": [
            {"path": "C:/docs/sample.txt"},
        ],
    }


def make_phase01_input_ok() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120101-deadbeef",
        "items": [
            {"path": "C:/docs/sample.txt"},
            {"path": "C:/docs/notes.md"},
        ],
    }


def make_phase01_input_invalid() -> Dict[str, Any]:
    return {
        "run_id": "",
        "items": [],
    }


def make_phase01_output_ok() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120101-deadbeef",
        "unified_document": {
            "stage": "encoding",
            "items": [
                {
                    "file_path": "C:/docs/sample.txt",
                    "detection": {
                        "encoding": "utf-8",
                        "confidence": 0.99,
                        "bom": False,
                        "is_utf8": True,
                        "sample_len": 1024,
                    },
                    "normalization": {
                        "ok": True,
                        "normalized_path": "C:/tmp/normalized/sample.txt",
                        "reason": None,
                    },
                }
            ],
        },
        "stage_stats": {
            "stage": "encoding",
            "total_items": 1,
            "normalized": 1,
            "failed_normalizations": 0,
            "with_bom": 0,
            "utf8_native": 1,
        },
        "versioning": {"app_version": "0.1.0", "schema_version": "0.1.0"},
    }
