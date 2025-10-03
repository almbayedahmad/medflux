from __future__ import annotations

"""Schema helpers and typed payloads for the encoding stage."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence


@dataclass
class EncodingItem:
    file_path: str
    detection: Dict[str, Any]
    normalization: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "file_path": self.file_path,
            "detection": self.detection,
        }
        if self.normalization is not None:
            payload["normalization"] = self.normalization
        return payload


def summarize_encoding_document(items: Sequence[EncodingItem]) -> Dict[str, Any]:
    return {
        "stage": "encoding",
        "items": [item.to_dict() for item in items],
    }


def summarize_encoding_stats(items: Sequence[EncodingItem]) -> Dict[str, Any]:
    total = len(items)
    normalized = sum(1 for item in items if item.normalization and item.normalization.get("ok"))
    failed = sum(1 for item in items if item.normalization and not item.normalization.get("ok"))
    with_bom = sum(1 for item in items if item.detection.get("bom"))
    utf8_native = sum(1 for item in items if item.detection.get("is_utf8"))
    return {
        "stage": "encoding",
        "total_items": total,
        "normalized": normalized,
        "failed_normalizations": failed,
        "with_bom": with_bom,
        "utf8_native": utf8_native,
    }


def get_encoding_types() -> Dict[str, Any]:
    return {
        "unified_document": {
            "stage": "encoding",
            "items": [
                {
                    "file_path": "string",
                    "detection": {
                        "encoding": "string | null",
                        "confidence": "float | null",
                        "bom": "bool",
                        "is_utf8": "bool",
                        "sample_len": "int",
                    },
                    "normalization": {
                        "ok": "bool",
                        "normalized_path": "string | null",
                        "reason": "string | null",
                    },
                }
            ],
        },
        "stage_stats": {
            "stage": "encoding",
            "total_items": "int",
            "normalized": "int",
            "failed_normalizations": "int",
            "with_bom": "int",
            "utf8_native": "int",
        },
    }
