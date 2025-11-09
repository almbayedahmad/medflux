# PURPOSE:
#   Unified CLI entrypoint for the readers phase using the shared CLI toolkit
#   and PhaseRunner implementation.
#
# OUTCOME:
#   Consistent CLI UX across phases while preserving legacy CLI modules.

from __future__ import annotations

from core.preprocessing.cli.common import run_phase_cli
from ..api import ReadersRunner, PHASE_ID, PHASE_NAME_DEFAULT


def main(argv: list[str] | None = None) -> int:
    """Run the readers phase CLI wrapper using the shared toolkit.

    Outcome:
        Ensures a consistent CLI UX across phases.
    """
    return run_phase_cli(
        ReadersRunner,
        spec_kwargs={"phase_id": PHASE_ID, "name": PHASE_NAME_DEFAULT},
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
