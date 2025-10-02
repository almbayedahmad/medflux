from typing import Any, Dict, List

READERS_REQUIRED_TOP: List[str] = [
    "schema_version",
    "run_id",
    "doc_meta",
    "per_page_stats",
    "text_blocks",
    "warnings",
    "logs",
]

READERS_OPTIONAL_TOP: List[str] = [
    "pipeline_id",
    "table_candidates",
    "zones",
    "warnings_codes",
    "logs_structured",
    "error_code",
]


SCHEMA_VERSION: str = "readers-1.0"
