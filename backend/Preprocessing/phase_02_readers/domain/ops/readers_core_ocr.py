# PURPOSE:
#   OCR execution helpers and merge logic for readers.
#
# OUTCOME:
#   Runs OCR when needed and merges native/OCR text heuristically to maximize
#   content quality for downstream phases.
#
# INPUTS:
#   - File paths, page selection, orchestrator options (lang, psm, dpi, etc.).
#
# OUTPUTS:
#   - In-memory OCR results and merged text fed back to orchestrator records.
#
# DEPENDENCIES:
#   - Optional: PyMuPDF (fitz), PIL, pytesseract; standard library.
from __future__ import annotations

"""OCR execution helpers for the readers runtime orchestrator."""

import io
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:  # Optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - PyMuPDF not installed
    fitz = None

try:  # Optional dependency
    from PIL import Image
except Exception:  # pragma: no cover - PIL missing at runtime
    Image = None

try:  # Optional dependency
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - pytesseract missing
    pytesseract = None

from core.preprocessing.cross_phase.helpers.main_pre_helpers_image import process_readers_preprocess_pipeline, to_readers_pil_image
from core.monitoring import observe_ocr_time_ms, observe_ocr_confidence


def compute_readers_clamped_dpi(value: int, *, minimum: int = 200, maximum: int = 450) -> int:
    return max(minimum, min(maximum, value))


