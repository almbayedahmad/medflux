from __future__ import annotations

import functools
import os
from typing import Any, Callable, Optional

from .validator import validate_input, validate_output


def _get_soft_default() -> bool:
    val = (os.environ.get("MEDFLUX_VALIDATION_SOFT", "") or os.environ.get("MFLUX_VALIDATION_SOFT", "")).strip().lower()
    return val in {"1", "true", "yes"}


def validate_io(
    phase: str,
    *,
    validate_input_enabled: bool = True,
    validate_output_enabled: bool = True,
    input_getter: Optional[Callable[..., Any]] = None,
    output_getter: Optional[Callable[[Any], Any]] = None,
    soft: Optional[bool] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to validate a function's input and output against phase schemas.

    By default, input payload is taken as the first positional argument or
    from kwarg named 'payload'. Output payload is the function return value.
    Set env MEDFLUX_VALIDATION_SOFT=1 (or legacy MFLUX_VALIDATION_SOFT=1) to downgrade failures to warnings.
    """

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            effective_soft = _get_soft_default() if soft is None else soft
            if validate_input_enabled:
                try:
                    payload_in = input_getter(*args, **kwargs) if input_getter else (
                        kwargs.get("payload", args[0] if args else None)
                    )
                except Exception:
                    payload_in = None
                if payload_in is not None:
                    validate_input(phase, payload_in, soft=effective_soft)
            result = fn(*args, **kwargs)
            if validate_output_enabled:
                payload_out = result if output_getter is None else output_getter(result)
                if payload_out is not None:
                    validate_output(phase, payload_out, soft=effective_soft)
            return result

        return _wrapped

    return _decorator
def payload_from_args(*, run_id_kw: str = "run_id", items_pos: int = 0) -> Callable[..., Any]:
    """Factory for a standard input payload getter.

    Returns a function that extracts a payload shaped as {run_id, items}
    from function args/kwargs. Useful for pipeline run_* wrappers.
    """

    def _getter(*args: Any, **kwargs: Any) -> Any:
        rid = kwargs.get(run_id_kw)
        items = list(args[items_pos]) if (len(args) > items_pos and args[items_pos] is not None) else []
        return {"run_id": rid, "items": items}

    return _getter
