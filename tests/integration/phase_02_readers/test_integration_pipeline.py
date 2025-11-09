from __future__ import annotations

import pytest

from backend.Preprocessing.phase_02_readers.domain.process import (
    ReadersSegmentError,
    process_readers_segment,
)


def test_readers_pipeline_requires_items() -> None:
    with pytest.raises(ReadersSegmentError):
        process_readers_segment(
            [],
            io_config={},
            options_config={},
        )
