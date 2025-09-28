from __future__ import annotations
"""Lightweight readers shim with native, OCR, and document handlers."""
from pathlib import Path
from collections import defaultdict
import json
import time
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Set

DE_TRIGGER_CHARS = {'ä', 'ö', 'ü', 'ß'}
DE_KEYWORDS = {
    'und', 'der', 'die', 'das', 'ein', 'eine', 'ist', 'nicht', 'mit', 'für', 'aus', 'dem', 'den', 'des', 'bei', 'oder', 'wir', 'sie', 'dass', 'zum', 'zur', 'über',
}
EN_KEYWORDS = {
    'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'you', 'please', 'dear', 'hello', 'thank', 'invoice', 'date', 'page', 'tax',
}
DATE_KEYWORDS_DE = {
    'januar', 'februar', 'märz', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'dezember',
}
DATE_KEYWORDS_EN = {
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
}

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
    chars: int = 0
    ocr_conf_avg: Optional[float] = None


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
        self._tables_raw: List[Dict[str, Any]] = []
        self._blocks: List[Dict[str, Any]] = []
        self._table_flags: Set[int] = set()
        self._table_candidates: Dict[int, Dict[str, float]] = {}
        self._page_language_hints: Dict[int, str] = {}
        self._page_locale_hints: Dict[int, str] = {}
        self._tool_events: List[Dict[str, Any]] = []
        self._visual_artifacts: List[Dict[str, Any]] = []
        self._block_counter: int = 0
        self._timings: defaultdict[str, float] = defaultdict(float)
        self._table_counts: defaultdict[int, int] = defaultdict(int)
        self._t0 = time.time()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _reset_state(self) -> None:
        self._records.clear()
        self._warnings.clear()
        self._page_decisions.clear()
        self._tables.clear()
        self._tables_raw.clear()
        self._blocks.clear()
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

    def _log_warning(self, code: str) -> None:
        if code not in self._warnings:
            self._warnings.append(code)

    def _log_tool_event(
        self,
        step: str,
        status: str,
        page: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry: Dict[str, Any] = {"step": step, "status": status}
        if page is not None:
            entry["page"] = int(page)
        if details:
            entry["details"] = details
        self._tool_events.append(entry)

    def _extract_style_features(self, text: str, font_sizes: List[float], spans_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    def _classify_visual_artifact(self, bbox: List[float], page_rect) -> Optional[Tuple[str, float]]:
        if not bbox or page_rect is None:
            return None
        try:
            x0, y0, x1, y1 = bbox
        except Exception:
            return None
        width = max(float(x1) - float(x0), 0.0)
        height = max(float(y1) - float(y0), 0.0)
        if width <= 0.0 or height <= 0.0:
            return None
        page_area = max(page_rect.width * page_rect.height, 1.0)
        area_ratio = (width * height) / page_area
        if area_ratio < 5e-4:
            return None
        aspect = width / height if height else 0.0
        center_y = ((float(y0) + float(y1)) / 2.0) / max(page_rect.height, 1.0)
        if center_y > 0.6 and aspect >= 2.5 and area_ratio < 0.1:
            confidence = min(1.0, 0.55 + min((aspect - 2.5) * 0.1, 0.4))
            return "signature", confidence
        if 0.5 <= aspect <= 1.5 and 0.003 <= area_ratio <= 0.1:
            confidence = min(1.0, 0.6 + (0.1 - abs(aspect - 1.0)) * 1.2)
            return "stamp", confidence
        if center_y < 0.25 and area_ratio <= 0.15:
            confidence = min(1.0, 0.6 + (0.15 - area_ratio) * 1.5)
            return "logo", confidence
        return None

    def _collect_image_artifacts(self, page, page_no: int) -> None:
        if fitz is None:
            return
        try:
            images = page.get_images(full=True)
        except Exception:
            return
        if not images:
            return
        page_rect = getattr(page, "rect", None)
        if page_rect is None:
            return
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
            if bbox is None:
                continue
            if hasattr(bbox, "tolist"):
                coords = list(bbox.tolist())
            elif isinstance(bbox, (list, tuple)):
                coords = list(bbox)
            else:
                coords = None
            if not coords or len(coords) < 4:
                continue
            coords = [float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])]
            classified = self._classify_visual_artifact(coords, page_rect)
            if not classified:
                continue
            kind, confidence = classified
            entry = {
                "page": page_no,
                "bbox": [round(value, 2) for value in coords],
                "kind": kind,
                "confidence": round(confidence, 2),
                "source": "image",
            }
            self._visual_artifacts.append(entry)
            self._log_tool_event("visual_artifact", "detected", page=page_no, details={
                "kind": kind,
                "confidence": entry["confidence"],
            })

    def _infer_language_hint(self, text: str) -> str:
        if not text:
            return 'unknown'
        normalized = re.sub(r'[^A-Za-zäöüÄÖÜß ]', ' ', text).lower()
        tokens = [tok for tok in normalized.split() if tok]
        if not tokens:
            return 'unknown'
        de_scores = sum(1 for tok in tokens if DE_TRIGGER_CHARS.intersection(tok) or tok in DE_KEYWORDS)
        en_scores = sum(1 for tok in tokens if tok in EN_KEYWORDS)
        if any(tok in DATE_KEYWORDS_DE for tok in tokens):
            de_scores += 1
        if any(tok in DATE_KEYWORDS_EN for tok in tokens):
            en_scores += 1
        if de_scores == 0 and en_scores == 0:
            return 'unknown'
        if de_scores > 0 and en_scores > 0 and abs(de_scores - en_scores) <= 1:
            return 'mixed'
        return 'de' if de_scores > en_scores else 'en'

    def _infer_locale_hint(self, text: str) -> str:
        if not text:
            return 'unknown'
        has_de = False
        has_en = False
        if re.search(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b', text):
            has_de = True
        if re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text):
            has_en = True
        if re.search(r'\d+,\d{2}\b', text) and re.search(r'\d{1,3}(\.\d{3})+\b', text):
            has_de = True
        if re.search(r'\d+\.\d{2}\b', text) and re.search(r'\d{1,3}(,\d{3})+\b', text):
            has_en = True
        if has_de and has_en:
            return 'mixed'
        if has_de:
            return 'de'
        if has_en:
            return 'en'
        return 'unknown'

    @staticmethod
    def _merge_hint(existing: Optional[str], new_hint: str) -> str:
        new_hint = new_hint or 'unknown'
        if new_hint == 'unknown':
            return existing or 'unknown'
        if not existing or existing == 'unknown':
            return new_hint
        if existing == new_hint:
            return existing
        return 'mixed'

    def _update_page_hints(self, page_no: int, text: str) -> None:
        start = time.perf_counter()
        lang_hint = self._infer_language_hint(text)
        locale_hint = self._infer_locale_hint(text)
        self._page_language_hints[page_no] = self._merge_hint(self._page_language_hints.get(page_no), lang_hint)
        self._page_locale_hints[page_no] = self._merge_hint(self._page_locale_hints.get(page_no), locale_hint)
        self._timings["lang_detect"] += (time.perf_counter() - start) * 1000.0


    def _native_page_data(self, page, page_no: int) -> Dict[str, Any]:
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
                blocks = self._build_block_entries(blocks_dict, page_no)
            except Exception:
                blocks = []
        block_count = len(blocks)
        if not text and blocks:
            text = "\n".join(entry.get("text_raw", "") for entry in blocks).strip()
        words = len(text.split()) if text else 0
        conf = self._estimate_native_conf(text, block_count, words)
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

    def _build_block_entries(self, blocks_dict: Dict[str, Any], page_no: int) -> List[Dict[str, Any]]:
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
                "is_heading_like": self._is_heading_like(text_raw, font_sizes, text_lines),
                "is_list_like": self._is_list_like(text_raw),
                "ocr_conf_avg": None,
            }
            entry.update(self._extract_style_features(text_raw, font_sizes, spans_meta))
            entries.append(entry)
        return entries

    def _is_heading_like(self, text_raw: str, font_sizes: List[float], text_lines: List[str]) -> bool:
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

    def _is_list_like(self, text_raw: str) -> bool:
        stripped = (text_raw or "").lstrip()
        if not stripped:
            return False
        bullet_prefixes = ("- ", "* ", "+ ", "\u2022", "\u2022 ")
        if stripped.startswith(bullet_prefixes):
            return True
        if re.match(r"^([0-9]+[\\).]|[a-zA-Z][\\).])\\s+", stripped):
            return True
        return False

    def _record_page_blocks(
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
            self._add_simple_block(page_no, final_text, decision, ocr_avg_conf)

        self._update_page_hints(page_no, final_text)

    def _add_simple_block(
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
        lang_hint = self._infer_language_hint(normalized_text)
        locale_hint = self._infer_locale_hint(normalized_text)
        entry = {
            "id": f"{page_no}-block-{self._block_counter}",
            "page": page_no,
            "text_raw": normalized_text,
            "text_lines": lines,
            "bbox": list(bbox) if bbox else None,
            "reading_order_index": self._block_counter,
            "is_heading_like": self._is_heading_like(normalized_text, [], lines),
            "is_list_like": self._is_list_like(lines[0] if lines else normalized_text),
            "ocr_conf_avg": ocr_avg_conf if (ocr_avg_conf is not None and "ocr" in decision_lower) else None,
            "lang_hint": lang_hint,
            "locale_hint": locale_hint,
        }
        entry.update(self._extract_style_features(normalized_text, [], []))
        self._blocks.append(entry)
        self._block_counter += 1
        self._page_language_hints[page_no] = self._merge_hint(self._page_language_hints.get(page_no), lang_hint)
        self._page_locale_hints[page_no] = self._merge_hint(self._page_locale_hints.get(page_no), locale_hint)

    def _compute_table_bbox(self, geometry: Dict[str, Any], page, zoom: float) -> Optional[List[float]]:
        row_lines = geometry.get("row_lines") or []
        col_lines = geometry.get("col_lines") or []
        if len(row_lines) < 2 or len(col_lines) < 2:
            return None
        y0_pix = min(row_lines)
        y1_pix = max(row_lines)
        x0_pix = min(col_lines)
        x1_pix = max(col_lines)
        return [
            float(page.rect.x0 + x0_pix / zoom),
            float(page.rect.y0 + y0_pix / zoom),
            float(page.rect.x0 + x1_pix / zoom),
            float(page.rect.y0 + y1_pix / zoom),
        ]

    def _cell_bbox_from_geometry(
        self,
        geometry: Dict[str, Any],
        page,
        zoom: float,
        row_idx: int,
        col_idx: int,
    ) -> Optional[List[float]]:
        row_lines = geometry.get("row_lines") or []
        col_lines = geometry.get("col_lines") or []
        if len(row_lines) <= row_idx + 1 or len(col_lines) <= col_idx + 1:
            return None
        y0_pix = row_lines[row_idx]
        y1_pix = row_lines[row_idx + 1]
        x0_pix = col_lines[col_idx]
        x1_pix = col_lines[col_idx + 1]
        return [
            float(page.rect.x0 + x0_pix / zoom),
            float(page.rect.y0 + y0_pix / zoom),
            float(page.rect.x0 + x1_pix / zoom),
            float(page.rect.y0 + y1_pix / zoom),
        ]

    def _append_table_raw(
        self,
        page_no: int,
        extraction_tool: str,
        status: str,
        bbox: Optional[List[float]] = None,
        cells: Optional[List[Dict[str, Any]]] = None,
        table_text: Optional[str] = None,
    ) -> None:
        record: Dict[str, Any] = {
            "id": f"{page_no}-table-{len(self._tables_raw)}",
            "page": page_no,
            "bbox": bbox,
            "extraction_tool": extraction_tool,
            "status": status,
        }
        if cells is not None:
            record["cells"] = cells
        if table_text:
            record["table_text"] = table_text
        self._tables_raw.append(record)
        if status == "ok":
            self._table_counts[page_no] += 1
        self._log_tool_event("table_extract", status, page=page_no, details={"tool": extraction_tool})


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
            self._log_tool_event("ocr_runner", "unavailable", details={"reason": "pytesseract_missing"})
            return {}
        if ocr_runner is None:
            self._log_warning("ocr_runner_missing")
            self._log_tool_event("ocr_runner", "unavailable", details={"reason": "runner_missing"})
            return {}
        try:
            debug_dir = None
            if self.opts.verbose:
                debug_dir = self.readers_dir / "ocr_debug"
            start = time.perf_counter()
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
            self._timings["ocr"] += (time.perf_counter() - start) * 1000.0
        except Exception as exc:  # pragma: no cover - external OCR errors
            self._log_warning(f"ocr_runner_error:{exc}")
            self._log_tool_event("ocr_runner", "error", details={"error": str(exc), "pages": pages})
            return {}
        lookup: Dict[int, Dict[str, object]] = {}
        for item in results:
            page_no = int(item.get("page_no", 0) or 0)
            if page_no > 0:
                lookup[page_no] = item
        status = "ok" if lookup else "empty"
        self._log_tool_event("ocr_runner", status, details={"pages": pages, "covered": sorted(lookup.keys()), "lang": self.opts.lang})
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
            tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
            self._append_table_raw(page_no, tool, "failed")
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
            tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
            self._append_table_raw(page_no, tool, "failed")
            return
        export_dir = None
        if self.opts.save_table_crops and not detect_only:
            export_dir = str(self.readers_dir / "tables")
        sensitivity = "high" if mode_value == "full" else "normal"
        start_extract = time.perf_counter()
        try:
            rows, metrics, geometry = extract_tables_from_image(
                arr,
                lang=self.opts.lang,
                sensitivity=sensitivity,
                export_dir=export_dir,
                page_tag=f"{page_no:04d}",
                allow_borderless=True,
                ocr_cells=not detect_only,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start_extract) * 1000.0
            if detect_only:
                self._timings["table_detect"] += elapsed
            else:
                self._timings["table_extract"] += elapsed
            self._log_warning(f"table_extract_error:p{page_no}:{exc}")
            tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
            self._append_table_raw(page_no, tool, "failed")
            return
        elapsed = (time.perf_counter() - start_extract) * 1000.0
        if detect_only:
            self._timings["table_detect"] += elapsed
        else:
            self._timings["table_extract"] += elapsed
        geometry = geometry or {}
        geometry.setdefault("row_lines", [])
        geometry.setdefault("col_lines", [])
        if arr.ndim >= 2:
            geometry.setdefault("image_height", int(arr.shape[0]))
            geometry.setdefault("image_width", int(arr.shape[1]))
        geometry.setdefault("page_width", float(page.rect.width))
        geometry.setdefault("page_height", float(page.rect.height))
        geometry["zoom"] = zoom
        geometry.setdefault("image_width", arr.shape[1] if arr.ndim >= 2 else 0)
        geometry.setdefault("image_height", arr.shape[0] if arr.ndim >= 2 else 0)
        geometry["zoom"] = zoom
        table_bbox = self._compute_table_bbox(geometry, page, zoom)
        decision_lower = (decision or "").lower()
        extraction_tool = "ocr" if "ocr" in decision_lower else "camelot"
        if not rows:
            table_text = None
            status = "failed"
            if ocr_data and ocr_data.get("text"):
                table_text = ocr_data.get("text")
                status = "fallback"
            self._append_table_raw(page_no, extraction_tool, status, bbox=table_bbox, table_text=table_text)
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
                self._append_table_raw(page_no, extraction_tool, "failed", bbox=table_bbox)
                return
            rows = [["" for _ in row] for row in rows]
        else:
            min_words = max(int(getattr(self.opts, "tables_min_words", 0)), 0)
            total_words = sum(len(str(cell).split()) for row in rows for cell in row)
            if min_words and total_words < min_words:
                self._append_table_raw(page_no, extraction_tool, "failed", bbox=table_bbox)
                return
        cells_payload: List[Dict[str, Any]] = []
        for r_index, row_cells in enumerate(rows):
            for c_index, text_value in enumerate(row_cells):
                cell_bbox = self._cell_bbox_from_geometry(geometry, page, zoom, r_index, c_index)
                cells_payload.append(
                    {
                        "row": r_index,
                        "col": c_index,
                        "text": text_value or "",
                        "bbox": cell_bbox,
                        "row_span": 1,
                        "col_span": 1,
                    }
                )
        self._append_table_raw(page_no, extraction_tool, "ok", bbox=table_bbox, cells=cells_payload)
        table_record = TableRecord(file=str(pdf_path), page=page_no, rows=rows, decision=decision, metrics=metrics_clean)
        self._tables.append(table_record)
        self._table_flags.add(page_no)
        self._table_candidates[page_no] = metrics_clean

    def _ocr_image_file(self, path: Path) -> None:
        if Image is None or pytesseract is None:
            self._log_warning("image_ocr_unavailable")
            self._log_tool_event("image_ocr", "unavailable")
            return
        start = time.perf_counter()
        try:
            image = Image.open(path).convert("RGB")
            self._log_tool_event("image_open", "ok", details={"file": str(path)})
        except Exception as exc:
            self._log_warning(f"read_image_error:{exc}")
            self._log_tool_event("image_open", "error", details={"file": str(path), "error": str(exc)})
            return
        try:
            cfg = f"-l {getattr(self.opts, 'lang', 'eng')} --oem {getattr(self.opts, 'oem', 3)} --psm {getattr(self.opts, 'psm', 6)}"
            data = pytesseract.image_to_data(image, output_type="dict", config=cfg)
            words = data.get("text", []) or []
            confs = data.get("conf", []) or []
            text = " \n".join(word for word in words if word and word.strip() and word != "-1")
            conf = _safe_avg_conf(confs)
            self._log_tool_event("pytesseract", "ok", details={"file": str(path), "lang": getattr(self.opts, 'lang', 'eng')})
        except Exception as exc:
            self._log_warning(f"fallback_ocr_error:{exc}")
            self._log_tool_event("pytesseract", "error", details={"file": str(path), "error": str(exc)})
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
                chars=len(text or ""),
                ocr_conf_avg=conf if text else None,
            )
        )
        self._page_decisions.append("ocr")
        self._add_simple_block(1, text, "ocr", conf)
        self._update_page_hints(1, text)

    def _docx_native(self, path: Path) -> None:
        start = time.perf_counter()
        try:
            text = read_docx_to_text(str(path))
        except Exception as exc:
            self._log_warning(f"docx_error:{exc}")
            self._log_tool_event("docx_reader", "error", details={"file": str(path), "error": str(exc)})
            return
        elapsed = (time.perf_counter() - start) * 1000.0
        words = len(text.split()) if text else 0
        conf = 90.0 if text else 0.0
        self._log_tool_event("docx_reader", "ok", details={"file": str(path), "words": words})
        self._records.append(
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
        self._page_decisions.append("native")
        self._add_simple_block(1, text, "native", None)

    def _text_native(self, path: Path) -> None:
        start = time.perf_counter()
        try:
            text = Path(path).read_text("utf-8", errors="replace")
        except Exception as exc:
            self._log_warning(f"text_error:{exc}")
            self._log_tool_event("text_reader", "error", details={"file": str(path), "error": str(exc)})
            return
        elapsed = (time.perf_counter() - start) * 1000.0
        words = len(text.split()) if text else 0
        conf = 92.0 if text else 0.0
        self._log_tool_event("text_reader", "ok", details={"file": str(path), "words": words})
        self._records.append(
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
        self._page_decisions.append("native")
        self._add_simple_block(1, text, "native", None)

    def _fallback_pdf_native(self, path: Path) -> None:
        try:
            text = read_pdf_text(str(path))
        except Exception as exc:
            self._log_warning(f"pdf_native_error:{exc}")
            self._log_tool_event("pdf_native", "error", details={"file": str(path), "error": str(exc)})
            return
        words = len(text.split()) if text else 0
        conf = 80.0 if text else 0.0
        self._log_tool_event("pdf_native", "ok", details={"file": str(path), "words": words})
        self._records.append(
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
        self._page_decisions.append("native")
        self._add_simple_block(1, text, "native", None)

    def _process_pdf(self, path: Path) -> None:
        if fitz is None:
            self._log_warning("pymupdf_missing")
            self._log_tool_event("pymupdf", "missing", details={"file": str(path)})
            self._fallback_pdf_native(path)
            return
        try:
            doc = fitz.open(path)
            self._log_tool_event("pymupdf_open", "ok", details={"file": str(path)})
        except Exception as exc:
            self._log_warning(f"pdf_open_error:{exc}")
            self._log_tool_event("pymupdf_open", "error", details={"file": str(path), "error": str(exc)})
            self._fallback_pdf_native(path)
            return
        native_map: Dict[int, Dict[str, float]] = {}
        overlay_candidates: List[int] = []
        ocr_needed: List[int] = []
        mode = (self.opts.mode or "mixed").lower()
        for index, page in enumerate(doc):
            page_no = index + 1
            native_data = self._native_page_data(page, page_no)
            coverage, image_count = self._image_stats(page)
            self._collect_image_artifacts(page, page_no)
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
            native_blocks = native_data.get("blocks") or []
            ocr_data = ocr_lookup.get(page_no)
            ocr_avg_conf = None
            if ocr_data and ocr_data.get("avg_conf") is not None:
                try:
                    ocr_avg_conf = float(ocr_data.get("avg_conf") or 0.0)
                except Exception:
                    ocr_avg_conf = float(ocr_data.get("avg_conf"))
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
            self._record_page_blocks(page_no, decision, native_blocks, final_text, ocr_avg_conf)
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
                    chars=len(final_text or ""),
                    ocr_conf_avg=ocr_avg_conf,
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
        summary_dict["text_blocks_count"] = len(self._blocks)
        summary_dict["tables_raw_count"] = len(self._tables_raw)
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
        tables_raw_path = self.readers_dir / "tables_raw.jsonl"
        with open(tables_raw_path, "w", encoding="utf-8") as handle:
            for entry in self._tables_raw:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
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
            "text_blocks_count": len(self._blocks),
            "tables_raw_count": len(self._tables_raw),
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
        summary_path = self.readers_dir / "readers_summary.json"
        payload = {"summary": summary, "tool_log": summary["tool_log"]}
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._tool_events:
            log_path = self.readers_dir / "tool_log.jsonl"
            with open(log_path, "w", encoding="utf-8") as handle:
                for event in self._tool_events:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
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

    lang_lookup = {int(entry.get("page", 0) or 0): entry.get("lang") or "unknown" for entry in summary.get("lang_per_page", []) or []}
    locale_lookup = {int(entry.get("page", 0) or 0): entry.get("locale") or "unknown" for entry in summary.get("locale_per_page", []) or []}
    table_counts = {int(page): int(count) for page, count in (summary.get("table_counts") or {}).items()}
    tool_events = summary.get("tool_log", []) or []
    table_fail_pages = {int(event.get("page") or 0) for event in tool_events if event.get("step") == "table_extract" and str(event.get("status")).lower() in {"failed", "fallback"}}
    per_page = []
    flagged = []
    any_thr = float(thresholds.get("any_min_conf", 70.0))
    ocr_thr = float(thresholds.get("ocr_min_conf", 80.0))
    low_text_thr = 10
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
    payload["flags"] = {"manual_review": bool(warnings) or bool(flagged), "pages": sorted(set(flagged))}
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






