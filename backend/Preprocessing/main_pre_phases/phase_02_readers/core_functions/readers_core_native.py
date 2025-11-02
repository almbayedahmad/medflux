from __future__ import annotations

"""Native document processing helpers for the readers runtime orchestrator."""

import time
from pathlib import Path
from typing import Dict, List, Optional

try:  # Optional at runtime
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None

try:  # Optional at runtime
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

try:  # Optional at runtime
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

from ..schemas.readers_schema_models import PageRecord
from .readers_core_docx import get_docx_text
from .readers_core_pdf import get_pdf_text
from .readers_core_ocr import process_readers_ocr_result, run_pdf_ocr, process_readers_merge_text
from .readers_core_tables import process_readers_collect_tables
from .readers_core_artifacts import process_readers_collect_image_artifacts

DOCX_PAGE_WIDTH_EMU = 8.27 * 914400
DOCX_PAGE_HEIGHT_EMU = 11.69 * 914400


def compute_readers_safe_avg_conf(conf_list) -> float:
    values: List[float] = []
    for value in conf_list or []:
        try:
            float_value = float(value)
        except Exception:
            continue
        if float_value > 0:
            values.append(float_value)
    return sum(values) / len(values) if values else 0.0


def process_readers_docx_native(orchestrator, path: Path) -> None:
    start = time.perf_counter()
    try:
        text = get_docx_text(str(path))
    except Exception as exc:
        orchestrator._log_warning(f"docx_error:{exc}")
        orchestrator._log_tool_event("docx_reader", "error", details={"file": str(path), "error": str(exc)})
        return
    elapsed = (time.perf_counter() - start) * 1000.0
    words = len(text.split()) if text else 0
    conf = 90.0 if text else 0.0
    orchestrator._log_tool_event("docx_reader", "ok", details={"file": str(path), "words": words})
    orchestrator._page_geometry[1] = {
        "width": float(DOCX_PAGE_WIDTH_EMU),
        "height": float(DOCX_PAGE_HEIGHT_EMU),
        "rotation": 0.0,
        "images_count": 0,
    }
    orchestrator._records.append(
        PageRecord(
            file=str(path),
            page=1,
            source="native",
            text=text,
            conf=conf,
            time_ms=elapsed,
            words=words,
            chars=len(text or ""),
        )
    )
    orchestrator._page_decisions.append("native")
    orchestrator._add_simple_block(1, text, "native", None)


def process_readers_text_native(orchestrator, path: Path) -> None:
    start = time.perf_counter()
    try:
        text = Path(path).read_text("utf-8", errors="replace")
    except Exception as exc:
        orchestrator._log_warning(f"text_error:{exc}")
        orchestrator._log_tool_event("text_reader", "error", details={"file": str(path), "error": str(exc)})
        return
    elapsed = (time.perf_counter() - start) * 1000.0
    words = len(text.split()) if text else 0
    conf = 92.0 if text else 0.0
    orchestrator._log_tool_event("text_reader", "ok", details={"file": str(path), "words": words})
    orchestrator._records.append(
        PageRecord(
            file=str(path),
            page=1,
            source="native",
            text=text,
            conf=conf,
            time_ms=elapsed,
            words=words,
            chars=len(text or ""),
        )
    )
    orchestrator._page_decisions.append("native")
    orchestrator._add_simple_block(1, text, "native", None)


def process_readers_pdf_fallback(orchestrator, path: Path) -> None:
    try:
        text = get_pdf_text(str(path))
    except Exception as exc:
        orchestrator._log_warning(f"pdf_native_error:{exc}")
        orchestrator._log_tool_event("pdf_native", "error", details={"file": str(path), "error": str(exc)})
        return
    words = len(text.split()) if text else 0
    conf = 80.0 if text else 0.0
    orchestrator._log_tool_event("pdf_native", "ok", details={"file": str(path), "words": words})
    orchestrator._records.append(
        PageRecord(
            file=str(path),
            page=1,
            source="native",
            text=text,
            conf=conf,
            time_ms=0.0,
            words=words,
            chars=len(text or ""),
        )
    )
    orchestrator._page_decisions.append("native")
    orchestrator._add_simple_block(1, text, "native", None)


