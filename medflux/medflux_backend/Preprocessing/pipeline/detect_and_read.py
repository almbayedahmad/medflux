from __future__ import annotations

"""Thin wrapper around the readers CLI for backwards compatibility."""

from medflux_backend.Preprocessing.phase_02_readers.run_readers import main as run_readers_main


def main() -> None:
    """Delegate to the unified run_readers CLI."""
    run_readers_main()


if __name__ == "__main__":
    main()
