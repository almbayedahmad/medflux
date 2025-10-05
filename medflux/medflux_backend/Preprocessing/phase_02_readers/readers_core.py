"""Compatibility shim for legacy `readers_core` imports."""
from __future__ import annotations

from .pipeline_workflow.readers_pipeline_main import ReadersOrchestrator
from .internal_helpers.reader_helpers_runtime_options import ReaderOptions
from .core_processors.reader_core_docx import (
    get_docx_text,
    get_readers_docx_text,
)
from .core_processors.reader_core_pdf import (
    get_pdf_text,
    get_readers_pdf_text,
)
from .core_processors.reader_core_ocr_optimizer import (
    get_image_as_cv,
    get_image_as_pil,
    get_readers_image_as_cv,
    get_readers_image_as_pil,
    normalize_image_orientation,
    normalize_readers_image_orientation,
)
from .core_processors.reader_core_ocr_runner import (
    run_ocr_pages,
    run_readers_ocr_pages,
)
from .core_processors.reader_core_ocr_tables import (
    extract_tables_from_image,
    process_readers_tables_from_image,
)
from .core_processors.reader_core_tables_light_detector import (
    LightTableDetector,
    ReadersLightTableDetector,
)

UnifiedReaders = ReadersOrchestrator

__all__ = [
    "ReaderOptions",
    "UnifiedReaders",
    "get_docx_text",
    "get_readers_docx_text",
    "get_pdf_text",
    "get_readers_pdf_text",
    "normalize_image_orientation",
    "normalize_readers_image_orientation",
    "get_image_as_cv",
    "get_readers_image_as_cv",
    "get_image_as_pil",
    "get_readers_image_as_pil",
    "run_ocr_pages",
    "run_readers_ocr_pages",
    "extract_tables_from_image",
    "process_readers_tables_from_image",
    "LightTableDetector",
    "ReadersLightTableDetector",
]
