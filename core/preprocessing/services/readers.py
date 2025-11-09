# PURPOSE:
#   Stable wrapper around readers stage helpers to expose consistent metadata
#   without importing the readers internals directly.
#
# OUTCOME:
#   Allows orchestrators and tools to compute readers run metadata and derive
#   detect/encoding-driven metadata via a stable facade, avoiding cross-phase
#   imports outside the services layer.

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


class ReadersService:
    """Facade for readers-stage utilities."""

    @staticmethod
    def compute_run_metadata(run_id: Optional[str] = None, pipeline_id: Optional[str] = None) -> Dict[str, str]:
        """Compute run metadata in a stable, import-light way.

        Args:
            run_id: Optional run identifier.
            pipeline_id: Optional pipeline identifier.
        Returns:
            A mapping with run metadata keys.
        """

        from uuid import uuid4

        resolved_run_id = run_id or f"readers-{uuid4().hex}"
        resolved_pipeline = pipeline_id or "preprocessing.readers"
        return {"run_id": resolved_run_id, "pipeline_id": resolved_pipeline}

    @staticmethod
    def get_detect_meta(input_path: str | Path) -> Dict[str, Any]:
        """Get detection metadata via DetectService facade.

        Args:
            input_path: Path to the input document.
        Returns:
            Readers-digestible detection metadata mapping.
        """

        from .detect import DetectService

        res = DetectService.detect_file(str(input_path))
        recommended = res.get("recommended") or {}
        return {
            "detected_mode": recommended.get("mode"),
            "lang": recommended.get("lang") or "deu+eng",
            "dpi": recommended.get("dpi", 300),
            "psm": recommended.get("psm", 6),
            "tables_mode": recommended.get("tables_mode", "light"),
            "file_type": (res.get("file_type") or "unknown"),
            "confidence": res.get("confidence"),
            "details": res.get("details") or {},
        }

    @staticmethod
    def get_encoding_meta(input_path: str | Path, file_type: str) -> Dict[str, Any]:
        """Get encoding metadata via EncodingService facade when applicable.

        Args:
            input_path: Path to the input document (text file for encoding).
            file_type: File type hint from detection (e.g., 'txt').
        Returns:
            Mapping with primary encoding info when relevant to readers.
        """

        from .encoding import EncodingService

        payload: Dict[str, Any] = {
            "primary": None,
            "confidence": None,
            "bom": False,
            "is_utf8": None,
            "sample_len": 0,
        }
        if str(file_type).lower() in {"txt"}:
            info = EncodingService.detect_text_info(str(input_path))
            payload.update(
                {
                    "primary": info.get("encoding"),
                    "confidence": info.get("confidence"),
                    "bom": info.get("bom"),
                    "is_utf8": info.get("is_utf8"),
                    "sample_len": info.get("sample_len", 0),
                }
            )
        return payload
