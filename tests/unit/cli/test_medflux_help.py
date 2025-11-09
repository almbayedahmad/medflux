# PURPOSE:
#   Unit tests for umbrella CLI help to ensure expected subcommands are present.
# OUTCOME:
#   Guards against accidental removal/rename of CLI entries.

from __future__ import annotations

import pytest

from core.cli.medflux import build_parser


@pytest.mark.unit
def test_medflux_help_lists_expected_subcommands() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    # Must include these subcommands
    for sub in (
        "phase-list",
        "phase-detect",
        "phase-encoding",
        "phase-readers",
        "phase-merge",
        "phase-cleaning",
        "phase-light-normalization",
        "phase-segmentation",
        "phase-table-extraction",
        "phase-heavy-normalization",
        "phase-provenance",
        "phase-offsets",
        "chain-run",
    ):
        assert sub in help_text
