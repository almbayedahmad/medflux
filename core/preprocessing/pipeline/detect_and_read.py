from __future__ import annotations

"""Thin wrapper delegating to the v2 readers CLI."""

from backend.Preprocessing.phase_02_readers.cli.readers_cli_v2 import main as _readers_main


def main() -> None:
    """Delegate to the unified v2 run_readers CLI."""
    _readers_main()


if __name__ == "__main__":
    main()