def compute_readers_median_font_size(page) -> Optional[float]:
    try:
        data = page.get_text("dict")
    except Exception:
        return None
    sizes: List[float] = []
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                size = span.get("size")
                if isinstance(size, (int, float)) and size > 0:
                    sizes.append(float(size))
    if not sizes:
        return None
    sizes.sort()
    return float(sizes[len(sizes) // 2])


def compute_readers_recommended_dpi(page, default: int = 300, mode: str = "fixed") -> int:
    if mode != "auto":
        return compute_readers_clamped_dpi(int(default))
    median = compute_readers_median_font_size(page)
    if median is None:
        dpi = 350
    elif median < 7.5:
        dpi = 400
    elif median < 9.5:
        dpi = 350
    else:
        dpi = 300
    return compute_readers_clamped_dpi(dpi)


def run_ocr_pages(
    pdf_path: str,
    *,
    page_numbers_1based: List[int],
    lang: str = "deu+eng",
    dpi: int = 300,
    psm: int = 3,
    oem: int = 1,
    pre: Optional[str] = None,
    save_tsv: bool = False,
    outdir: Optional[Path] = None,
    dpi_mode: str = "fixed",
) -> List[Dict[str, object]]:
    """Run OCR on the requested PDF pages using PyMuPDF + Tesseract."""

    if fitz is None or pytesseract is None or Image is None:
        raise RuntimeError("OCR prerequisites missing: PyMuPDF, PIL, pytesseract")

    doc = fitz.open(pdf_path)
    results: List[Dict[str, object]] = []
    try:
        for page_number in page_numbers_1based:
            page = doc.load_page(page_number - 1)
            dpi_used = compute_readers_recommended_dpi(page, default=dpi, mode=dpi_mode)

            zoom = dpi_used / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            if pre:
                steps = [step for step in pre.split(",") if step.strip()]
                if steps:
                    try:
                        img = process_readers_preprocess_pipeline(img, steps)
                    except Exception:
                        pass

            config = f"--psm {psm} --oem {oem}"
            start = time.time()
            text = pytesseract.image_to_string(img, lang=lang, config=config) or ""
            tsv = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.STRING)
            elapsed = int((time.time() - start) * 1000)

            avg_conf = None
            try:
                rows = [row for row in tsv.splitlines()[1:] if row.strip()]
                confidences = []
                for row in rows:
                    parts = row.split("\t")
                    if len(parts) > 10:
                        try:
                            value = float(parts[10])
                        except Exception:
                            continue
                        if value >= 0:
                            confidences.append(value)
                if confidences:
                    avg_conf = round(sum(confidences) / len(confidences), 2)
            except Exception:
                avg_conf = None

            results.append(
                {
                    "page_no": page_number,
                    "mode": "ocr",
                    "text": text,
                    "text_len": len(text),
                    "avg_conf": avg_conf,
                    "tokens": None,
                    "dpi": dpi_used,
                    "oem": oem,
                    "pre": pre,
                    "time_ms": elapsed,
                }
            )
            try:
                observe_ocr_time_ms(float(elapsed))
                if avg_conf is not None:
                    observe_ocr_confidence(float(avg_conf))
            except Exception:
                pass

            if save_tsv and outdir is not None:
                outdir.mkdir(parents=True, exist_ok=True)
                (outdir / f"ocr_page_{page_number:03d}.tsv").write_text(tsv, encoding="utf-8")
    finally:
        doc.close()

    return results


def run_pdf_ocr(orchestrator, pdf_path: Path, pages: List[int]) -> Dict[int, Dict[str, object]]:
    """Run OCR for orchestrator integration, returning a page lookup."""

    try:
        debug_dir = orchestrator.readers_dir / "ocr_debug" if orchestrator.opts.verbose else None
        pre_config = "deskew,clahe" if orchestrator.opts.use_pre else None
        start = time.perf_counter()
        results = run_ocr_pages(
            str(pdf_path),
            page_numbers_1based=pages,
            lang=orchestrator.opts.lang,
            dpi=orchestrator.opts.dpi,
            psm=orchestrator.opts.psm,
            oem=orchestrator.opts.oem,
            pre=pre_config,
            save_tsv=orchestrator.opts.verbose,
            outdir=debug_dir,
            dpi_mode=orchestrator.opts.dpi_mode,
        )
        orchestrator._timings["ocr"] += (time.perf_counter() - start) * 1000.0
    except RuntimeError as exc:
        orchestrator._log_warning("ocr_unavailable")
        orchestrator._log_tool_event(
            "ocr_runner",
            "unavailable",
            details={"reason": str(exc)},
        )
        return {}
    except Exception as exc:  # pragma: no cover - external OCR errors
        orchestrator._log_warning(f"ocr_runner_error:{exc}")
        orchestrator._log_tool_event(
            "ocr_runner",
            "error",
            details={"error": str(exc), "pages": pages},
        )
        return {}

    lookup: Dict[int, Dict[str, object]] = {}
    for item in results:
        page_no = int(item.get("page_no", 0) or 0)
        if page_no > 0:
            lookup[page_no] = item

    status = "ok" if lookup else "empty"
    details = {"pages": pages, "covered": sorted(lookup.keys()), "lang": orchestrator.opts.lang}
    if orchestrator.opts.use_pre:
        details["pre"] = "deskew,clahe"
    orchestrator._log_tool_event("ocr_runner", status, details=details)
    return lookup


def process_readers_ocr_result(fallback_text: str, ocr_data: Optional[Dict[str, object]]) -> Tuple[str, float, int, float]:
    """Translate a raw OCR payload into text, confidence, word count, and timing."""

    if not ocr_data:
        text = fallback_text or ""
        return text, 0.0, len(text.split()), 0.0
    text = ocr_data.get("text") or ""
    conf = float(ocr_data.get("avg_conf") or 0.0)
    time_ms = float(ocr_data.get("time_ms") or 0.0)
    words = len(text.split()) if text else int(ocr_data.get("tokens") or 0)
    return text, conf, words, time_ms


def process_readers_merge_text(native_text: str, ocr_text: str, native_conf: float, ocr_conf: float) -> Tuple[str, float]:
    """Merge native and OCR text heuristically, returning the chosen text and confidence."""

    if not native_text.strip():
        return ocr_text, ocr_conf
    if not ocr_text.strip():
        return native_text, native_conf
    len_native = len(native_text)
    len_ocr = len(ocr_text)
    if len_ocr > len_native * 1.25:
        return ocr_text, max(ocr_conf, native_conf)
    if len_native > len_ocr * 1.25:
        return native_text, max(native_conf, ocr_conf)
    merged_conf = round(min(99.0, max(native_conf, ocr_conf, (native_conf + ocr_conf) / 2.0)), 2)
    return native_text, merged_conf


__all__ = [
    "run_ocr_pages",
    "run_pdf_ocr",
    "process_readers_ocr_result",
    "process_readers_merge_text",
]
