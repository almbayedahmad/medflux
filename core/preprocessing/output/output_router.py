from __future__ import annotations

# PURPOSE:
#   Provide consistent, policy-compliant output directory handling for
#   preprocessing phases and smoke runs.
#
# OUTCOME:
#   Standardizes where artifacts are written and removes the legacy
#   repo-local `outputs/` default by preferring OS temp or an explicit env var.
#
# INPUTS:
#   Optional env var `MEDFLUX_OUTPUT_ROOT` to override base output directory.
#
# OUTPUTS:
#   Resolved paths for per-stage documents, stats, and optional summaries.

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import time


def _default_output_root() -> Path:
    """Resolve the base directory for preprocessing outputs.

    Prefers `MEDFLUX_OUTPUT_ROOT`. Falls back to the OS temp directory
    under `medflux/preprocessing` rather than a repo-local path, fully
    retiring the legacy `outputs/` structure.
    """

    env_override = os.environ.get("MEDFLUX_OUTPUT_ROOT")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return (Path(tempfile.gettempdir()) / "medflux" / "preprocessing").resolve()


_DEFAULT_BASE = _default_output_root()
_DEFAULT_SMOKE_ROOT = _DEFAULT_BASE / "pre_smoke_results"

_STAGE_DIRS = {
    "detector": "output_pre_detector_results",
    "encoder": "output_pre_encoder_results",
    "readers": "output_pre_readers_results",
    "merge": "output_pre_merge_results",
    "cleaning": "output_pre_cleaning_results",
    "light_normalization": "output_pre_light_normalization_results",
    "segmentation": "output_pre_segmentation_results",
    "table_extraction": "output_pre_table_extraction_results",
    "heavy_normalization": "output_pre_heavy_normalization_results",
    "provenance": "output_pre_provenance_results",
    "offsets": "output_pre_offsets_results",
}
_ALL_PHASES_DIR = "output_pre_all_phase_results"


@dataclass(frozen=True)
class StageIO:
    """Resolved file paths for an individual preprocessing stage.

    Outcome:
        Provides canonical IO mapping for document, stats, and optional
        summary files, suitable for `config_overrides["io"]`.
    """

    directory: Path
    doc_path: Path
    stats_path: Path
    summary_path: Optional[Path] = None

    def as_overrides(self) -> Dict[str, str]:
        """Return mapping compatible with a stage's IO overrides."""

        payload = {
            "out_doc_path": str(self.doc_path),
            "out_stats_path": str(self.stats_path),
        }
        if self.summary_path is not None:
            payload["out_summary_path"] = str(self.summary_path)
        return payload


class OutputRouter:
    """Manage smoke-test output folders across preprocessing stages.

    Outcome:
        Ensures directories exist and yields consistent file paths. Uses
        temp-based defaults unless MEDFLUX_OUTPUT_ROOT is set.
    """

    def __init__(
        self,
        *,
        root: Path | str | None = None,
        run_id: str | None = None,
        create_session_subdir: bool = True,
    ) -> None:
        self._root = Path(root) if root is not None else _DEFAULT_SMOKE_ROOT
        self._root = self._root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

        self._create_session_subdir = create_session_subdir
        self._run_id = run_id or time.strftime("session_%Y%m%d_%H%M%S")

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def root(self) -> Path:
        return self._root

    def child(self, *, run_id: str | None = None) -> "OutputRouter":
        """Return a router sharing the same base but with a different run id."""

        return OutputRouter(
            root=self._root,
            run_id=run_id or self._run_id,
            create_session_subdir=self._create_session_subdir,
        )

    # ------------------------------------------------------------------
    # Stage handling
    # ------------------------------------------------------------------

    def stage_dir(self, stage: str) -> Path:
        """Return the directory for a given stage, creating it if necessary."""

        if stage not in _STAGE_DIRS:
            raise ValueError(f"Unknown preprocessing stage: {stage!r}")
        base = self._root / _STAGE_DIRS[stage]
        base.mkdir(parents=True, exist_ok=True)
        if self._create_session_subdir:
            session_dir = base / self._run_id
            session_dir.mkdir(parents=True, exist_ok=True)
            return session_dir
        return base

    def stage_io(
        self,
        stage: str,
        *,
        doc_filename: str = "unified_document.json",
        stats_filename: str = "stage_stats.json",
        summary_filename: str | None = None,
    ) -> StageIO:
        """Provide the canonical IO file mapping for the target stage."""

        directory = self.stage_dir(stage)
        summary_path: Optional[Path] = None
        if summary_filename or stage == "readers":
            summary_path = directory / (summary_filename or "summary.json")
        return StageIO(
            directory=directory,
            doc_path=directory / doc_filename,
            stats_path=directory / stats_filename,
            summary_path=summary_path,
        )

    def normalization_dir(self, stage: str, name: str = "normalized") -> Path:
        """Directory where a stage should store additional assets (e.g., normalization)."""

        target = self.stage_dir(stage) / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    # ------------------------------------------------------------------
    # Multi-stage / combined outputs
    # ------------------------------------------------------------------

    def all_phases_dir(self) -> Path:
        base = self._root / _ALL_PHASES_DIR
        base.mkdir(parents=True, exist_ok=True)
        if self._create_session_subdir:
            session_dir = base / self._run_id
            session_dir.mkdir(parents=True, exist_ok=True)
            return session_dir
        return base

    def chain_summary_path(self, filename: str = "chain_summary.json") -> Path:
        target = self.all_phases_dir() / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def smoke_root(self) -> Path:
        """Return the base smoke directory (without stage-specific subfolders)."""

        return self._root


__all__ = ["OutputRouter", "StageIO"]
