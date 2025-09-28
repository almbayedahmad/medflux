from __future__ import annotations

from typing import List, NotRequired, TypedDict


class TimingBreakdown(TypedDict, total=False):
    total_ms: float
    detect: float
    encoding: float
    readers: float
    text_extract: float
    ocr: float
    table_detect: float
    table_extract: float
    lang_detect: float
    cleaning: float
    merge: float
    summarize: float


class PerPageStat(TypedDict, total=False):
    page: int
    source: str
    conf: float
    ocr_words: int
    chars: int
    has_table: bool
    tables_found: int
    table_cells: int
    decision: str
    time_ms: float
    lang: str
    locale: str
    flags: List[str]
    ocr_conf_avg: NotRequired[float]


class TextBlock(TypedDict, total=False):
    id: str
    page: int
    text_raw: str
    text_lines: str
    bbox: List[float]
    reading_order_index: NotRequired[int]
    is_heading_like: NotRequired[bool]
    is_list_like: NotRequired[bool]
    lang: NotRequired[str]
    ocr_conf_avg: NotRequired[float]


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
    by_page: List[dict]
    doc: NotRequired[str]


class LocaleHints(TypedDict, total=False):
    overall: str
    by_page: List[dict]
    numbers_locale: NotRequired[str]
    dates_locale: NotRequired[str]


class DocMetaPayload(TypedDict, total=False):
    file_name: str
    file_type: str
    pages_count: int
    detected_encodings: str | None
    detected_languages: DetectedLanguages
    has_ocr: bool
    avg_ocr_conf: float
    timings_ms: TimingBreakdown
    per_page_stats: List[PerPageStat]
    text_blocks: List[TextBlock]
    tables_raw: List[RawTable]
    artifacts: List[Artifact]
    locale_hints: LocaleHints
    qa: QASection
    warnings: List[str]
    logs: List[str]
    processing_log: List[dict]
    visual_artifacts_path: str
    text_blocks_path: str
    tables_raw_path: str
