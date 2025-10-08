from __future__ import annotations

"""Schema helpers and typed results for the detect_type stage."""

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence


class FileType(str, Enum):
    """Supported file types detected during preprocessing."""

    PDF_TEXT = "pdf_text"
    PDF_SCANNED = "pdf_scanned"
    PDF_MIXED = "pdf_mixed"
    DOCX = "docx"
    IMAGE = "image"
    TXT = "txt"
    UNKNOWN = "unknown"


@dataclass
class FileTypeResult:
    """Unified representation of the detection outcome for a single document."""

    file_path: str
    ext: str
    mime: Optional[str]
    file_type: FileType
    ocr_recommended: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    recommended: Dict[str, Any] = field(default_factory=dict)

    def to_unified_dict(self) -> Dict[str, Any]:
        """Translate the detection result into a serializable payload."""

        return {
            "file_path": self.file_path,
            "extension": self.ext,
            "mime": self.mime,
            "file_type": self.file_type.value,
            "ocr_recommended": self.ocr_recommended,
            "confidence": self.confidence,
            "recommended": self.recommended,
            "details": self.details,
        }


def summarize_detect_type_results(results: Sequence[FileTypeResult]) -> Dict[str, Any]:
    """Build the unified document payload expected by the stage contract."""

    return {
        "stage": "detect_type",
        "items": [result.to_unified_dict() for result in results],
    }


def summarize_detect_type_stats(results: Sequence[FileTypeResult]) -> Dict[str, Any]:
    """Aggregate high-level statistics for the stage."""

    counter = Counter(result.file_type.value for result in results)
    return {
        "stage": "detect_type",
        "total_items": len(results),
        "counts": dict(counter),
    }


def get_detect_type_types() -> Dict[str, Any]:
    """Expose the typed schema description required by the standards."""

    return {
        "unified_document": {
            "stage": "detect_type",
            "items": [
                {
                    "file_path": "string",
                    "extension": "string",
                    "mime": "string | null",
                    "file_type": list(item.value for item in FileType),
                    "ocr_recommended": "bool",
                    "confidence": "float",
                    "recommended": "dict",
                    "details": "dict",
                }
            ],
        },
        "stage_stats": {
            "stage": "detect_type",
            "total_items": "int",
            "counts": {item.value: "int" for item in FileType},
        },
    }
