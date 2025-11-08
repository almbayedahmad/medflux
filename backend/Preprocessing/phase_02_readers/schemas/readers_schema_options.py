from __future__ import annotations

"""Runtime options configuration for the readers stage."""

from dataclasses import dataclass


@dataclass(slots=True)
class ReaderOptions:
    """Configuration for the readers runtime."""

    mode: str = "mixed"
    lang: str = "deu+eng"
    dpi_mode: str = "auto"
    oem: int = 3
    dpi: int = 300
    psm: int = 6
    workers: int = 4
    use_pre: bool = False
    export_xlsx: bool = False
    verbose: bool = False
    tables_mode: str = "detect"
    save_table_crops: bool = False
    tables_min_words: int = 12
    table_detect_min_area: float = 9000.0
    table_detect_max_cells: int = 600
    blocks_threshold: int = 3
    native_ocr_overlay: bool = False
    overlay_area_thr: float = 0.35
    overlay_min_images: int = 1
    overlay_if_any_image: bool = False


__all__ = ["ReaderOptions"]
