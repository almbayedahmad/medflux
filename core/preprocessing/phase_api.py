# PURPOSE:
#   Provide a shared, minimal Phase API to standardize how phases connect
#   configuration, prepare inputs, execute domain logic, persist outputs,
#   validate contracts, and stamp versioning metadata.
#
# OUTCOME:
#   Enables consistent, testable phase lifecycles across all phases, reduces
#   duplication, and prepares the codebase for incremental refactors without
#   breaking external interfaces.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, Iterable, List, MutableMapping, Optional, Sequence, Tuple, TypeVar
import logging

logger = logging.getLogger(__name__)

I = TypeVar("I")
O = TypeVar("O")


@dataclass(frozen=True)
class PhaseSpec:
    """Describe a phase in a stable, minimal way.

    Args:
        phase_id: Canonical identifier (e.g., "phase_01_encoding").
        name: Human-friendly name (e.g., "encoding").
    Outcome:
        Stable identity usable for logging, metrics, and routing.
    """

    phase_id: str
    name: str


@dataclass(frozen=True)
class StageIO:
    """Standard output locations for a phase.

    Args:
        out_doc_path: Document JSON path to write.
        out_stats_path: Stage stats JSON path to write.
        summary_path: Optional phase summary path.
    Outcome:
        Normalized IO targets per phase to ensure deterministic structure.
    """

    out_doc_path: Path
    out_stats_path: Path
    summary_path: Optional[Path] = None


def _try_import_metrics() -> Tuple[Any, Any]:
    """Get metrics helpers if available; otherwise fall back to no-ops.

    Returns:
        A pair of context managers (phase_step, io_op).
    """

    try:
        from core.preprocessing.metrics import phase_step, io_op  # type: ignore

        return phase_step, io_op
    except Exception:  # pragma: no cover - defensive fallback
        from contextlib import contextmanager

        @contextmanager
        def _noop(_name: str):
            yield

        return _noop, _noop


class PhaseRunner(Generic[I, O]):
    """Base class orchestrating a phase's lifecycle.

    Subclasses should override the underscored hook methods. Public `run()`
    remains stable and is intended to be used by CLIs and orchestrators.

    Outcome:
        Provides a single, consistent lifecycle for all phases.
    """

    spec: PhaseSpec

    def __init__(self, spec: PhaseSpec) -> None:
        self.spec = spec
        self._phase_step, self._io_op = _try_import_metrics()

    # ----- Hooks to override -------------------------------------------------
    def _connect_config(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return effective configuration for this phase.

        Raises:
            NotImplementedError: if subclass doesn't implement.
        """

        raise NotImplementedError

    def _connect_upstream(self, items: Optional[Sequence[I]] = None) -> Sequence[I]:
        """Normalize/prepare upstream inputs to a canonical structure."""

        return list(items or [])

    def _process(self, upstream: Sequence[I], *, config: Dict[str, Any]) -> O:  # noqa: D401
        """Run the domain logic. Must be implemented by subclasses."""

        raise NotImplementedError

    def _save_outputs(self, payload: O, *, config: Dict[str, Any]) -> None:
        """Persist outputs to disk. Subclasses should implement if applicable."""

        return None

    def _validate_io(self, payload: O) -> None:
        """Validate input/output contracts (schema). Optional by default."""

        return None

    def _stamp_version(self, result: MutableMapping[str, Any]) -> None:
        """Attach versioning metadata to the result mapping if provided."""

        return None

    # ----- Orchestration ----------------------------------------------------
    def run(
        self,
        items: Optional[Sequence[I]] = None,
        *,
        config_overrides: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the standardized lifecycle for a phase.

        Args:
            items: Optional upstream items for this phase.
            config_overrides: Optional configuration overrides.
            run_id: Optional run identifier for traceability.
        Returns:
            A result mapping with at least the computed payload. Subclasses
            can enrich this mapping as needed.
        Outcome:
            Stable execution flow with metrics around key steps.
        """

        with self._phase_step(f"{self.spec.phase_id}.connect_config"):
            cfg = self._connect_config(config_overrides)

        with self._phase_step(f"{self.spec.phase_id}.connect_upstream"):
            upstream = self._connect_upstream(items)

        with self._phase_step(f"{self.spec.phase_id}.process"):
            payload = self._process(upstream, config=cfg)

        with self._phase_step(f"{self.spec.phase_id}.save_outputs"):
            self._save_outputs(payload, config=cfg)

        with self._phase_step(f"{self.spec.phase_id}.validate_io"):
            self._validate_io(payload)

        result: Dict[str, Any] = {
            "payload": payload,  # subclasses can return richer payloads
            "config": cfg,
        }
        if run_id:
            result["run_id"] = run_id
        with self._phase_step(f"{self.spec.phase_id}.stamp_version"):
            try:
                self._stamp_version(result)
            except Exception:  # pragma: no cover - defensive
                logger.debug("phase.versioning.skip", exc_info=True)
        return result
