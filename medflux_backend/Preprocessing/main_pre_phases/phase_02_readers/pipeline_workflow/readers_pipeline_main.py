from __future__ import annotations
"""Runtime orchestrator for the readers pipeline stage."""
from pathlib import Path
from collections import defaultdict
import json
import time
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple, Set

from ..schemas.readers_schema_models import Summary, PageRecord, TableRecord
from ..schemas.readers_schema_options import ReaderOptions
from ..schemas.readers_schema_settings import get_runtime_settings
from medflux_backend.Preprocessing.main_pre_helpers.main_pre_helpers_lang_detect import (
    compute_language_hint,
    compute_locale_hint,
    compute_merged_language_hint,
)
from ..internal_helpers.readers_helper_logging import (
    record_readers_tool_event,
    record_readers_warning,
)

log_tool_event = record_readers_tool_event
log_warning = record_readers_warning

from ..core_functions.readers_core_native import (
    process_readers_docx_native,
    process_readers_pdf_fallback,
    process_readers_ocr_image,
    process_readers_pdf_document,
    process_readers_text_native,
)
from ..core_functions.readers_core_ocr import process_readers_ocr_result, run_pdf_ocr, process_readers_merge_text
from ..core_functions.readers_core_tables import (
    process_readers_append_table_raw,
    compute_readers_cell_bbox_from_geometry,
    compute_readers_table_bbox_from_geometry,
    process_readers_collect_tables,
    record_readers_table_candidate_entry,
)
from ..core_functions.readers_core_artifacts import process_readers_collect_image_artifacts, compute_readers_visual_artifact


SETTINGS = get_runtime_settings()
OCR_LOW_CONF = float(SETTINGS.thresholds.get("ocr_low_conf", 75.0))
OCR_LOW_TEXT_MIN_WORDS = int(SETTINGS.thresholds.get("ocr_low_text_min_words", 12))
SUSPICIOUS_TEXT_CHARS_MIN = int(SETTINGS.thresholds.get("suspicious_text_chars_min", 40))
TABLES_FEATURE_MODE = str(SETTINGS.features.get("tables_mode", "detect")).lower()


from ..core_functions.readers_core_tables_detector import LightTableDetector

