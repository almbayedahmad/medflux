from __future__ import annotations
"""Lightweight readers shim with native, OCR, and document handlers."""
from pathlib import Path
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - optional deps at runtime
    fitz = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

try:
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

from .docx_reader import read_docx_to_text
from .pdf_reader import read_pdf_text

try:
    from . import ocr_runner
except Exception:  # pragma: no cover
    ocr_runner = None

try:
    from .ocr_table_reader import extract_tables_from_image
except Exception:  # pragma: no cover
    extract_tables_from_image = None

DOCX_EXTS = {".docx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
TEXT_EXTS = {".txt", ".log", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".ini", ".cfg", ".conf"}


@dataclass
class ReaderOptions:
    mode: str = "mixed"
    lang: str = "deu+eng"
    dpi_mode: str = "auto"
    oem: int = 3
    dpi: int = 300
    psm: int = 6
    workers: int = 4
    use_pre: bool = False
    export_xlsx: bool = False
    verbose: bool = False
    tables_mode: str = "light"
    save_table_crops: bool = False
    tables_min_words: int = 12
    table_detect_min_area: float = 9000.0
    table_detect_max_cells: int = 600
    blocks_threshold: int = 3
    native_ocr_overlay: bool = False
    overlay_area_thr: float = 0.35
    overlay_min_images: int = 1
    overlay_if_any_image: bool = False


@dataclass
class Summary:
    files: List[str]
    page_count: int
    avg_conf: float
    warnings: List[str]
    timings_ms: Dict[str, float]
    page_decisions: List[str]


@dataclass
class PageRecord:
    file: str
    page: int
    source: str
    text: str
    conf: float = 0.0
    time_ms: float = 0.0
    words: int = 0


@dataclass
class TableRecord:
    file: str
    page: int
    rows: List[List[str]]
    decision: str
    metrics: Optional[Dict[str, float]] = None


def _safe_avg_conf(conf_list) -> float:
    values: List[float] = []
    for value in conf_list or []:
        try:
            float_value = float(value)
        except Exception:
            continue
        if float_value > 0:
            values.append(float_value)
    return sum(values) / len(values) if values else 0.0


class UnifiedReaders:
    def __init__(self, outdir: Path, opts: ReaderOptions):
        self.base_outdir = Path(outdir)
        self.outdir = self.base_outdir
        self.readers_dir = self.base_outdir / "readers"
        self.opts = opts
        self._records: List[PageRecord] = []
        self._warnings: List[str] = []
        self._page_decisions: List[str] = []
        self._tables: List[TableRecord] = []
        self._table_flags: Set[int] = set()
        self._table_candidates: Dict[int, Dict[str, float]] = {}
        self._t0 = time.time()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _reset_state(self) -> None:
        self._records.clear()
        self._warnings.clear()
        self._page_decisions.clear()
        self._tables.clear()
        self._table_flags.clear()
        self._table_candidates.clear()
        self._t0 = time.time()

    def _log_warning(self, code: str) -> None:
        if code not in self._warnings:
            self._warnings.append(code)

    def _native_page_data(self, page) -> Dict[str, float]:
        start = time.perf_counter()
        text = ""
        block_count = 0
        words = 0
        try:
            text = page.get_text("text") or ""
        except Exception:
            text = ""
        try:
            blocks_dict = page.get_text("dict") or {}
        except Exception:
            blocks_dict = {}
        blocks = blocks_dict.get("blocks", []) if isinstance(blocks_dict, dict) else []
        block_count = len(blocks)
        if not text and blocks:
            try:
                text = "\n".join(span.get("text", "") for block in blocks for line in block.get("lines", []) for span in line.get("spans", []))
            except Exception:
                text = ""
        if text:
            words = len(text.split())
        else:
            words = 0
        conf = self._estimate_native_conf(text, block_count, words)
        elapsed = (time.perf_counter() - start) * 1000.0
        return {
            "text": text,
            "conf": conf,
            "words": words,
            "block_count": block_count,
            "time_ms": elapsed,
        }

    @staticmethod
    def _estimate_native_conf(text: str, block_count: int, words: int) -> float:
        if not text.strip():
            return 0.0
        block_factor = min(block_count, 8) / 8.0
        word_factor = min(words / 120.0, 1.0)
        char_factor = min(len(text) / 1500.0, 1.0)
        conf = 55.0 + block_factor * 20.0 + word_factor * 15.0 + char_factor * 10.0
        return round(min(conf, 96.0), 2)

    def _image_stats(self, page) -> Tuple[float, int]:
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

    def _should_overlay(self, text: str, conf: float, coverage: float, image_count: int) -> bool:
        if not self.opts.native_ocr_overlay:
            return False
        if image_count == 0:
            return False
        if image_count < self.opts.overlay_min_images and not (self.opts.overlay_if_any_image and image_count > 0):
            return False
        if coverage < self.opts.overlay_area_thr and not self.opts.overlay_if_any_image:
            return False
        if not text.strip():
            return True
        return conf < 85.0

    def _should_use_native_mixed(self, conf: float, block_count: int, words: int, coverage: float) -> bool:
        if conf == 0.0 or words == 0:
            return False
        if block_count >= max(1, self.opts.blocks_threshold) and conf >= 70.0:
            if coverage < 0.6:
                return True
        if conf >= 85.0 and words > 40:
            return True
        return False

    def _run_ocr(self, pdf_path: Path, pages: List[int]) -> Dict[int, Dict[str, object]]:
        if pytesseract is None or Image is None:
            self._log_warning("ocr_unavailable")
            return {}
        if ocr_runner is None:
            self._log_warning("ocr_runner_missing")
            return {}
        try:
            debug_dir = None
            if self.opts.verbose:
                debug_dir = self.readers_dir / "ocr_debug"
            results = ocr_runner.ocr_pages(
                str(pdf_path),
                page_numbers_1based=pages,
                lang=self.opts.lang,
                dpi=self.opts.dpi,
                psm=self.opts.psm,
                oem=self.opts.oem,
                pre="deskew,clahe" if self.opts.use_pre else None,
                save_tsv=self.opts.verbose,
                outdir=debug_dir,
                dpi_mode=self.opts.dpi_mode,
            )
        except Exception as exc:  # pragma: no cover - external OCR errors
            self._log_warning(f"ocr_runner_error:{exc}")
            return {}
        lookup: Dict[int, Dict[str, object]] = {}
        for item in results:
            page_no = int(item.get("page_no", 0) or 0)
            if page_no > 0:
                lookup[page_no] = item
        return lookup

    def _apply_ocr_result(self, fallback_text: str, ocr_data: Optional[Dict[str, object]]) -> Tuple[str, float, int, float]:
        if not ocr_data:
            text = fallback_text or ""
            return text, 0.0, len(text.split()), 0.0
        text = ocr_data.get("text") or ""
        conf = float(ocr_data.get("avg_conf") or 0.0)
        time_ms = float(ocr_data.get("time_ms") or 0.0)
        words = len(text.split()) if text else int(ocr_data.get("tokens") or 0)
        return text, conf, words, time_ms

    def _smart_merge(self, native_text: str, ocr_text: str, native_conf: float, ocr_conf: float) -> Tuple[str, float]:
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

    def _maybe_collect_tables(
        self,
        page,
        pdf_path: Path,
        page_no: int,
        decision: str,
        ocr_data: Optional[Dict[str, object]],
    ) -> None:
        mode_value = (self.opts.tables_mode or "off").lower()
        if extract_tables_from_image is None or np is None or fitz is None:
            if mode_value != "off":
                self._log_warning("tables_unavailable")
            return
        if mode_value == "off":
            return
        detect_only = mode_value in {"detect", "detect-only", "check", "flag"}
        if detect_only:
            dpi_hint = max(int(getattr(self.opts, "dpi", 220)) or 220, 220)
        else:
            dpi_hint = int(ocr_data.get("dpi") or self.opts.dpi or 300) if ocr_data else max(self.opts.dpi, 220)
        zoom = max(dpi_hint / 72.0, 2.0)
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        except Exception as exc:
            self._log_warning(f"table_render_error:p{page_no}:{exc}")
            return
        try:
            buffer = pix.samples
            channels = pix.n
            arr = np.frombuffer(buffer, dtype=np.uint8)
            if channels <= 1:
                arr = arr.reshape(pix.height, pix.width)
            else:
                arr = arr.reshape(pix.height, pix.width, channels)
                if channels == 4:
                    arr = arr[:, :, :3]
        except Exception as exc:
            self._log_warning(f"table_np_error:p{page_no}:{exc}")
            return
        export_dir = None
        if self.opts.save_table_crops and not detect_only:
            export_dir = str(self.readers_dir / "tables")
        sensitivity = "high" if mode_value == "full" else "normal"
        try:
            rows, metrics = extract_tables_from_image(
                arr,
                lang=self.opts.lang,
                sensitivity=sensitivity,
                export_dir=export_dir,
                page_tag=f"{page_no:04d}",
                allow_borderless=True,
                ocr_cells=not detect_only,
            )
        except Exception as exc:
            self._log_warning(f"table_extract_error:p{page_no}:{exc}")
            return
        if not rows:
            return
        cell_count = int(metrics.get("cell_count", 0) or 0)
        avg_cell_area = float(metrics.get("avg_cell_area", 0.0) or 0.0)
        metrics_clean = {
            "rows": int(metrics.get("rows", 0) or 0),
            "cols": int(metrics.get("cols", 0) or 0),
            "cell_count": cell_count,
            "avg_cell_height": float(metrics.get("avg_cell_height", 0.0) or 0.0),
            "avg_cell_width": float(metrics.get("avg_cell_width", 0.0) or 0.0),
            "avg_cell_area": avg_cell_area,
        }
        if detect_only:
            min_area = float(getattr(self.opts, "table_detect_min_area", 9000.0) or 0.0)
            max_cells = int(getattr(self.opts, "table_detect_max_cells", 600) or 0)
            if cell_count == 0 or cell_count > max_cells or avg_cell_area < min_area:
                self._log_warning(
                    f"table_candidate_filtered:p{page_no}:cells{cell_count}:area{avg_cell_area:.0f}"
                )
                return
            rows = [["" for _ in row] for row in rows]
        else:
            min_words = max(int(getattr(self.opts, "tables_min_words", 0)), 0)
            total_words = sum(len(str(cell).split()) for row in rows for cell in row)
            if min_words and total_words < min_words:
                return
        table_record = TableRecord(file=str(pdf_path), page=page_no, rows=rows, decision=decision, metrics=metrics_clean)
        self._tables.append(table_record)
        self._table_flags.add(page_no)
        self._table_candidates[page_no] = metrics_clean
    def _ocr_image_file(self, path: Path) -> None:
        if Image is None or pytesseract is None:
            self._log_warning("image_ocr_unavailable")
            return
        start = time.perf_counter()
        try:
            image = Image.open(path).convert("RGB")
        except Exception as exc:
            self._log_warning(f"read_image_error:{exc}")
            return
        try:
            cfg = f"-l {getattr(self.opts, 'lang', 'eng')} --oem {getattr(self.opts, 'oem', 3)} --psm {getattr(self.opts, 'psm', 6)}"
            data = pytesseract.image_to_data(image, output_type="dict", config=cfg)
            words = data.get("text", []) or []
            confs = data.get("conf", []) or []
            text = " \n".join(word for word in words if word and word.strip() and word != "-1")
            conf = _safe_avg_conf(confs)
        except Exception as exc:
            self._log_warning(f"fallback_ocr_error:{exc}")
            text, conf = "", 0.0
        elapsed = (time.perf_counter() - start) * 1000.0
        self._records.append(
            PageRecord(
                file=str(path),
                page=1,
                source="ocr_image",
                text=text,
                conf=conf,
                time_ms=elapsed,
                words=len(text.split()),
            )
        )
        self._page_decisions.append("ocr")

    def _docx_native(self, path: Path) -> None:
        start = time.perf_counter()
        try:
            text = read_docx_to_text(str(path))
        except Exception as exc:
            self._log_warning(f"docx_error:{exc}")
            return
        elapsed = (time.perf_counter() - start) * 1000.0
        words = len(text.split()) if text else 0
        conf = 90.0 if text else 0.0
        self._records.append(
            PageRecord(
                file=str(path),
                page=1,
                source="native",
                text=text,
                conf=conf,
                time_ms=elapsed,
                words=words,
            )
        )
        self._page_decisions.append("native")

    def _text_native(self, path: Path) -> None:
        start = time.perf_counter()
        try:
            text = Path(path).read_text("utf-8", errors="replace")
        except Exception as exc:
            self._log_warning(f"text_error:{exc}")
            return
        elapsed = (time.perf_counter() - start) * 1000.0
        words = len(text.split()) if text else 0
        conf = 92.0 if text else 0.0
        self._records.append(
            PageRecord(
                file=str(path),
                page=1,
                source="native",
                text=text,
                conf=conf,
                time_ms=elapsed,
                words=words,
            )
        )
        self._page_decisions.append("native")

    def _fallback_pdf_native(self, path: Path) -> None:
        try:
            text = read_pdf_text(str(path))
        except Exception as exc:
            self._log_warning(f"pdf_native_error:{exc}")
            return
        words = len(text.split()) if text else 0
        conf = 80.0 if text else 0.0
        self._records.append(
            PageRecord(
                file=str(path),
                page=1,
                source="native",
                text=text,
                conf=conf,
                time_ms=0.0,
                words=words,
            )
        )
        self._page_decisions.append("native")

    def _process_pdf(self, path: Path) -> None:
        if fitz is None:
            self._log_warning("pymupdf_missing")
            self._fallback_pdf_native(path)
            return
        try:
            doc = fitz.open(path)
        except Exception as exc:
            self._log_warning(f"pdf_open_error:{exc}")
            self._fallback_pdf_native(path)
            return
        native_map: Dict[int, Dict[str, float]] = {}
        overlay_candidates: List[int] = []
        ocr_needed: List[int] = []
        mode = (self.opts.mode or "mixed").lower()
        for index, page in enumerate(doc):
            page_no = index + 1
            native_data = self._native_page_data(page)
            coverage, image_count = self._image_stats(page)
            native_data["coverage"] = coverage
            native_data["image_count"] = image_count
            native_map[page_no] = native_data
            if mode == "ocr":
                ocr_needed.append(page_no)
                continue
            if mode == "native":
                if not native_data.get("text", "").strip():
                    ocr_needed.append(page_no)
                elif self._should_overlay(native_data.get("text", ""), native_data.get("conf", 0.0), coverage, image_count):
                    overlay_candidates.append(page_no)
                    ocr_needed.append(page_no)
                continue
            # mixed
            if self._should_use_native_mixed(native_data.get("conf", 0.0), native_data.get("block_count", 0), native_data.get("words", 0), coverage):
                if self._should_overlay(native_data.get("text", ""), native_data.get("conf", 0.0), coverage, image_count):
                    overlay_candidates.append(page_no)
                    ocr_needed.append(page_no)
            else:
                ocr_needed.append(page_no)
        ocr_lookup: Dict[int, Dict[str, object]] = {}
        if ocr_needed:
            unique_pages = sorted(set(ocr_needed))
            ocr_lookup = self._run_ocr(path, unique_pages)
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
            ocr_data = ocr_lookup.get(page_no)
            if mode == "ocr":
                final_text, final_conf, final_words, final_time = self._apply_ocr_result(native_text, ocr_data)
                decision = "ocr"
            elif mode == "native":
                if not native_text.strip():
                    final_text, final_conf, final_words, final_time = self._apply_ocr_result(native_text, ocr_data)
                    decision = "ocr"
                elif page_no in overlay_candidates and ocr_data:
                    merged_text, merged_conf = self._smart_merge(native_text, ocr_data.get("text") or "", native_conf, float(ocr_data.get("avg_conf") or 0.0))
                    final_text = merged_text
                    final_conf = merged_conf
                    final_words = len(final_text.split())
                    final_time += float(ocr_data.get("time_ms") or 0.0)
                    decision = "native+ocr"
            else:  # mixed
                if page_no in ocr_lookup and page_no not in overlay_candidates:
                    final_text, final_conf, final_words, final_time = self._apply_ocr_result(native_text, ocr_data)
                    decision = "ocr"
                elif page_no in overlay_candidates and ocr_data:
                    merged_text, merged_conf = self._smart_merge(native_text, ocr_data.get("text") or "", native_conf, float(ocr_data.get("avg_conf") or 0.0))
                    final_text = merged_text
                    final_conf = merged_conf
                    final_words = len(final_text.split())
                    final_time += float(ocr_data.get("time_ms") or 0.0)
                    decision = "native+ocr"
                elif not native_text.strip():
                    final_text, final_conf, final_words, final_time = self._apply_ocr_result(native_text, ocr_data)
                    decision = "ocr"
            if not final_text.strip():
                self._log_warning(f"empty_page_text:p{page_no}")
            self._records.append(
                PageRecord(
                    file=str(path),
                    page=page_no,
                    source=decision,
                    text=final_text,
                    conf=round(final_conf, 2),
                    time_ms=round(final_time, 2),
                    words=final_words,
                )
            )
            self._page_decisions.append(decision)
            if final_text.strip():
                self._maybe_collect_tables(page, path, page_no, decision, ocr_data)
        doc.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, inputs) -> Dict[str, object]:
        self._reset_state()
        files: List[str] = []
        mode = (self.opts.mode or "mixed").lower()
        for item in inputs:
            path = Path(item)
            files.append(str(path))
            ext = path.suffix.lower()
            if ext == ".pdf":
                self._process_pdf(path)
            elif ext in DOCX_EXTS:
                self._docx_native(path)
            elif ext in TEXT_EXTS:
                self._text_native(path)
            elif ext in IMAGE_EXTS:
                self._ocr_image_file(path)
            else:
                self._log_warning(f"unknown_ext:{ext or 'none'}")
                self._ocr_image_file(path)
        self._write_outputs(files)
        avg_conf = _safe_avg_conf([record.conf for record in self._records])
        total_ms = (time.time() - self._t0) * 1000.0
        summary = Summary(
            files=files,
            page_count=len(self._page_decisions),
            avg_conf=avg_conf,
            warnings=self._warnings,
            timings_ms={"total_ms": total_ms},
            page_decisions=self._page_decisions,
        )
        summary_dict = asdict(summary)
        summary_dict["table_pages"] = sorted(self._table_flags)
        summary_dict["table_stats"] = [
            {"page": int(page), **metrics}
            for page, metrics in sorted(self._table_candidates.items())
        ]
        return {
            "summary": summary_dict,
            "pages_count": len(self._page_decisions),
            "tables_count": len(self._tables),
            "tables_cells": sum(sum(len(row) for row in tbl.rows) for tbl in self._tables),
            "outdir": str(self.readers_dir),
        }

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------
    def _write_outputs(self, inputs) -> None:
        self.readers_dir.mkdir(parents=True, exist_ok=True)
        jsonl_path = self.readers_dir / "unified_text.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as handle:
            for record in self._records:
                handle.write(
                    json.dumps(
                        {
                            "file": record.file,
                            "page": record.page,
                            "source": record.source,
                            "text": record.text,
                            "conf": record.conf,
                            "time_ms": record.time_ms,
                            "words": record.words,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        txt_path = self.readers_dir / "unified_text.txt"
        with open(txt_path, "w", encoding="utf-8") as handle:
            for record in self._records:
                handle.write(
                    f"# file={record.file} page={record.page} source={record.source} conf={record.conf:.2f} time_ms={record.time_ms:.2f}\n"
                )
                handle.write(record.text.strip() + "\n\n")
        tables_path = self.readers_dir / "tables.jsonl"
        if self._tables:
            with open(tables_path, "w", encoding="utf-8") as handle:
                for table in self._tables:
                    payload = {"file": table.file, "page": table.page, "decision": table.decision, "rows": table.rows}
                    if table.metrics:
                        payload["metrics"] = table.metrics
                    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            (self.readers_dir / "tables.json").write_text(
                json.dumps({"tables": [asdict(table) for table in self._tables]}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        avg_conf = _safe_avg_conf([record.conf for record in self._records])
        total_ms = (time.time() - self._t0) * 1000.0
        table_stats = [
            {"page": int(page), **metrics}
            for page, metrics in sorted(self._table_candidates.items())
        ]
        summary = {
            "files": list({record.file for record in self._records}) or [str(p) for p in inputs],
            "page_count": len(self._page_decisions),
            "avg_conf": avg_conf,
            "warnings": self._warnings,
            "timings_ms": {"total_ms": total_ms},
            "page_decisions": self._page_decisions,
            "tables_count": len(self._tables),
            "table_pages": sorted(self._table_flags),
            "table_stats": table_stats,
        }
        summary_path = self.readers_dir / "readers_summary.json"
        summary_path.write_text(json.dumps({"summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            _enrich_summary_on_disk(self.readers_dir, self.opts)
        except Exception as exc:
            self._log_warning(f"enrich_error:{exc}")


def _enrich_summary_on_disk(outdir: Path, opts: ReaderOptions):
    """Enrich readers_summary.json with per-page statistics and review flags."""
    import csv
    import json
    from collections import defaultdict

    summary_path = Path(outdir) / "readers_summary.json"
    if not summary_path.exists():
        return

    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return

    summary = payload.get("summary", {}) or {}
    pages = int(summary.get("page_count", 0) or 0)
    decisions = summary.get("page_decisions", []) or []
    warnings = summary.get("warnings", []) or []

    thresholds = dict(payload.get("thresholds", {}) or {})
    thresholds.setdefault("any_min_conf", 70.0)
    thresholds.setdefault("ocr_min_conf", 80.0)
    thresholds.setdefault("low_conf", 70.0)
    thresholds.setdefault("boost_conf", 80.0)
    thresholds.setdefault("overlay_area_thr", float(getattr(opts, "overlay_area_thr", 0.35)))
    thresholds.setdefault("overlay_min_images", int(getattr(opts, "overlay_min_images", 1)))
    payload["thresholds"] = thresholds

    tables_cells = defaultdict(int)
    tables_path = Path(outdir) / "tables.jsonl"
    if tables_path.exists():
        try:
            for line in tables_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                page_no = int(obj.get("page", 0) or 0)
                rows = obj.get("rows", []) or []
                cells = sum(len(r) for r in rows)
                tables_cells[page_no] += cells
        except Exception:
            tables_cells = defaultdict(int)

    record_map = {}
    jsonl_path = Path(outdir) / "unified_text.jsonl"
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            page_no = int(obj.get("page", 0) or 0)
            record_map[page_no] = obj

    per_page = []
    for page in range(1, pages + 1):
        record = record_map.get(page, {})
        decision = (decisions[page - 1] if page - 1 < len(decisions) else record.get("source", "native")) or "native"
        source = str(record.get("source") or decision)
        conf = float(record.get("conf") or 0.0)
        time_ms = float(record.get("time_ms") or 0.0)
        words = int(record.get("words") or 0)
        cells = int(tables_cells.get(page, 0))
        per_page.append(
            {
                "page": page,
                "source": source,
                "conf": conf,
                "ocr_words": words,
                "has_table": cells > 0,
                "table_cells": cells,
                "decision": decision,
                "time_ms": time_ms,
            }
        )

    payload["per_page_stats"] = per_page

    flagged = []
    any_thr = float(thresholds.get("any_min_conf", 70.0))
    ocr_thr = float(thresholds.get("ocr_min_conf", 80.0))
    for record in per_page:
        source = str(record.get("source", "")).lower()
        conf = float(record.get("conf") or 0.0)
        if conf < any_thr or ("ocr" in source and conf < ocr_thr):
            flagged.append(record["page"])

    payload["flags"] = {"manual_review": bool(warnings) or bool(flagged), "pages": flagged}
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = Path(outdir) / "per_page_stats.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["page", "source", "conf", "ocr_words", "has_table", "table_cells", "decision", "time_ms"],
            )
            writer.writeheader()
            writer.writerows(per_page)
    except Exception:
        pass
# === end auto-added enrichment ===