def compute_readers_image_stats(page) -> tuple[float, int]:
    if fitz is None:
        return 0.0, 0
    try:
        images = page.get_images(full=True)
    except Exception:
        return 0.0, 0
    if not images:
        return 0.0, 0
    page_area = max(page.rect.width * page.rect.height, 1.0)
    area_acc = 0.0
    for image in images:
        xref = image[0]
        bbox = None
        try:
            info = page.get_image_info(xref)
            if isinstance(info, list) and info:
                bbox = info[0].get("bbox")
            elif isinstance(info, dict):
                bbox = info.get("bbox")
        except Exception:
            bbox = None
        if bbox:
            x0, y0, x1, y1 = bbox
            width = max(x1 - x0, 0.0)
            height = max(y1 - y0, 0.0)
            area_acc += width * height
        else:
            width = image[2]
            height = image[3]
            area_acc += float(width * height)
    coverage = min(area_acc / page_area, 1.5)
    return max(coverage, 0.0), len(images)


def process_readers_pdf_document(orchestrator, path: Path) -> None:
    if fitz is None:
        orchestrator._log_warning("pymupdf_missing")
        orchestrator._log_tool_event("pymupdf", "missing", details={"file": str(path)})
        process_readers_pdf_fallback(orchestrator, path)
        return
    try:
        doc = fitz.open(path)
        orchestrator._log_tool_event("pymupdf_open", "ok", details={"file": str(path)})
    except Exception as exc:
        orchestrator._log_warning(f"pdf_open_error:{exc}")
        orchestrator._log_tool_event("pymupdf_open", "error", details={"file": str(path), "error": str(exc)})
        process_readers_pdf_fallback(orchestrator, path)
        return

    native_map: Dict[int, Dict[str, float]] = {}
    overlay_candidates: List[int] = []
    ocr_needed: List[int] = []
    mode = (orchestrator.opts.mode or "mixed").lower()

    for index, page in enumerate(doc):
        page_no = index + 1
        native_data = orchestrator._native_page_data(page, page_no)
        coverage, image_count = compute_readers_image_stats(page)
        process_readers_collect_image_artifacts(orchestrator, page, page_no)
        native_data["coverage"] = coverage
        native_data["image_count"] = image_count
        native_map[page_no] = native_data
        rect = getattr(page, "rect", None)
        if rect is not None:
            orchestrator._page_geometry[page_no] = {
                "width": float(getattr(rect, "width", 0.0)),
                "height": float(getattr(rect, "height", 0.0)),
                "rotation": float(getattr(page, "rotation", 0) or 0.0),
                "images_count": int(image_count),
            }
        else:
            orchestrator._page_geometry.setdefault(
                page_no,
                {
                    "width": 0.0,
                    "height": 0.0,
                    "rotation": float(getattr(page, "rotation", 0) or 0.0),
                    "images_count": int(image_count),
                },
            )
        if mode == "ocr":
            ocr_needed.append(page_no)
            continue
        if mode == "native":
            if not native_data.get("text", "").strip():
                ocr_needed.append(page_no)
            elif orchestrator._should_overlay(
                native_data.get("text", ""),
                native_data.get("conf", 0.0),
                coverage,
                image_count,
            ):
                overlay_candidates.append(page_no)
                ocr_needed.append(page_no)
            continue
        if orchestrator._should_use_native_mixed(
            native_data.get("conf", 0.0),
            native_data.get("block_count", 0),
            native_data.get("words", 0),
            coverage,
        ):
            if orchestrator._should_overlay(
                native_data.get("text", ""),
                native_data.get("conf", 0.0),
                coverage,
                image_count,
            ):
                overlay_candidates.append(page_no)
                ocr_needed.append(page_no)
        else:
            ocr_needed.append(page_no)

    ocr_lookup: Dict[int, Dict[str, object]] = {}
    if ocr_needed:
        unique_pages = sorted(set(ocr_needed))
        ocr_lookup = run_pdf_ocr(orchestrator, path, unique_pages)

    for index, page in enumerate(doc):
        page_no = index + 1
        native_data = native_map.get(page_no, {})
        native_text = native_data.get("text", "")
        native_conf = native_data.get("conf", 0.0)
        native_words = native_data.get("words", 0)
        time_ms = native_data.get("time_ms", 0.0)
        coverage = native_data.get("coverage", 0.0)
        image_count = native_data.get("image_count", 0)
        decision = "native"
        final_text = native_text
        final_conf = native_conf
        final_words = native_words
        final_time = time_ms
        native_blocks = native_data.get("blocks") or []
        ocr_data = ocr_lookup.get(page_no)
        ocr_avg_conf = None
        if ocr_data and ocr_data.get("avg_conf") is not None:
            try:
                ocr_avg_conf = float(ocr_data.get("avg_conf") or 0.0)
            except Exception:
                ocr_avg_conf = float(ocr_data.get("avg_conf"))
        if mode == "ocr":
            final_text, final_conf, final_words, final_time = process_readers_ocr_result(native_text, ocr_data)
            decision = "ocr"
        elif mode == "native":
            if not native_text.strip():
                final_text, final_conf, final_words, final_time = process_readers_ocr_result(native_text, ocr_data)
                decision = "ocr"
            elif page_no in overlay_candidates and ocr_data:
                merged_text, merged_conf = process_readers_merge_text(
                    native_text,
                    ocr_data.get("text") or "",
                    native_conf,
                    float(ocr_data.get("avg_conf") or 0.0),
                )
                final_text = merged_text
                final_conf = merged_conf
                final_words = len(final_text.split())
                final_time += float(ocr_data.get("time_ms") or 0.0)
                decision = "native+ocr"
        else:  # mixed
            if page_no in ocr_lookup and page_no not in overlay_candidates:
                final_text, final_conf, final_words, final_time = process_readers_ocr_result(native_text, ocr_data)
                decision = "ocr"
            elif page_no in overlay_candidates and ocr_data:
                merged_text, merged_conf = process_readers_merge_text(
                    native_text,
                    ocr_data.get("text") or "",
                    native_conf,
                    float(ocr_data.get("avg_conf") or 0.0),
                )
                final_text = merged_text
                final_conf = merged_conf
                final_words = len(final_text.split())
                final_time += float(ocr_data.get("time_ms") or 0.0)
                decision = "native+ocr"
            elif not native_text.strip():
                final_text, final_conf, final_words, final_time = process_readers_ocr_result(native_text, ocr_data)
                decision = "ocr"

        orchestrator._record_page_blocks(page_no, decision, native_blocks, final_text, ocr_avg_conf)
        if not final_text.strip():
            orchestrator._log_warning(f"empty_page_text:p{page_no}")
        orchestrator._records.append(
            PageRecord(
                file=str(path),
                page=page_no,
                source=decision,
                text=final_text,
                conf=round(final_conf, 2),
                time_ms=round(final_time, 2),
                words=final_words,
                chars=len(final_text or ""),
                ocr_conf_avg=ocr_avg_conf,
            )
        )
        orchestrator._page_decisions.append(decision)
        if final_text.strip():
            process_readers_collect_tables(orchestrator, page, path, page_no, decision, ocr_data)
        orchestrator._update_zones(page, page_no)
    doc.close()


