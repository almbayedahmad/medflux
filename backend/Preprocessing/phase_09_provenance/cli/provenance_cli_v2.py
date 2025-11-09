# PURPOSE:
#   Unified CLI entrypoint for the provenance phase (v2 scaffold).
# OUTCOME:
#   Consistent CLI flags and runner bootstrapping.

from __future__ import annotations

from core.preprocessing.cli.common import run_phase_cli
from ..api import ProvenanceRunner, PHASE_ID, PHASE_NAME_DEFAULT


def main(argv: list[str] | None = None) -> int:
    """Run the provenance phase CLI wrapper using the shared toolkit.

    Outcome:
        Ensures a consistent CLI UX across phases.
    """
    return run_phase_cli(
        ProvenanceRunner,
        spec_kwargs={"phase_id": PHASE_ID, "name": PHASE_NAME_DEFAULT},
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
