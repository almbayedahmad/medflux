# PURPOSE:
#   Stable wrapper around phase_00 detection logic to decouple other phases
#   from implementation details and imports.
#
# OUTCOME:
#   Other phases or tools can request detection metadata via a single, stable
#   method without importing phase internals directly.
#
# INPUTS:
#   - input_path: str path to the document to detect.
#
# OUTPUTS:
#   - Plain dict with detection details including recommended settings.
#
# DEPENDENCIES:
#   - backend.Preprocessing.phase_00_detect_type.domain.process (v2 domain entry).

from __future__ import annotations

from typing import Any, Dict, List


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

        # Use the v2 domain entrypoint to avoid direct dependence
        # on legacy internal_helpers. Domain returns a unified payload
        # with a list of items; we extract the one that matches input_path.
        from backend.Preprocessing.phase_00_detect_type.domain.process import (
            process_detect_type_classifier,
        )

        items: List[Dict[str, Any]] = [{"path": input_path}]
        payload = process_detect_type_classifier(items, detection_overrides=None)  # type: ignore[arg-type]
        try:
            docs = payload.get("unified_document", {}).get("items", [])  # type: ignore[assignment]
        except Exception:
            docs = []
        # Prefer exact file match; fallback to first item
        match = None
        for it in docs:
            try:
                if str(it.get("file_path")) == str(input_path):
                    match = it
                    break
            except Exception:
                continue
        match = match or (docs[0] if docs else None)
        if isinstance(match, dict):
            return match
        # Fallback: return minimal mapping
        return {"file_path": input_path, "details": {}, "recommended": {}}