def process_readers_ocr_image(orchestrator, path: Path) -> None:
    if Image is None or pytesseract is None:
        orchestrator._log_warning("image_ocr_unavailable")
        orchestrator._log_tool_event("image_ocr", "unavailable")
        return
    start = time.perf_counter()
    try:
        image = Image.open(path).convert("RGB")
        orchestrator._log_tool_event("image_open", "ok", details={"file": str(path)})
        width, height = image.size
        orchestrator._page_geometry[1] = {
            "width": float(width),
            "height": float(height),
            "rotation": 0.0,
            "images_count": 1,
        }
    except Exception as exc:
        orchestrator._log_warning(f"read_image_error:{exc}")
        orchestrator._log_tool_event("image_open", "error", details={"file": str(path), "error": str(exc)})
        return
    try:
        cfg = (
            f"-l {getattr(orchestrator.opts, 'lang', 'eng')} "
            f"--oem {getattr(orchestrator.opts, 'oem', 3)} --psm {getattr(orchestrator.opts, 'psm', 6)}"
        )
        data = pytesseract.image_to_data(image, output_type="dict", config=cfg)
        words = data.get("text", []) or []
        confs = data.get("conf", []) or []
        text = " \n".join(word for word in words if word and word.strip() and word != "-1")
        conf = compute_readers_safe_avg_conf(confs)
        orchestrator._log_tool_event(
            "pytesseract",
            "ok",
            details={"file": str(path), "lang": getattr(orchestrator.opts, 'lang', 'eng')},
        )
    except Exception as exc:
        orchestrator._log_warning(f"fallback_ocr_error:{exc}")
        orchestrator._log_tool_event("pytesseract", "error", details={"file": str(path), "error": str(exc)})
        text, conf = "", 0.0
    elapsed = (time.perf_counter() - start) * 1000.0
    orchestrator._records.append(
        PageRecord(
            file=str(path),
            page=1,
            source="ocr_image",
            text=text,
            conf=conf,
            time_ms=elapsed,
            words=len(text.split()),
            chars=len(text or ""),
            ocr_conf_avg=conf if text else None,
        )
    )
    orchestrator._page_decisions.append("ocr")
    orchestrator._add_simple_block(1, text, "ocr", conf)
    orchestrator._update_page_hints(1, text)


__all__ = [
    "process_readers_docx_native",
    "process_readers_text_native",
    "process_readers_pdf_fallback",
    "process_readers_pdf_document",
    "process_readers_ocr_image",
]
