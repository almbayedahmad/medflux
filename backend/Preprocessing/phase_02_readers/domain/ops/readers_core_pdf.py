# PURPOSE:
#   PDF text extraction helpers for the readers stage.
#
# OUTCOME:
#   Extracts plain text from PDFs using PyMuPDF to feed native readers flows.
#
# INPUTS:
#   - Path to PDF and optional page limits.
#
# OUTPUTS:
#   - Extracted text as a normalized string (in-memory).
#
# DEPENDENCIES:
#   - Optional: PyMuPDF (fitz).
from __future__ import annotations

"""PDF text extraction helpers for the readers runtime."""

from typing import Optional

try:
    import fitz  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore
    FITZ_IMPORT_ERROR = exc
else:
    FITZ_IMPORT_ERROR = None


def get_pdf_text(path: str, max_pages: Optional[int] = None) -> str:
    """Return concatenated text extracted from a PDF using PyMuPDF."""

    if fitz is None:  # pragma: no cover - dependency missing at runtime
        raise RuntimeError("PyMuPDF (fitz) is required to read PDF text") from FITZ_IMPORT_ERROR

    doc = fitz.open(path)
    try:
        total_pages = len(doc)
        page_indexes = range(total_pages) if max_pages is None else range(min(max_pages, total_pages))
        parts = []
        for index in page_indexes:
            page = doc.load_page(index)
            text = page.get_text("text") or ""
            if text.strip():
                parts.append(text.rstrip())
        return "\n\n".join(parts).strip()
    finally:
        doc.close()


def get_readers_pdf_text(path: str) -> str:
    """Compatibility alias mirroring the legacy helper name."""

    return get_pdf_text(path)


__all__ = ["get_pdf_text", "get_readers_pdf_text"]
