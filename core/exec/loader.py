"""Core execution loader wiring cross-cutting modules.

This is a minimal, dependency-injected loader that exposes hooks for:
 - logging (core.logging)
 - validation (core.validation)
 - versioning (core.versioning)

It does not move or assume locations for flows/rules/contracts beyond the
existing package boundaries, and can be extended incrementally.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from core.logging import get_logger, configure_logging, log_context, with_context
from core.validation import Validator, ValidationError, ValidationEngine
from core.versioning import get_version
from core.monitoring import get_monitor


FlowFn = Callable[[Dict[str, Any]], Any]


class CoreLoader:
    """Lightweight core loader that wires cross-cutting concerns.

    Parameters are optional for DI; sensible defaults are used otherwise.
    """

    def __init__(
        self,
        *,
        logger=None,
        validator: Optional[Validator] = None,
        version: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> None:
        configure_logging()
        base_logger = logger or get_logger("medflux.core.exec")
        self.validator = validator or Validator()
        self.version = version or get_version()
        self.pipeline_id = pipeline_id
        self.run_id = run_id
        self.log = with_context(
            base_logger,
            version=self.version,
            pipeline_id=self.pipeline_id,
            run_id=self.run_id,
        )
        self.monitor = get_monitor(logger=base_logger, version=self.version, pipeline_id=self.pipeline_id, run_id=self.run_id)
        self._flows: Dict[str, FlowFn] = {}

    # --- Flow registry -------------------------------------------------
    def register_flow(self, name: str, fn: FlowFn) -> None:
        if not callable(fn):
            raise TypeError("flow must be callable")
        if name in self._flows:
            self.log.warning("Overriding existing flow '%s'", name)
        self._flows[name] = fn
        self.log.debug("Registered flow '%s'", name)

    def has_flow(self, name: str) -> bool:
        return name in self._flows

    def run_flow(self, name: str, context: Dict[str, Any]) -> Any:
        if name not in self._flows:
            raise KeyError(f"Unknown flow: {name}")
        self.log.info("Running flow '%s'", name)
        self.monitor.inc("flow_runs_total", labels={"flow": name})
        try:
            with log_context(self.log, flow=name) as clog, self.monitor.timer("flow_duration_ms", labels={"flow": name}):
                result = self._flows[name](context)
                clog.debug("Flow '%s' completed", name)
                return result
        except Exception as exc:  # pragma: no cover - minimal error path
            self.log.exception("Flow '%s' failed: %s", name, exc)
            raise

    # --- Validation helpers -------------------------------------------
    def validate(self, data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
        try:
            self.validator.validate(data, schema)
        except ValidationError:
            # Re-raise for upstream handling; already explicit
            raise
        except Exception as exc:  # pragma: no cover
            # Wrap unexpected issues as ValidationError for consistency
            raise ValidationError(str(exc))

    # Policy-driven config validation helper
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        engine = ValidationEngine()
        issues = engine.validate_config(config)
        if issues:
            for issue in issues:
                self.log.warning("config validation: %s at %s (%s)", issue.message, issue.path, issue.scope)
        return {"ok": not issues, "issues": [issue.__dict__ for issue in issues]}
