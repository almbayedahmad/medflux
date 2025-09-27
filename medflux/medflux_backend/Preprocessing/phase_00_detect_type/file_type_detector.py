from __future__ import annotations
"""File type detection heuristics using the improved PDF analyser."""
import mimetypes
import os
from typing import Any, Dict, List, Tuple

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional dependency
    fitz = None

from .file_type_enum import FileType
from .file_type_result import FileTypeResult

DEFAULT_SAMPLE_PAGES = 5
DEFAULT_TOPK_IMAGE_PAGES = 2
DEFAULT_IMG_AREA_THR = 0.35
DEFAULT_TEXT_LEN_THR = 200
DEFAULT_WORDS_THR = 15
DEFAULT_BLOCKS_THR = 3

DEFAULT_RECO: Dict[str, Any] = {
    "mode": "native",
    "dpi": 200,
    "psm": 6,
    "tables_mode": "light",
    "lang": "deu+eng",
}

DOCX_EXTS = {".docx"}
TXT_EXTS = {
    ".txt",
    ".log",
    ".md",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}


__all__ = [
    "DEFAULT_SAMPLE_PAGES",
    "DEFAULT_TOPK_IMAGE_PAGES",
    "DEFAULT_IMG_AREA_THR",
    "DEFAULT_TEXT_LEN_THR",
    "DEFAULT_WORDS_THR",
    "DEFAULT_BLOCKS_THR",
    "detect_file_type",
    "detect_many",
    "detect_file_type_improved",
    "detect_many_improved",
]


def _guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or ""


def _page_image_area_ratio(page) -> float:
    try:
        rect = page.rect
        page_area = float(rect.width * rect.height) if rect else 1.0
        images = page.get_images(full=True) or []
        image_area = 0.0
        try:
            raw = page.get_text("rawdict") or {"blocks": []}
            for block in raw.get("blocks", []):
                if block.get("type") == 1 and "bbox" in block:
                    x0, y0, x1, y1 = block["bbox"]
                    image_area += max(0.0, (x1 - x0) * (y1 - y0))
        except Exception:
            image_area = max(image_area, 0.1 * page_area * len(images))
        if page_area <= 0:
            return 0.0
        return float(max(0.0, min(1.0, image_area / page_area)))
    except Exception:
        return 0.0


def _analyze_page(
    page,
    text_len_thr: int,
    words_thr: int,
    blocks_thr: int,
    img_area_thr: float,
) -> Dict[str, Any]:
    text = page.get_text("text") or ""
    words = page.get_text("words") or []
    blocks = page.get_text("blocks") or []
    img_count = len(page.get_images(full=True) or [])
    img_area = _page_image_area_ratio(page)

    native_score = sum(
        [
            int(len(text) >= text_len_thr),
            int(len(words) >= words_thr),
            int(len(blocks) >= blocks_thr),
        ]
    )

    ocr_score = sum(
        [
            int(img_count >= 1),
            int(img_area >= img_area_thr),
            int(len(text) < text_len_thr and len(words) < words_thr),
        ]
    )

    if native_score > ocr_score:
        mode = "native"
    elif ocr_score > native_score:
        mode = "ocr"
    else:
        mode = "unclear"

    return {
        "text_len": len(text),
        "words": len(words),
        "blocks": len(blocks),
        "image_count": img_count,
        "image_area_ratio": round(float(img_area), 3),
        "native_score": native_score,
        "ocr_score": ocr_score,
        "page_mode": mode,
    }


def detect_pdf(
    path: str,
    sample_pages: int = DEFAULT_SAMPLE_PAGES,
    topk_image_pages: int = DEFAULT_TOPK_IMAGE_PAGES,
    img_area_thr: float = DEFAULT_IMG_AREA_THR,
    text_len_thr: int = DEFAULT_TEXT_LEN_THR,
    words_thr: int = DEFAULT_WORDS_THR,
    blocks_thr: int = DEFAULT_BLOCKS_THR,
) -> Dict[str, Any]:
    if fitz is None:
        return {"pages": 0, "sampled_pages": 0, "scanned": None, "confidence": 0.0}

    try:
        doc = fitz.open(path)
    except Exception:
        return {"pages": 0, "sampled_pages": 0, "scanned": None, "confidence": 0.0}
    total_pages = len(doc) or 0
    if total_pages == 0:
        return {"pages": 0, "sampled_pages": 0, "scanned": None, "confidence": 0.0}

    ratios: List[Tuple[int, float]] = []
    for index in range(total_pages):
        try:
            page = doc.load_page(index)
            ratios.append((index, _page_image_area_ratio(page)))
        except Exception:
            ratios.append((index, 0.0))
    ratios_sorted = sorted(ratios, key=lambda item: item[1], reverse=True)

    mid = total_pages // 2
    base = {0, max(0, mid), total_pages - 1}
    topk = [idx for (idx, _ratio) in ratios_sorted[: max(0, min(topk_image_pages, total_pages))]]
    sample_indices = sorted(base.union(topk))[: max(1, min(sample_pages, len(base.union(topk))))]

    per_page = []
    native_count = 0
    ocr_count = 0
    for index in sample_indices:
        page = doc.load_page(index)
        stats = _analyze_page(page, text_len_thr, words_thr, blocks_thr, img_area_thr)
        per_page.append({"page_no": index + 1, **stats})
        if stats["page_mode"] == "native":
            native_count += 1
        elif stats["page_mode"] == "ocr":
            ocr_count += 1

    meta: Dict[str, Any] = {
        "pages": total_pages,
        "sampled_pages": len(sample_indices),
        "sample_indices": [idx + 1 for idx in sample_indices],
        "per_page": per_page,
        "pages_native": native_count,
        "pages_ocr": ocr_count,
    }

    max_img_ratio = max((ratio for (_, ratio) in ratios_sorted), default=0.0)
    if ocr_count >= len(sample_indices) and native_count == 0:
        meta.update({"mixed": False, "scanned": True, "confidence": 0.9})
    elif max_img_ratio >= 0.9 and native_count == 0:
        meta.update({"mixed": False, "scanned": True, "confidence": max(meta.get("confidence", 0.5), 0.9)})
    elif native_count > 0 and ocr_count > 0:
        total = max(1, native_count + ocr_count)
        balance = 1.0 - abs(native_count - ocr_count) / total
        meta.update({"mixed": True, "scanned": False, "confidence": round(0.6 + 0.4 * balance, 3)})
    elif any(ratio >= img_area_thr for (_, ratio) in ratios_sorted[: max(2, len(sample_indices))]):
        meta.update({"mixed": True, "scanned": False, "confidence": max(meta.get("confidence", 0.5), 0.7)})
    elif native_count >= len(sample_indices) and ocr_count == 0:
        meta.update({"mixed": False, "scanned": False, "confidence": 0.9})
    else:
        meta.update({"mixed": False, "scanned": None, "confidence": 0.5})

    return meta


