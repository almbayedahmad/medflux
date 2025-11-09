# PURPOSE:
#   Provide shared CLI utilities (arguments and bootstrapping) for all
#   preprocessing phases to ensure consistent user experience.
#
# OUTCOME:
#   Standardizes CLI flags across phases and provides a simple runner wrapper
#   for PhaseRunner-based phases, reducing boilerplate and divergence.

from __future__ import annotations

import argparse
from typing import Any, Dict, Optional, Sequence, Type
from core.logging import get_logger

from core.preprocessing.phase_api import PhaseRunner


def add_common_phase_args(parser: argparse.ArgumentParser) -> None:
    """Add common flags used by all phases.

    Args:
        parser: Argument parser to extend.
    Outcome:
        Phases expose a predictable set of CLI flags and defaults.
    """

    parser.add_argument("inputs", nargs="*", help="Input items (paths or records)")
    parser.add_argument("--output-root", default=None, help="Optional output root directory")
    parser.add_argument("--run-id", default=None, help="Optional run identifier")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
    parser.add_argument("--log-json", action="store_true", help="Enable JSON logging format")
    parser.add_argument("--log-stderr", action="store_true", help="Log to stderr (console)")


def run_phase_cli(
    runner_cls: Type[PhaseRunner[Any, Any]],
    spec_kwargs: Dict[str, Any],
    argv: Optional[Sequence[str]] = None,
) -> int:
    """Bootstrap a PhaseRunner CLI entry.

    Args:
        runner_cls: A PhaseRunner subclass.
        spec_kwargs: Keyword args to construct the PhaseSpec for the runner.
        argv: Optional argument vector.
    Returns:
        Exit code (0 on success).
    Outcome:
        Consistent wiring between CLI flags and PhaseRunner orchestration.
    """

    parser = argparse.ArgumentParser()
    add_common_phase_args(parser)
    args = parser.parse_args(argv)

    # Configure logging via central policy, honoring CLI flags and env profile.
    # MEDFLUX_LOG_PROFILE selects the profile (dev/prod). CLI flags adjust runtime.
    import os
    from core.logging import configure_logging

    if args.log_level:
        os.environ["MEDFLUX_LOG_LEVEL"] = str(args.log_level)
    # Toggle JSON and stderr based on flags
    if bool(getattr(args, "log_json", False)):
        os.environ["MEDFLUX_LOG_JSON"] = "1"
    if bool(getattr(args, "log_stderr", False)):
        os.environ["MEDFLUX_LOG_TO_STDERR"] = "1"
    # Apply logging configuration (force reconfigure to honor flags)
    configure_logging(force=True)

    from core.preprocessing.phase_api import PhaseSpec

    runner = runner_cls(PhaseSpec(**spec_kwargs))
    result = runner.run(
        items=[{"path": p} for p in (args.inputs or [])],
        config_overrides={"io": {"out_root": args.output_root}} if args.output_root else None,
        run_id=args.run_id,
    )
    # Log minimal JSON for quick inspection (no stdout prints)
    logger = get_logger("cli")
    try:
        import json
        logger.info(json.dumps({k: v for k, v in result.items() if k != "payload"}, ensure_ascii=False, indent=2))
    except Exception:
        logger.info("{result}")
    return 0
