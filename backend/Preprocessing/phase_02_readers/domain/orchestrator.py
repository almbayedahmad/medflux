"""Readers orchestrator (single source of truth).

PURPOSE:
  Provide the ReadersOrchestrator class within the domain layer, without
  depending on a secondary module. This consolidates the implementation and
  avoids fragile import indirection.

OUTCOME:
  Exposes a concrete orchestrator API used by process_readers_segment(),
  producing a summary payload and runtime state for doc_meta composition.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..schemas.readers_schema_models import PageRecord
from ..schemas.readers_schema_options import ReaderOptions
from ..schemas.readers_schema_settings import get_runtime_settings
from ..domain.helpers_logging import (
    record_readers_tool_event as log_tool_event,
    record_readers_warning as log_warning,
)
from .ops.readers_core_native import (
    process_readers_text_native,
    process_readers_pdf_document,
    process_readers_pdf_fallback,
)
from .ops.readers_core_ocr import run_pdf_ocr, process_readers_ocr_result, process_readers_merge_text
from .ops.readers_core_tables import process_readers_collect_tables
from .ops.readers_core_artifacts import process_readers_collect_image_artifacts


SETTINGS = get_runtime_settings()


class ReadersOrchestrator:
    def __init__(self, outdir: Path, opts: ReaderOptions) -> None:  # noqa: D401
        self.base_outdir = Path(outdir)
        self.outdir = self.base_outdir
        self.readers_dir = self.base_outdir / "readers"
        self.readers_dir.mkdir(parents=True, exist_ok=True)
        self.opts = opts
        # Runtime state used by ops
        self._records: List[PageRecord] = []
        self._warnings: List[str] = []
        self._page_decisions: List[str] = []
        self._blocks: List[Dict[str, Any]] = []
        self._zones: List[Dict[str, Any]] = []
        self._page_geometry: Dict[int, Dict[str, float]] = {}
        self._timings: Dict[str, float] = {"ocr": 0.0, "text": 0.0}
        self._tool_events: List[Dict[str, Any]] = []

    # Logging shims
    def _log_warning(self, code: str) -> None:
        log_warning(self.readers_dir, self._warnings, code)

    def _log_tool_event(self, step: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        log_tool_event(self.readers_dir, self._tool_events, step=step, status=status, details=details)

    # Helpers used by ops
    def _add_simple_block(self, page_no: int, text: str, source: str, conf: Optional[float]) -> None:
        if not text:
            return
        entry = {
            "id": f"{page_no}-0",
            "page": page_no,
            "text_raw": text,
            "bbox": [0.0, 0.0, 0.0, 0.0],
            "source": source,
            "conf": conf,
        }
        self._blocks.append(entry)

    def _record_page_blocks(
        self,
        page_no: int,
        decision: str,
        native_blocks: List[Dict[str, Any]] | None,
        final_text: str,
        ocr_avg_conf: Optional[float],
    ) -> None:
        if native_blocks:
            self._blocks.extend(native_blocks)

    def _update_zones(self, page, page_no: int) -> None:
        try:
            rect = getattr(page, "rect")
            y0 = float(rect.y0)
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
        for block in list(self._blocks):
            if int(block.get("page", 0)) != page_no:
                continue
            bbox = block.get("bbox")
            if not (isinstance(bbox, (list, tuple)) and len(bbox) >= 4):
                continue
            try:
                bx0, by0, bx1, by1 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            except Exception:
                continue
            if by1 <= header_band:
                header_boxes.append((bx0, by0, bx1, by1))
            if by0 >= footer_band:
                footer_boxes.append((bx0, by0, bx1, by1))
        def _merge(boxes: List[Tuple[float, float, float, float]]) -> List[float]:
            if not boxes:
                return []
            x0 = min(b[0] for b in boxes)
            y0 = min(b[1] for b in boxes)
            x1 = max(b[2] for b in boxes)
            y1 = max(b[3] for b in boxes)
            return [x0, y0, x1, y1]
        self._zones = [z for z in self._zones if int(z.get("page", 0)) != page_no]
        hb = _merge(header_boxes)
        fb = _merge(footer_boxes)
        if hb:
            self._zones.append({"page": page_no, "bbox": hb, "type": "header"})
        if fb:
            self._zones.append({"page": page_no, "bbox": fb, "type": "footer"})

    # Text/confidence heuristics
    def compute_readers_native_confidence(self, text: str, block_count: int, words: int) -> float:
        if not text:
            return 0.0
        base = 60.0
        bonus = min(40.0, float(words) / 50.0 * 10.0 + float(block_count) * 1.0)
        return round(min(99.0, base + bonus), 2)

    def _should_overlay(self, native_text: str, native_conf: float, coverage: float, image_count: int) -> bool:
        if image_count > 0 and coverage > 0.35:
            return True
        if native_conf < 60.0 and len(native_text.split()) < 50:
            return True
        return False

    def _should_use_native_mixed(self, conf: float, block_count: int, words: int, coverage: float, image_count: int) -> bool:
        if image_count == 0 and coverage < 0.1 and conf >= 70.0 and words > 50:
            return True
        return False

    # Native page data extraction (used internally by ops)
    def _native_page_data(self, page, page_no: int) -> Dict[str, Any]:
        import time as _t
        start = _t.perf_counter()
        try:
            rect = getattr(page, "rect")
            width = float(getattr(rect, "width", 0.0))
            height = float(getattr(rect, "height", 0.0))
        except Exception:
            width = height = 0.0
        try:
            text = page.get_text("text") or ""
        except Exception:
            text = ""
        try:
            blocks_dict = page.get_text("dict") or {}
        except Exception:
            blocks_dict = {}
        blocks: List[Dict[str, Any]] = []
        if isinstance(blocks_dict, dict):
            try:
                blocks = self.compute_readers_block_entries(blocks_dict, page_no)
            except Exception:
                blocks = []
        words = len(text.split()) if text else 0
        conf = self.compute_readers_native_confidence(text, len(blocks), words)
        # Geometry persist
        rotation = float(getattr(page, "rotation", 0) or 0.0)
        self._page_geometry[page_no] = {"width": width, "height": height, "rotation": rotation, "images_count": 0}
        elapsed = (_t.perf_counter() - start) * 1000.0
        return {"text": text, "conf": conf, "words": words, "time_ms": elapsed, "blocks": blocks, "coverage": 0.0, "image_count": 0}

    def compute_readers_block_entries(self, blocks_dict: Dict[str, Any], page_no: int) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        blocks = blocks_dict.get("blocks") or []
        for idx, block in enumerate(blocks):
            bbox = block.get("bbox")
            if not (isinstance(bbox, (list, tuple)) and len(bbox) >= 4):
                continue
            text_lines: List[str] = []
            for line in block.get("lines", []) or []:
                parts: List[str] = []
                for span in line.get("spans", []) or []:
                    s = span.get("text")
                    if isinstance(s, str) and s:
                        parts.append(s)
                line_text = "".join(parts).strip("\n")
                if line_text:
                    text_lines.append(line_text)
            text_raw = "\n".join(text_lines).strip()
            if not text_raw:
                continue
            try:
                bx0, by0, bx1, by1 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            except Exception:
                continue
            entry = {"id": f"{page_no}-{idx}", "page": page_no, "text_raw": text_raw, "bbox": [bx0, by0, bx1, by1]}
            entries.append(entry)
        return entries

    # Main entry
    def process(self, inputs: Sequence[Path]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        for path in inputs:
            p = Path(path)
            if not p.exists():
                self._log_warning(f"input_missing:{p}")
                continue
            ext = p.suffix.lower()
            try:
                if ext == ".txt":
                    process_readers_text_native(self, p)
                elif ext == ".pdf":
                    try:
                        process_readers_pdf_document(self, p)
                    except Exception:
                        process_readers_pdf_fallback(self, p)
                else:
                    process_readers_text_native(self, p)
            except Exception as exc:
                self._log_warning(f"reader_error:{exc}")
                continue

        total_ms = int((time.perf_counter() - t0) * 1000)
        page_count = max(1, len(self._records))
        summary = {
            "page_count": page_count,
            "avg_conf": 0.0,
            "warnings": list(self._warnings),
            "page_decisions": list(self._page_decisions) or ["text"] * page_count,
            "timings_ms": {"total_ms": total_ms},
            "tool_log": list(self._tool_events),
        }
        return {"outdir": str(self.readers_dir), "summary": summary, "tool_log": list(self._tool_events)}


__all__ = ["ReadersOrchestrator"]
