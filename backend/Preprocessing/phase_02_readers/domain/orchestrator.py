# PURPOSE:
#   Provide a stable import path for the Readers orchestrator within the
#   domain layer, decoupling external callers from legacy pipeline_workflow
#   locations while migration proceeds.
#
# OUTCOME:
#   Allows domain.process to import ReadersOrchestrator from this module.
#   Implementation may initially delegate to the legacy module but can be
#   inlined here when the migration removes pipeline_workflow.

from __future__ import annotations

try:
    from .orchestrator_core import ReadersOrchestrator as ReadersOrchestrator  # type: ignore
except Exception as exc:  # pragma: no cover - defensive fallback
    class ReadersOrchestrator:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401
            raise RuntimeError("ReadersOrchestrator implementation not available: " + str(exc))
