# PURPOSE:
#   Stable wrapper around phase_00 detection logic to decouple other phases
#   from implementation details and imports.
#
# OUTCOME:
#   Other phases or tools can request detection metadata via a single, stable
#   method without importing phase internals directly.

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict


class DetectService:
    """Facade for detect-type capabilities."""

    @staticmethod
    def detect_file(input_path: str) -> Dict[str, Any]:
        """Run detection for a single file and return a plain dict.

        Args:
            input_path: Path to input file.
        Returns:
            Detection result as a JSON-serializable dict.
        Outcome:
            Provides downstream-agnostic detection metadata.
        """

        from backend.Preprocessing.phase_00_detect_type.internal_helpers.detect_type_helper_detection import (  # noqa: E501
            process_detect_type_file,
        )

        result = process_detect_type_file(input_path)
        if is_dataclass(result):
            try:
                return asdict(result)
            except Exception:
                pass
        # best effort conversion
        try:
            return dict(result)  # type: ignore[arg-type]
        except Exception:
            return {"value": str(result)}
