# Reader-stage output schema definitions
from typing import Tuple

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

