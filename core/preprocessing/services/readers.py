# PURPOSE:
#   Stable wrapper around readers stage helpers to expose consistent metadata
#   without importing the readers internals directly.
#
# OUTCOME:
#   Allows orchestrators and tools to compute readers run metadata via a stable
#   facade method.

from __future__ import annotations

from typing import Dict, Optional


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

        from backend.Preprocessing.phase_02_readers.connecters.readers_connector_metadata import (  # noqa: E501
            compute_readers_run_metadata,
        )

        return compute_readers_run_metadata(run_id=run_id, pipeline_id=pipeline_id)
