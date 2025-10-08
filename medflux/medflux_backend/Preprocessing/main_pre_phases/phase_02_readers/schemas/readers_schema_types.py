from __future__ import annotations

"""Consolidated type definitions for the readers stage."""

from typing import Any, Dict, List, NotRequired, TypedDict, Tuple


# Schema constants
READERS_REQUIRED_TOP: Tuple[str, ...] = (
    "schema_version",
    "run_id",
    "doc_meta",
    "per_page_stats",
    "text_blocks",
    "warnings",
    "logs",
)

READERS_OPTIONAL_TOP: Tuple[str, ...] = (
    "pipeline_id",
    "table_candidates",
    "zones",
    "warnings_codes",
    "logs_structured",
    "error_code",
)

SCHEMA_VERSION: str = "readers.v1"


# TypedDict definitions
class PageTiming(TypedDict):
    page: int
    time_ms: float


class TimingBreakdown(TypedDict, total=False):
    total_ms: float
    detect: float
    encoding: float
    readers: float
    text_extract: float
    ocr: float
    table_detect: float
    table_detect_light: float
    table_extract: float
    lang_detect: float
    cleaning: float
    merge: float
    summarize: float
    pagewise: List[PageTiming]


class PerPageStat(TypedDict, total=False):
    page: int
    source: str
    chars: int
    lang: str
    lang_share: Dict[str, float]
    ocr_conf: float
    ocr_words: int
    tables_found: int
    table_cells: int
    flags: List[str]
    rotation_deg: int
    skew_deg: float
    is_multi_column: bool
    columns_count: int
    page_size: Dict[str, float]
    noise_score: float
    text_density: float
    has_header_footer: bool
    has_images: bool
    images_count: int
    graphics_objects_count: int
    time_ms: float
    locale: str
    decision: str
    has_table: bool


class TextBlock(TypedDict, total=False):
    id: str
    page: int
    text_raw: str
    text_lines: List[str]
    bbox: List[float]
    token_count: int
    char_count: int
    reading_order_index: int
    lang: str
    lang_conf: float
    ocr_conf_avg: float
    is_heading_like: bool
    is_list_like: bool
    font_size: float
    is_bold: bool
    is_upper: bool
    paragraph_style: str
    list_level: int
    line_height: float
    baseline_y: float
    column_index: int
    indent_level: int
    numbering_marker: str
    block_type: str


class WordEntry(TypedDict, total=False):
    block_id: str
    page: int
    text: str
    bbox: List[float]
    ocr_conf: float


class ZoneEntry(TypedDict, total=False):
    page: int
    bbox: List[float]
    type: str


class RawTableCell(TypedDict, total=False):
    row: int
    col: int
    text: str
    bbox: NotRequired[List[float]]
    row_span: NotRequired[int]
    col_span: NotRequired[int]


class RawTable(TypedDict, total=False):
    id: str
    page: int
    bbox: NotRequired[List[float]]
    extraction_tool: str
    status: str
    cells: NotRequired[List[RawTableCell]]
    table_text: NotRequired[str]


class Artifact(TypedDict, total=False):
    page: int
    bbox: List[float]
    kind: str
    confidence: float
    source: str


class QASection(TypedDict, total=False):
    needs_review: bool
    pages: List[int]
    warnings: List[str]
    low_conf_pages: List[int]
    low_text_pages: List[int]
    tables_fail: bool
    reasons: List[str]
    summary: NotRequired[str]


class DetectedLanguages(TypedDict, total=False):
    overall: List[str]
    by_page: List[str]
    doc: str
    conf_doc: float


class LocaleHints(TypedDict, total=False):
    overall: str
    by_page: List[dict]
    numbers_locale: NotRequired[str]
    dates_locale: NotRequired[str]


class DocMeta(TypedDict, total=False):
    file_name: str
    file_type: str
    pages_count: int
    detected_encodings: str | None
    detected_languages: DetectedLanguages
    has_ocr: bool
    avg_ocr_conf: float
    coordinate_unit: str
    bbox_origin: str
    pdf_locked: bool
    ocr_engine: str
    ocr_engine_version: str
    ocr_langs: str
    reader_version: str
    preprocess_applied: List[str]
    content_hash: str
    has_text_layer: bool
    timings_ms: TimingBreakdown
    words: List[WordEntry]
    artifacts: List[Artifact]
    locale_hints: LocaleHints
    warnings: List[str]
    logs: List[str]
    processing_log: List[dict]
    visual_artifacts_path: str
    text_blocks_path: str


class ReadersOutput(TypedDict, total=False):
    schema_version: str
    run_id: str
    pipeline_id: str
    doc_meta: DocMeta
    per_page_stats: List[PerPageStat]
    text_blocks: List[TextBlock]
    warnings: List[str]
    logs: List[str]
    table_candidates: List[Dict[str, Any]]
    zones: List[ZoneEntry]
    warnings_codes: List[str]
    logs_structured: List[Dict[str, Any]]
    error_code: str


__all__ = [
    # Schema constants
    "READERS_REQUIRED_TOP",
    "READERS_OPTIONAL_TOP", 
    "SCHEMA_VERSION",
    # TypedDict classes
    "PageTiming",
    "TimingBreakdown",
    "PerPageStat",
    "TextBlock",
    "WordEntry",
    "ZoneEntry",
    "RawTableCell",
    "RawTable",
    "Artifact",
    "QASection",
    "DetectedLanguages",
    "LocaleHints",
    "DocMeta",
    "ReadersOutput",
]