from __future__ import annotations
"""High-level file type detection wrapper around the improved detector pipeline."""
from typing import List

from ..pipeline import detector_improved as _detector
from .file_type_enum import FileType
from .file_type_result import FileTypeResult

_FILETYPE_MAP = {
    _detector.PDF_TEXT: FileType.PDF_TEXT,
    _detector.PDF_SCANNED: FileType.PDF_SCANNED,
    _detector.PDF_MIXED: FileType.PDF_MIXED,
    'docx': FileType.DOCX,
    'txt': FileType.TXT,
    'image': FileType.IMAGE,
    _detector.UNKNOWN: FileType.UNKNOWN,
}


def _convert_result(res: _detector.FileTypeResult) -> FileTypeResult:
    file_type = _FILETYPE_MAP.get(res.file_type, FileType.UNKNOWN)
    return FileTypeResult(
        file_path=res.file_path,
        ext=res.ext,
        mime=res.mime,
        file_type=file_type,
        ocr_recommended=res.ocr_recommended,
        details=res.details,
        confidence=float(res.confidence or 0.0),
        recommended=res.recommended,
    )


def detect_file_type(path: str, **kwargs) -> FileTypeResult:
    """Detect the file type using the improved heuristics and normalise the result."""
    improved = _detector.detect_file_type_improved(path, **kwargs)
    return _convert_result(improved)


def detect_many(paths: List[str], **kwargs) -> List[FileTypeResult]:
    """Vectorised variant of :func:`detect_file_type`."""
    results: List[FileTypeResult] = []
    for res in _detector.detect_many_improved(paths, **kwargs):
        try:
            results.append(_convert_result(res))
        except Exception:
            results.append(
                FileTypeResult(
                    file_path=res.file_path,
                    ext=res.ext,
                    mime=res.mime,
                    file_type=FileType.UNKNOWN,
                    ocr_recommended=False,
                    details={"error": "convert_failed"},
                    confidence=0.0,
                    recommended={"mode": "mixed"},
                )
            )
    return results
