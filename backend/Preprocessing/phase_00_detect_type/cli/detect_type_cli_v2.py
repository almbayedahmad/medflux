# PURPOSE:
#   Unified CLI entrypoint for the detect_type phase using the shared CLI toolkit
#   and PhaseRunner implementation.
#
# OUTCOME:
#   Consistent CLI UX across phases while preserving legacy CLI modules.

from __future__ import annotations

from core.preprocessing.cli.common import run_phase_cli
from ..api import DetectTypeRunner, PHASE_ID, PHASE_NAME_DEFAULT


def main(argv: list[str] | None = None) -> int:
    """Run the detect_type phase CLI wrapper.

    Outcome:
        Delegates argument parsing/dispatch to the shared CLI toolkit.
    """
    return run_phase_cli(
        DetectTypeRunner,
        spec_kwargs={"phase_id": PHASE_ID, "name": PHASE_NAME_DEFAULT},
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
