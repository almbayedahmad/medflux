from __future__ import annotations

"""Thin wrapper around the readers CLI for backwards compatibility."""

from backend.Preprocessing.phase_02_readers.pipeline_workflow.readers_cli import run_readers_cli


def main() -> None:
    """Delegate to the unified run_readers CLI."""
    run_readers_cli()


if __name__ == "__main__":
    main()
