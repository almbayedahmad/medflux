from pathlib import Path

import numpy as np
import pytest

from medflux_backend.Preprocessing.phase_02_readers import readers_core
from medflux_backend.Preprocessing.phase_02_readers.readers_core import ReaderOptions, UnifiedReaders


class _DummyPixmap:
    def __init__(self, width: int = 16, height: int = 16, channels: int = 1):
        self.width = width
        self.height = height
        self.n = channels
        total = width * height * channels
        self.samples = (np.zeros(total, dtype=np.uint8)).tobytes()


class _DummyPage:
    class _Rect:
        def __init__(self):
            self.x0 = 0.0
            self.y0 = 0.0
            self.width = 595.0
            self.height = 842.0

    def __init__(self):
        self.rect = self._Rect()

    def get_pixmap(self, matrix, alpha=False):  # pragma: no cover - stub only
        return _DummyPixmap()


@pytest.fixture()
def reader(tmp_path):
    options = ReaderOptions(
        tables_mode="detect",
        table_detect_min_area=9000.0,
        table_detect_max_cells=600,
    )
    return UnifiedReaders(tmp_path, options)


def test_table_candidate_passes_threshold(monkeypatch, reader):
    warnings = []
    monkeypatch.setattr(reader, "_log_warning", warnings.append)

    def fake_extract(arr, **_):
        return (
            [["r1c1", "r1c2"], ["r2c1", "r2c2"]],
            {
                "rows": 2,
                "cols": 2,
                "cell_count": 4,
                "avg_cell_height": 400.0,
                "avg_cell_width": 40.0,
                "avg_cell_area": 16000.0,
            },
            {"row_lines": [0, 50, 100], "col_lines": [0, 60, 120], "image_width": 200, "image_height": 200},
        )

    monkeypatch.setattr(readers_core, "extract_tables_from_image", fake_extract)
    reader._maybe_collect_tables(_DummyPage(), Path("dummy.pdf"), 1, "native", ocr_data={})

    assert reader._table_flags == {1}
    assert reader._tables[0].metrics == {
        "rows": 2,
        "cols": 2,
        "cell_count": 4,
        "avg_cell_height": 400.0,
        "avg_cell_width": 40.0,
        "avg_cell_area": 16000.0,
    }
    assert reader._tables_raw
    assert reader._tables_raw[0]["status"] == "ok"
    assert warnings == []


def test_table_candidate_filtered(monkeypatch, reader):
    warnings = []
    monkeypatch.setattr(reader, "_log_warning", warnings.append)

    def fake_extract(arr, **_):
        return (
            [["only cell"]],
            {
                "rows": 20,
                "cols": 40,
                "cell_count": 800,
                "avg_cell_height": 100.0,
                "avg_cell_width": 10.0,
                "avg_cell_area": 1000.0,
            },
            {"row_lines": [0, 10, 20], "col_lines": [0, 5, 10], "image_width": 40, "image_height": 40},
        )

    monkeypatch.setattr(readers_core, "extract_tables_from_image", fake_extract)
    reader._maybe_collect_tables(_DummyPage(), Path("dummy.pdf"), 2, "native", ocr_data={})

    assert reader._table_flags == set()
    assert reader._tables == []
    assert reader._tables_raw
    assert reader._tables_raw[-1]["status"] in {"failed", "fallback"}
    assert warnings and "table_candidate_filtered:p2" in warnings[0]
