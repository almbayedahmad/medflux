# PURPOSE:
#   Unit tests to ensure v2 phase CLIs expose help and parse without errors.
# OUTCOME:
#   Guards against accidental CLI regressions across representative phases.

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_detect_type_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    from backend.Preprocessing.phase_00_detect_type.cli.detect_type_cli_v2 import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])  # argparse exits after printing help
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower()


@pytest.mark.unit
def test_encoding_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    from backend.Preprocessing.phase_01_encoding.cli.encoding_cli_v2 import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])  # argparse exits after printing help
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower()


@pytest.mark.unit
def test_readers_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    from backend.Preprocessing.phase_02_readers.cli.readers_cli_v2 import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])  # argparse exits after printing help
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "usage" in out.lower()