def detect_file_type(
    path: str,
    sample_pages: int = DEFAULT_SAMPLE_PAGES,
    topk_image_pages: int = DEFAULT_TOPK_IMAGE_PAGES,
    img_area_thr: float = DEFAULT_IMG_AREA_THR,
    text_len_thr: int = DEFAULT_TEXT_LEN_THR,
    words_thr: int = DEFAULT_WORDS_THR,
    blocks_thr: int = DEFAULT_BLOCKS_THR,
) -> FileTypeResult:
    ext = os.path.splitext(path)[1].lower()
    mime = _guess_mime(path)

    if ext == ".pdf" or (mime and mime.endswith("pdf")):
        meta = detect_pdf(path, sample_pages, topk_image_pages, img_area_thr, text_len_thr, words_thr, blocks_thr)
        scanned = meta.get("scanned")
        mixed = meta.get("mixed", False)
        confidence = float(meta.get("confidence", 0.0))
        if scanned is True:
            file_type = FileType.PDF_SCANNED
            recommended: Dict[str, Any] = {"mode": "ocr", "dpi": 320, "psm": 6, "tables_mode": "light", "lang": "deu+eng"}
            ocr_rec = True
        elif mixed:
            file_type = FileType.PDF_MIXED
            recommended = {"mode": "mixed", "dpi": 300, "psm": 6, "tables_mode": "light", "lang": "deu+eng"}
            ocr_rec = True
        else:
            file_type = FileType.PDF_TEXT
            recommended = dict(DEFAULT_RECO)
            ocr_rec = False
        details = {
            "pages": meta.get("pages"),
            "sampled_pages": meta.get("sampled_pages"),
            "sample_indices": meta.get("sample_indices"),
            "per_page": meta.get("per_page"),
            "pages_native": meta.get("pages_native"),
            "pages_ocr": meta.get("pages_ocr"),
        }
        return FileTypeResult(
            file_path=path,
            ext=ext,
            mime=mime,
            file_type=file_type,
            ocr_recommended=ocr_rec,
            details=details,
            confidence=confidence,
            recommended=recommended,
        )

    if ext in DOCX_EXTS or (mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        recommended = {"mode": "native", "tables_mode": "light", "lang": "deu+eng"}
        return FileTypeResult(path, ext, mime, FileType.DOCX, False, {"note": "docx"}, confidence=0.95, recommended=recommended)

    if ext in TXT_EXTS or (mime and (mime.startswith("text/") or "json" in mime or "yaml" in mime or "csv" in mime)):
        recommended = {"mode": "native", "tables_mode": "off", "lang": "deu+eng"}
        return FileTypeResult(path, ext, mime, FileType.TXT, False, {"note": "text"}, confidence=0.95, recommended=recommended)

    if ext in IMAGE_EXTS or (mime and mime.startswith("image/")):
        recommended = {"mode": "ocr", "dpi": 320, "psm": 6, "tables_mode": "light", "lang": "deu+eng"}
        return FileTypeResult(path, ext, mime, FileType.IMAGE, True, {"note": "image"}, confidence=0.95, recommended=recommended)

    return FileTypeResult(
        path,
        ext,
        mime,
        FileType.UNKNOWN,
        False,
        {"note": "unknown"},
        confidence=0.3,
        recommended={"mode": "mixed", "tables_mode": "light", "lang": "deu+eng"},
    )


def detect_many(paths: List[str], **kwargs) -> List[FileTypeResult]:
    results: List[FileTypeResult] = []
    for path in paths:
        try:
            results.append(detect_file_type(path, **kwargs))
        except Exception as exc:
            results.append(
                FileTypeResult(
                    path,
                    os.path.splitext(path)[1].lower(),
                    _guess_mime(path),
                    FileType.UNKNOWN,
                    False,
                    {"error": f"detect_failed: {exc}"},
                    confidence=0.0,
                    recommended={"mode": "mixed"},
                )
            )
    return results


def detect_file_type_improved(*args, **kwargs) -> FileTypeResult:
    """Backward compatible alias for older imports."""
    return detect_file_type(*args, **kwargs)


def detect_many_improved(*args, **kwargs) -> List[FileTypeResult]:
    """Backward compatible alias for older imports."""
    return detect_many(*args, **kwargs)
