# PURPOSE:
#   Stable wrapper around encoding helpers to avoid tight imports across phases.
#
# OUTCOME:
#   Downstream code can ask for text encoding characteristics without importing
#   phase-specific helper modules directly.
#
# INPUTS:
#   - input_path: str path to a text-like file whose encoding is to be detected.
#   - Uses default detection config (sample size) via domain process.
#
# OUTPUTS:
#   - Plain dict with keys: encoding, confidence, bom, is_utf8, sample_len.
#
# DEPENDENCIES:
#   - backend.Preprocessing.phase_01_encoding.domain.process (v2 domain entry).

from __future__ import annotations

from typing import Any, Dict, List


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

        # Delegate to v2 domain processing with normalization disabled to avoid IO.
        # This avoids importing legacy internal_helpers from the service layer.
        from backend.Preprocessing.phase_01_encoding.domain.process import (
            process_encoding_stage,
        )

        items: List[Dict[str, Any]] = [{"path": input_path, "normalize": False}]
        payload = process_encoding_stage(items, detection_cfg=None, normalization_cfg={"enabled": False})
        enc_items = payload.get("items") or []
        # payload["items"] holds EncodingItem instances; access attributes defensively
        def _extract(obj: Any) -> Dict[str, Any]:
            try:
                det = getattr(obj, "detection")  # dataclass attr
            except Exception:
                det = None
            if isinstance(det, dict):
                base = det
            else:
                # Fallback: attempt mapping-like access
                base = {}
                for k in ("encoding", "confidence", "bom", "is_utf8", "sample_len"):
                    try:
                        base[k] = getattr(det, k)
                    except Exception:
                        base[k] = None
            # Ensure all keys present
            out: Dict[str, Any] = {}
            for k in ("encoding", "confidence", "bom", "is_utf8", "sample_len"):
                out[k] = base.get(k) if isinstance(base, dict) else None
            return out

        if enc_items:
            try:
                return _extract(enc_items[0])
            except Exception:
                pass
        return {"encoding": None, "confidence": None, "bom": None, "is_utf8": None, "sample_len": 0}
