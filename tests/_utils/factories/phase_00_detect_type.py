from __future__ import annotations

from typing import Any, Dict, List


def make_phase00_input_minimal() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120000-deadbeef",
        "items": [
            {"path": "C:/docs/sample.pdf"},
        ],
    }


def make_phase00_input_ok() -> Dict[str, Any]:
    return {
        "run_id": "20250101T120000-deadbeef",
        "items": [
            {"path": "C:/docs/sample.pdf"},
            {"file_path": "C:/docs/image.png"},
        ],
        "extra": {"note": "allowed additionalProps"},
    }


def make_phase00_input_invalid() -> Dict[str, Any]:
    # Missing items
    return {
        "run_id": "",
        "items": [],
    }


def make_phase00_output_ok(items: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    items = items or [
        {
            "file_path": "C:/docs/sample.pdf",
            "extension": ".pdf",
            "file_type": "pdf",
            "confidence": 0.9,
        }
    ]
    return {
        "run_id": "20250101T120000-deadbeef",
        "unified_document": {
            "stage": "detect_type",
            "items": items,
            "source": {"items_received": 1, "items_included": 1},
            "errors": [],
        },
        "stage_stats": {
            "stage": "detect_type",
            "total_items": len(items),
            "items_received": len(items),
            "items_included": len(items),
            "items_skipped": 0,
            "counts": {},
        },
        "versioning": {"app_version": "0.1.0", "schema_version": "0.1.0"},
    }