DOCX_EXTS = {".docx"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
TEXT_EXTS = {".txt", ".log", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".ini", ".cfg", ".conf"}

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


class ReadersOrchestrator:
    def __init__(self, outdir: Path, opts: ReaderOptions):
        self.base_outdir = Path(outdir)
        self.outdir = self.base_outdir
        self.readers_dir = self.base_outdir / "readers"
        self.opts = opts
        self._records: List[PageRecord] = []
        self._warnings: List[str] = []
        self._page_decisions: List[str] = []
        self._tables: List[TableRecord] = []
        self._tables_raw: List[Dict[str, Any]] = []
        self._blocks: List[Dict[str, Any]] = []
        self._zones: List[Dict[str, Any]] = []
        self._page_geometry: Dict[int, Dict[str, float]] = {}
        self._table_flags: Set[int] = set()
        self._table_candidates: Dict[int, Dict[str, float]] = {}
        self._page_language_hints: Dict[int, str] = {}
        self._page_locale_hints: Dict[int, str] = {}
        self._tool_events: List[Dict[str, Any]] = []
        self._visual_artifacts: List[Dict[str, Any]] = []
        self._block_counter: int = 0
        self._timings: defaultdict[str, float] = defaultdict(float)
        self._structured_log_path = self.readers_dir / "structured_logs.jsonl"
        self._table_counts: defaultdict[int, int] = defaultdict(int)
        self._t0 = time.time()
        self._light_tables = LightTableDetector(self.readers_dir)

        base_tables_mode = TABLES_FEATURE_MODE
        effective_tables_mode = str(self.opts.tables_mode or base_tables_mode).lower()
        if effective_tables_mode == "light":
            effective_tables_mode = "detect"
        elif effective_tables_mode == "full":
            effective_tables_mode = "extract"
        self._tables_mode = effective_tables_mode
        self._allow_tables_raw = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def reset_readers_state(self) -> None:
        self._records.clear()
        self._warnings.clear()
        self._page_decisions.clear()
        self._tables.clear()
        self._tables_raw.clear()
        self._blocks.clear()
        self._zones.clear()
        self._page_geometry.clear()
        self._table_flags.clear()
        self._table_candidates.clear()
        self._page_language_hints.clear()
        self._page_locale_hints.clear()
        self._tool_events.clear()
        self._visual_artifacts.clear()
        self._timings.clear()
        self._table_counts.clear()
        self._block_counter = 0
        self._t0 = time.time()
        self._light_tables.reset()
        if self._structured_log_path.exists():
            try:
                self._structured_log_path.unlink()
            except Exception:
                pass

    def record_readers_warning_event(self, code: str) -> None:
        log_warning(self._structured_log_path, self._warnings, code)

    def record_readers_tool_event_entry(
        self,
        step: str,
        status: str,
        page: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        log_tool_event(
            self._structured_log_path,
            self._tool_events,
            step=step,
            status=status,
            page=page,
            details=details,
        )

    def _log_warning(self, code: str) -> None:
        self.record_readers_warning_event(code)

    def _log_tool_event(
        self,
        step: str,
        status: str,
        *,
        page: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.record_readers_tool_event_entry(step, status, page=page, details=details)

    def _blocks_for_page(self, page_no: int) -> List[Dict[str, Any]]:
        return self.get_readers_blocks_for_page(page_no)

    def get_readers_blocks_for_page(self, page_no: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for block in self._blocks:
            try:
                page_value = int(block.get("page") or 0)
            except Exception:
                continue
            if page_value == page_no:
                results.append(block)
        return results

    def process_readers_zones(self, page, page_no: int) -> None:
        try:
            rect = getattr(page, "rect")
            x0 = float(rect.x0)
            y0 = float(rect.y0)
            x1 = float(rect.x1)
            y1 = float(rect.y1)
        except Exception:
            return
        page_height = max(y1 - y0, 0.0)
        if page_height <= 0:
            return
        header_band = y0 + page_height * 0.12
        footer_band = y1 - page_height * 0.12
        header_boxes: List[Tuple[float, float, float, float]] = []
        footer_boxes: List[Tuple[float, float, float, float]] = []
        for block in self.get_readers_blocks_for_page(page_no):
            bbox = block.get("bbox")
            if not isinstance(bbox, list) or len(bbox) < 4:
                continue
            try:
                bx0, by0, bx1, by1 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            except Exception:
                continue
            if by1 <= header_band:
                header_boxes.append((bx0, by0, bx1, by1))
            if by0 >= footer_band:
                footer_boxes.append((bx0, by0, bx1, by1))
        self._zones = [zone for zone in self._zones if int(zone.get("page", 0)) != page_no]
        def _merge(boxes: List[Tuple[float, float, float, float]]) -> List[float]:
            return [
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            ]
        if header_boxes:
            self._zones.append({"page": page_no, "bbox": _merge(header_boxes), "type": "header"})
        if footer_boxes:
            self._zones.append({"page": page_no, "bbox": _merge(footer_boxes), "type": "footer"})
        header_bottom = max((box[3] for box in header_boxes), default=y0)
        footer_top = min((box[1] for box in footer_boxes), default=y1)
        body_top = header_bottom if header_boxes else y0
        body_bottom = footer_top if footer_boxes else y1
        if body_bottom <= body_top:
            body_top, body_bottom = y0, y1
        self._zones.append({"page": page_no, "bbox": [x0, body_top, x1, body_bottom], "type": "body"})

    def _native_page_data(self, page, page_no: int) -> Dict[str, Any]:
        return self.get_readers_native_page_data(page, page_no)

    def _record_page_blocks(
        self,
        page_no: int,
        decision: str,
        native_blocks: List[Dict[str, Any]],
        final_text: str,
        ocr_avg_conf: Optional[float],
    ) -> None:
        self.record_readers_page_blocks(page_no, decision, native_blocks, final_text, ocr_avg_conf)

    def _update_page_hints(self, page_no: int, text: str) -> None:
        self.process_readers_page_hints(page_no, text)

    def _update_zones(self, page, page_no: int) -> None:
        self.process_readers_zones(page, page_no)

    def _should_overlay(self, text: str, conf: float, coverage: float, image_count: int) -> bool:
        return self.check_readers_should_overlay(text, conf, coverage, image_count)

    def _should_use_native_mixed(self, conf: float, block_count: int, words: int, coverage: float) -> bool:
        return self.check_readers_use_native_mixed(conf, block_count, words, coverage)

    def record_readers_table_candidate(
        self,
        page,
        page_no: int,
        decision: str,
        status: str,
        extraction_tool: str,
        bbox: Optional[List[float]],
        metrics: Optional[Dict[str, Any]],
        geometry: Optional[Dict[str, Any]],
    ) -> None:
        record_readers_table_candidate_entry(self, page, page_no, decision, status, extraction_tool, bbox, metrics, geometry)


    def compute_readers_style_features(self, text: str, font_sizes: List[float], spans_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = text or ""
        char_count = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        uppercase_chars = sum(1 for c in text if c.isalpha() and c.isupper())
        is_upper = bool(alpha_chars) and (uppercase_chars / alpha_chars) >= 0.75
        font_avg: Optional[float] = None
        if font_sizes:
            try:
                font_avg = round(sum(font_sizes) / max(len(font_sizes), 1), 2)
            except Exception:
                font_avg = None
        fonts = [str(meta.get("font") or "") for meta in spans_meta]
        flags = [int(meta.get("flags") or 0) for meta in spans_meta]
        is_bold = any("bold" in font.lower() for font in fonts if font) or any(flag & 2 for flag in flags)
        return {
            "font_size_avg": font_avg,
            "is_bold": is_bold,
            "is_upper": is_upper,
            "char_count": char_count,
        }

    def compute_readers_visual_artifact(self, bbox: List[float], page_rect) -> Optional[Tuple[str, float]]:
        return compute_readers_visual_artifact(bbox, page_rect)


    def process_readers_image_artifacts(self, page, page_no: int) -> None:
        process_readers_collect_image_artifacts(self, page, page_no)


    def _infer_language_hint(self, text: str) -> str:
        return compute_language_hint(text or '')

    def _infer_locale_hint(self, text: str) -> str:
        return compute_locale_hint(text or '')

    def _merge_hint(self, current: Optional[str], new: Optional[str]) -> str:
        return compute_merged_language_hint(current, new)

    def process_readers_page_hints(self, page_no: int, text: str) -> None:
        start = time.perf_counter()
        lang_hint = compute_language_hint(text)
        locale_hint = compute_locale_hint(text)
        self._page_language_hints[page_no] = compute_merged_language_hint(self._page_language_hints.get(page_no), lang_hint)
        self._page_locale_hints[page_no] = compute_merged_language_hint(self._page_locale_hints.get(page_no), locale_hint)
        self._timings["lang_detect"] += (time.perf_counter() - start) * 1000.0


    def get_readers_native_page_data(self, page, page_no: int) -> Dict[str, Any]:
        start = time.perf_counter()
        text = ""
        blocks: List[Dict[str, Any]] = []
        try:
            text = page.get_text("text") or ""
        except Exception:
            text = ""
        try:
            blocks_dict = page.get_text("dict") or {}
        except Exception:
            blocks_dict = {}
        if isinstance(blocks_dict, dict):
            try:
                blocks = self.compute_readers_block_entries(blocks_dict, page_no)
            except Exception:
                blocks = []
        block_count = len(blocks)
        if not text and blocks:
            text = "\n".join(entry.get("text_raw", "") for entry in blocks).strip()
        words = len(text.split()) if text else 0
        conf = self.compute_readers_native_confidence(text, block_count, words)
        elapsed = (time.perf_counter() - start) * 1000.0
        self._timings["text_extract"] += elapsed
        return {
            "text": text,
            "conf": conf,
            "words": words,
            "block_count": block_count,
            "time_ms": elapsed,
            "blocks": blocks,
        }

    def compute_readers_block_entries(self, blocks_dict: Dict[str, Any], page_no: int) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        blocks = blocks_dict.get("blocks") or []
        for idx, block in enumerate(blocks):
            if block.get("type") not in (None, 0):
                continue
            lines = block.get("lines") or []
            text_lines: List[str] = []
            font_sizes: List[float] = []
            spans_meta: List[Dict[str, Any]] = []
            for line in lines:
                spans = line.get("spans") or []
                parts: List[str] = []
                for span in spans:
                    piece = span.get("text") or ""
                    if piece:
                        parts.append(piece)
                    spans_meta.append(
                        {
                            "font": span.get("font"),
                            "flags": span.get("flags"),
                            "size": span.get("size"),
                        }
                    )
                    size = span.get("size")
                    if size is not None:
                        try:
                            font_sizes.append(float(size))
                        except Exception:
                            continue
                line_text = "".join(parts).strip("\n")
                if line_text:
                    text_lines.append(line_text)
            text_raw = "\n".join(text_lines).strip()
            if not text_raw:
                continue
            entry = {
                "id": f"{page_no}-{idx}",
                "page": page_no,
                "text_raw": text_raw,
                "text_lines": text_lines,
                "bbox": list(block.get("bbox") or []),
                "reading_order_index": None,
                "is_heading_like": self.check_readers_heading_like(text_raw, font_sizes, text_lines),
                "is_list_like": self.check_readers_list_like(text_raw),
                "ocr_conf_avg": None,
            }
            entry.update(self.compute_readers_style_features(text_raw, font_sizes, spans_meta))
            entries.append(entry)
        return entries

    def check_readers_heading_like(self, text_raw: str, font_sizes: List[float], text_lines: List[str]) -> bool:
        trimmed = text_raw.strip()
        if not trimmed:
            return False
        words = trimmed.split()
        if len(words) > 12:
            return False
        alpha_count = sum(1 for c in trimmed if c.isalpha())
        upper_count = sum(1 for c in trimmed if c.isupper())
        uppercase_ratio = (upper_count / alpha_count) if alpha_count else 0.0
        max_size = max(font_sizes) if font_sizes else 0.0
        mean_size = (sum(font_sizes) / len(font_sizes)) if font_sizes else 0.0
        if uppercase_ratio >= 0.6 and len(words) <= 8:
            return True
        if max_size and max_size >= max(14.0, mean_size * 1.2):
            return True
        if len(text_lines) == 1 and len(words) <= 6 and uppercase_ratio >= 0.4:
            return True
        return False

    def check_readers_list_like(self, text_raw: str) -> bool:
        stripped = (text_raw or "").lstrip()
        if not stripped:
            return False
        bullet_prefixes = ("- ", "* ", "+ ", "\u2022", "\u2022 ")
        if stripped.startswith(bullet_prefixes):
            return True
        if re.match(r"^([0-9]+[\\).]|[a-zA-Z][\\).])\\s+", stripped):
            return True
        return False

    def record_readers_page_blocks(
        self,
        page_no: int,
        decision: str,
        native_blocks: List[Dict[str, Any]],
        final_text: str,
        ocr_avg_conf: Optional[float],
    ) -> None:
        decision_lower = (decision or "").lower()
        blocks_to_use = native_blocks or []
        if blocks_to_use:
            for block in blocks_to_use:
                lang_hint = block.get("lang_hint") or self._infer_language_hint(block.get("text_raw", ""))
                locale_hint = block.get("locale_hint") or self._infer_locale_hint(block.get("text_raw", ""))
                entry = {
                    "id": block.get("id") or f"{page_no}-{self._block_counter}",
                    "page": page_no,
                    "text_raw": block.get("text_raw", ""),
                    "text_lines": list(block.get("text_lines") or []),
                    "bbox": list(block.get("bbox") or []),
                    "reading_order_index": self._block_counter,
                    "is_heading_like": bool(block.get("is_heading_like")),
                    "is_list_like": bool(block.get("is_list_like")),
                    "ocr_conf_avg": block.get("ocr_conf_avg"),
                    "lang_hint": lang_hint,
                    "locale_hint": locale_hint,
                    "font_size_avg": block.get("font_size_avg"),
                    "is_bold": bool(block.get("is_bold")),
                    "is_upper": bool(block.get("is_upper")),
                    "char_count": int(block.get("char_count") or len(block.get("text_raw", ""))),
                }
                if "ocr" in decision_lower and ocr_avg_conf is not None:
                    entry["ocr_conf_avg"] = ocr_avg_conf
                self._blocks.append(entry)
                self._block_counter += 1
                self._page_language_hints[page_no] = self._merge_hint(self._page_language_hints.get(page_no), lang_hint)
                self._page_locale_hints[page_no] = self._merge_hint(self._page_locale_hints.get(page_no), locale_hint)
        else:
            self.process_readers_simple_block(page_no, final_text, decision, ocr_avg_conf)

        self.process_readers_page_hints(page_no, final_text)

    def process_readers_simple_block(
        self,
        page_no: int,
        text: str,
        decision: str,
        ocr_avg_conf: Optional[float],
        bbox: Optional[List[float]] = None,
    ) -> None:
        stripped = (text or "").strip()
        if not stripped:
            return
        lines = [line.strip() for line in stripped.splitlines() if line.strip()] or [stripped]
        normalized_text = "\n".join(lines)
        decision_lower = (decision or "").lower()
        lang_hint = compute_language_hint(normalized_text)
        locale_hint = compute_locale_hint(normalized_text)
        entry = {
            "id": f"{page_no}-block-{self._block_counter}",
            "page": page_no,
            "text_raw": normalized_text,
            "text_lines": lines,
            "bbox": list(bbox) if bbox else None,
            "reading_order_index": self._block_counter,
            "is_heading_like": self.check_readers_heading_like(normalized_text, [], lines),
            "is_list_like": self.check_readers_list_like(lines[0] if lines else normalized_text),
            "ocr_conf_avg": ocr_avg_conf if (ocr_avg_conf is not None and "ocr" in decision_lower) else None,
            "lang_hint": lang_hint,
            "locale_hint": locale_hint,
        }
        entry.update(self.compute_readers_style_features(normalized_text, [], []))
        self._blocks.append(entry)
        self._block_counter += 1
        self._page_language_hints[page_no] = compute_merged_language_hint(self._page_language_hints.get(page_no), lang_hint)
        self._page_locale_hints[page_no] = compute_merged_language_hint(self._page_locale_hints.get(page_no), locale_hint)

    def _add_simple_block(
        self,
        page_no: int,
        text: str,
        decision: str,
        ocr_avg_conf: Optional[float],
        bbox: Optional[List[float]] = None,
    ) -> None:
        self.process_readers_simple_block(page_no, text, decision, ocr_avg_conf, bbox=bbox)

    def compute_readers_table_bbox(self, geometry: Dict[str, Any], page, zoom: float) -> Optional[List[float]]:
        return compute_readers_table_bbox_from_geometry(geometry, page, zoom)


    def compute_readers_cell_bbox(
        self,
        geometry: Dict[str, Any],
        page,
        zoom: float,
        row_idx: int,
        col_idx: int,
    ) -> Optional[List[float]]:
        return compute_readers_cell_bbox_from_geometry(geometry, page, zoom, row_idx, col_idx)


    def process_readers_process_readers_append_table_raw(
        self,
        page_no: int,
        extraction_tool: str,
        status: str,
        bbox: Optional[List[float]] = None,
        cells: Optional[List[Dict[str, Any]]] = None,
        table_text: Optional[str] = None,
    ) -> None:
        process_readers_append_table_raw(self, page_no, extraction_tool, status, bbox=bbox, cells=cells, table_text=table_text)


    @staticmethod
    def compute_readers_native_confidence(text: str, block_count: int, words: int) -> float:
        if not text.strip():
            return 0.0
        block_factor = min(block_count, 8) / 8.0
        word_factor = min(words / 120.0, 1.0)
        char_factor = min(len(text) / 1500.0, 1.0)
        conf = 55.0 + block_factor * 20.0 + word_factor * 15.0 + char_factor * 10.0
        return round(min(conf, 96.0), 2)

    def compute_readers_image_stats(self, page) -> Tuple[float, int]:
        return image_stats(page)


    def check_readers_should_overlay(self, text: str, conf: float, coverage: float, image_count: int) -> bool:
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

    def check_readers_use_native_mixed(self, conf: float, block_count: int, words: int, coverage: float) -> bool:
        if conf == 0.0 or words == 0:
            return False
        if block_count >= max(1, self.opts.blocks_threshold) and conf >= OCR_LOW_CONF:
            if coverage < 0.6:
                return True
        if conf >= 85.0 and words > 40:
            return True
        return False

    def run_readers_ocr(self, pdf_path: Path, pages: List[int]) -> Dict[int, Dict[str, object]]:
        return run_pdf_ocr(self, pdf_path, pages)


    def process_readers_ocr_result_entry(self, fallback_text: str, ocr_data: Optional[Dict[str, object]]) -> Tuple[str, float, int, float]:
        return process_readers_ocr_result(fallback_text, ocr_data)


    def process_readers_smart_merge(self, native_text: str, ocr_text: str, native_conf: float, ocr_conf: float) -> Tuple[str, float]:
        return process_readers_merge_text(native_text, ocr_text, native_conf, ocr_conf)


    def process_readers_collect_tables(
        self,
        page,
        pdf_path: Path,
        page_no: int,
        decision: str,
        ocr_data: Optional[Dict[str, object]],
    ) -> None:
        process_readers_collect_tables(self, page, pdf_path, page_no, decision, ocr_data)


    def process_readers_ocr_image_page(self, path: Path) -> None:
        process_readers_ocr_image(self, path)


    def process_readers_docx_native_page(self, path: Path) -> None:
        process_readers_docx_native(self, path)


    def process_readers_text_native_page(self, path: Path) -> None:
        process_readers_text_native(self, path)


    def process_readers_pdf_fallback_page(self, path: Path) -> None:
        process_readers_pdf_fallback(self, path)


    def process_readers_pdf_document_page(self, path: Path) -> None:
        process_readers_pdf_document(self, path)


    def process(self, inputs) -> Dict[str, object]:
        self.reset_readers_state()
        files: List[str] = []
        mode = (self.opts.mode or "mixed").lower()
        for item in inputs:
            path = Path(item)
            files.append(str(path))
            ext = path.suffix.lower()
            if ext == ".pdf":
                self.process_readers_pdf_document_page(path)
            elif ext in DOCX_EXTS:
                self.process_readers_docx_native_page(path)
            elif ext in TEXT_EXTS:
                self.process_readers_text_native_page(path)
            elif ext in IMAGE_EXTS:
                self.process_readers_ocr_image_page(path)
            else:
                self.record_readers_warning_event(f"unknown_ext:{ext or 'none'}")
                self.process_readers_ocr_image_page(path)
        self.save_readers_outputs(files)
        avg_conf = compute_readers_safe_avg_conf([record.conf for record in self._records])
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
        summary_dict["text_blocks_count"] = len(self._blocks)
        summary_dict["table_pages"] = sorted(self._table_flags)
        summary_dict["table_stats"] = [
            {"page": int(page), **metrics}
            for page, metrics in sorted(self._table_candidates.items())
        ]
        summary_dict["visual_artifacts_count"] = len(self._visual_artifacts)
        summary_dict["lang_per_page"] = [
            {"page": page, "lang": self._page_language_hints.get(page, "unknown")}
            for page in sorted(self._page_language_hints)
        ]
        summary_dict["locale_per_page"] = [
            {"page": page, "locale": self._page_locale_hints.get(page, "unknown")}
            for page in sorted(self._page_locale_hints)
        ]
        if self._timings:
            timings_payload = dict(summary_dict.get("timings_ms") or {})
            for key, value in self._timings.items():
                timings_payload[key] = round(float(value), 2)
            summary_dict["timings_ms"] = timings_payload
        if self._table_counts:
            summary_dict["table_counts"] = {int(page): count for page, count in sorted(self._table_counts.items())}
        tool_log = [dict(event) for event in self._tool_events]
        summary_dict["tool_log"] = tool_log
        return {
            "summary": summary_dict,
            "pages_count": len(self._page_decisions),
            "tool_log": tool_log,
            "visual_artifacts_count": len(self._visual_artifacts),
            "tables_count": len(self._tables),
            "tables_cells": sum(sum(len(row) for row in tbl.rows) for tbl in self._tables),
            "outdir": str(self.readers_dir),
        }

    # ------------------------------------------------------------------
    # Output writers
    # ------------------------------------------------------------------
    def save_readers_outputs(self, inputs) -> None:
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
                            "chars": record.chars,
                            **({"ocr_conf_avg": record.ocr_conf_avg} if record.ocr_conf_avg is not None else {}),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        txt_path = self.readers_dir / "unified_text.txt"
        with open(txt_path, "w", encoding="utf-8") as handle:
            for record in self._records:
                header = (
                    f"# file={record.file} page={record.page} source={record.source} "
                    f"conf={record.conf:.2f} time_ms={record.time_ms:.2f} words={record.words} chars={record.chars}"
                )
                if record.ocr_conf_avg is not None:
                    header += f" ocr_conf_avg={record.ocr_conf_avg:.2f}"
                handle.write(header + "\n")
                handle.write((record.text or "").strip() + "\n\n")
        blocks_path = self.readers_dir / "text_blocks.jsonl"
        if self._blocks:
            with open(blocks_path, "w", encoding="utf-8") as handle:
                for block in self._blocks:
                    handle.write(json.dumps(block, ensure_ascii=False) + "\n")
        zones_path = self.readers_dir / "zones.jsonl"
        if self._zones:
            with open(zones_path, "w", encoding="utf-8") as handle:
                for zone in self._zones:
                    handle.write(json.dumps(zone, ensure_ascii=False) + "\n")
        elif zones_path.exists():
            try:
                zones_path.unlink()
            except Exception:
                pass
        tables_raw_path = self.readers_dir / "tables_raw.jsonl"
        if tables_raw_path.exists():
            try:
                tables_raw_path.unlink()
            except Exception:
                pass
        self._light_tables.flush()
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
        artifacts_path = self.readers_dir / "visual_artifacts.jsonl"
        with open(artifacts_path, "w", encoding="utf-8") as handle:
            for artifact in self._visual_artifacts:
                handle.write(json.dumps(artifact, ensure_ascii=False) + "\n")
        avg_conf = compute_readers_safe_avg_conf([record.conf for record in self._records])
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
            "text_blocks_count": len(self._blocks),
            "visual_artifacts_count": len(self._visual_artifacts),
            "lang_per_page": [
                {"page": page, "lang": self._page_language_hints.get(page, "unknown")}
                for page in sorted(self._page_language_hints)
            ],
            "locale_per_page": [
                {"page": page, "locale": self._page_locale_hints.get(page, "unknown")}
                for page in sorted(self._page_locale_hints)
            ],
            "tool_log": [dict(event) for event in self._tool_events],
        }
        if self._timings:
            timings_payload = dict(summary.get("timings_ms") or {})
            for key, value in self._timings.items():
                timings_payload[key] = round(float(value), 2)
            summary["timings_ms"] = timings_payload
        if self._table_counts:
            summary["table_counts"] = {int(page): count for page, count in sorted(self._table_counts.items())}
        if self._page_geometry:
            summary["page_geometry"] = {int(page): {key: (float(value) if isinstance(value, (int, float)) else value) for key, value in data.items()} for page, data in sorted(self._page_geometry.items())}
        summary_path = self.readers_dir / "readers_summary.json"
        payload = {"summary": summary, "tool_log": summary["tool_log"]}
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._tool_events:
            log_path = self.readers_dir / "tool_log.jsonl"
            with open(log_path, "w", encoding="utf-8") as handle:
                for event in self._tool_events:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        try:
            process_readers_enrich_summary_on_disk(self.readers_dir, self.opts)
        except Exception as exc:
            self.record_readers_warning_event(f"enrich_error:{exc}")


def process_readers_enrich_summary_on_disk(outdir: Path, opts: ReaderOptions):
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
    thresholds.setdefault("any_min_conf", OCR_LOW_CONF)
    thresholds.setdefault("ocr_min_conf", 80.0)
    thresholds.setdefault("low_conf", OCR_LOW_CONF)
    thresholds.setdefault("boost_conf", 80.0)
    thresholds.setdefault("review_low_conf_ratio", SETTINGS.thresholds.get("low_conf_pages_ratio_review", 0.25))
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

    lang_lookup = {int(entry.get("page", 0) or 0): entry.get("lang") or "unknown" for entry in summary.get("lang_per_page", []) or []}
    locale_lookup = {int(entry.get("page", 0) or 0): entry.get("locale") or "unknown" for entry in summary.get("locale_per_page", []) or []}
    table_counts = {int(page): int(count) for page, count in (summary.get("table_counts") or {}).items()}
    tool_events = summary.get("tool_log", []) or []
    table_fail_pages = {int(event.get("page") or 0) for event in tool_events if event.get("step") == "table_extract" and str(event.get("status")).lower() in {"failed", "fallback"}}
    per_page = []
    flagged = []
    any_thr = float(thresholds.get("any_min_conf", OCR_LOW_CONF))
    ocr_thr = float(thresholds.get("ocr_min_conf", 80.0))
    low_text_thr = OCR_LOW_TEXT_MIN_WORDS
    for page in range(1, pages + 1):
        record = record_map.get(page, {})
        decision = (decisions[page - 1] if page - 1 < len(decisions) else record.get("source", "native")) or "native"
        source = str(record.get("source") or decision)
        conf = float(record.get("conf") or 0.0)
        time_ms = float(record.get("time_ms") or 0.0)
        words = int(record.get("words") or 0)
        cells = int(tables_cells.get(page, 0))
        chars = int(record.get("chars") or len(str(record.get("text", ""))))
        ocr_conf_avg = record.get("ocr_conf_avg")
        lang = lang_lookup.get(page, "unknown")
        locale = locale_lookup.get(page, "unknown")
        tables_found = table_counts.get(page, 0)
        flags = []
        if conf < any_thr or ("ocr" in source.lower() and conf < ocr_thr):
            flags.append("low_conf_page")
        if words < low_text_thr and "ocr" in source.lower():
            flags.append("low_text_page")
        if chars < SUSPICIOUS_TEXT_CHARS_MIN and "ocr" in source.lower() and "low_text_page" not in flags:
            flags.append("low_text_page")
        if page in table_fail_pages:
            flags.append("table_extract_error")
        has_table = cells > 0 or tables_found > 0
        per_page.append(
            {
                "page": page,
                "source": source,
                "conf": conf,
                "ocr_words": words,
                "chars": chars,
                "ocr_conf_avg": ocr_conf_avg,
                "has_table": has_table,
                "tables_found": tables_found,
                "table_cells": cells,
                "decision": decision,
                "lang": lang,
                "locale": locale,
                "flags": flags,
                "time_ms": time_ms,
            }
        )
        if "low_conf_page" in flags:
            flagged.append(page)
    payload["per_page_stats"] = per_page
    low_conf_ratio_thr = float(thresholds.get("review_low_conf_ratio", SETTINGS.thresholds.get("low_conf_pages_ratio_review", 0.25)))
    manual_review = bool(warnings)
    if pages > 0 and len(flagged) / float(pages) >= low_conf_ratio_thr:
        manual_review = True
    elif bool(flagged) and low_conf_ratio_thr <= 0:
        manual_review = True
    payload.pop("flags", None)
    payload.pop("qa", None)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = Path(outdir) / "per_page_stats.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["page", "source", "conf", "ocr_words", "chars", "has_table", "tables_found", "table_cells", "flags", "decision", "lang", "locale", "time_ms"],
            )
            writer.writeheader()
            writer.writerows(per_page)
    except Exception:
        pass
# === end auto-added enrichment ===










