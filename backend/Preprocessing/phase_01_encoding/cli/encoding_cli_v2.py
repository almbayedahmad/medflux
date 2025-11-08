# PURPOSE:
#   Unified CLI entrypoint for the encoding phase using the shared CLI toolkit
#   and PhaseRunner implementation.
#
# OUTCOME:
#   Provides a consistent CLI UX across phases while preserving legacy CLI
#   modules for backward compatibility.

from __future__ import annotations

from core.preprocessing.cli.common import run_phase_cli
from core.preprocessing.phase_api import PhaseSpec
from ..api import EncodingRunner, PHASE_ID, PHASE_NAME_DEFAULT


def main(argv: list[str] | None = None) -> int:
    return run_phase_cli(
        EncodingRunner,
        spec_kwargs={"phase_id": PHASE_ID, "name": PHASE_NAME_DEFAULT},
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
