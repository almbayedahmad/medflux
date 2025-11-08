# PURPOSE:
#   Stable wrapper around encoding helpers to avoid tight imports across phases.
#
# OUTCOME:
#   Downstream code can ask for text encoding characteristics without importing
#   phase-specific helper modules directly.

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict


class EncodingService:
    """Facade for text encoding capabilities."""

    @staticmethod
    def detect_text_info(input_path: str) -> Dict[str, Any]:
        """Return text encoding information for a file (best-effort dict).

        Args:
            input_path: Path to input text file.
        Returns:
            A mapping with keys like encoding, confidence, bom, is_utf8, sample_len.
        """

        from backend.Preprocessing.phase_01_encoding.internal_helpers.encoding_helper_detection import (  # noqa: E501
            get_encoding_text_detection,
        )

        info = get_encoding_text_detection(input_path)
        if is_dataclass(info):
            try:
                return asdict(info)
            except Exception:
                pass
        payload: Dict[str, Any] = {}
        for key in ("encoding", "confidence", "bom", "is_utf8", "sample_len"):
            try:
                payload[key] = getattr(info, key)  # type: ignore[attr-defined]
            except Exception:
                payload[key] = None
        return payload
