from __future__ import annotations

"""Lightweight table candidate collector for the readers runtime."""

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ..schemas.readers_schema_settings import get_runtime_settings

SETTINGS = get_runtime_settings()
TABLE_CANDIDATE_MIN_CONF = float(SETTINGS.thresholds.get("table_candidate_min_conf", 0.45))
IMAGE_MORPH_ENABLED = bool(SETTINGS.features.get("image_morph_detection", True))
TEXT_ALIGNMENT_ENABLED = bool(SETTINGS.features.get("text_alignment_detection", True))


class LightTableDetector:
    """Collect lightweight table candidates and persist them to JSONL."""

    def __init__(self, readers_dir: Path):
        self.readers_dir = Path(readers_dir)
        self._path = self.readers_dir / "table_candidates.jsonl"
        self._candidates: List[Dict[str, Any]] = []
        self._enable_morph = IMAGE_MORPH_ENABLED
        self._enable_text_alignment = TEXT_ALIGNMENT_ENABLED

    def process_readers_reset_light_tables(self) -> None:
        self._candidates = []
        if self._path.exists():
            try:
                self._path.unlink()
            except Exception:
                pass

    @staticmethod
    def compute_readers_light_clamp_confidence(value: float) -> float:
        return max(0.0, min(1.0, round(value, 4)))

    @staticmethod
    def compute_readers_light_confidence(status: str, rows: int, cols: int, cell_count: int) -> float:
        status = (status or "failed").lower()
        base = 0.2
        if status == "ok":
            base = max(0.85, TABLE_CANDIDATE_MIN_CONF)
        elif status == "fallback":
            base = max(0.6, TABLE_CANDIDATE_MIN_CONF)
        elif status in {"detect", "candidate"}:
            base = max(0.5, TABLE_CANDIDATE_MIN_CONF)
        elif status == "failed":
            base = 0.2
        elif status == "inadmissible":
            base = 0.1
        richness = min(cell_count / 200.0, 1.0)
        structure = 0.0
        if rows >= 2 and cols >= 2:
            structure = 0.25
        elif rows >= 1 and cols >= 1:
            structure = 0.1
        return LightTableDetector.compute_readers_light_clamp_confidence(base + 0.25 * richness + structure)




    @staticmethod
    def compute_readers_light_cues(rows: int, cols: int, gridlines_h: int, gridlines_v: int) -> List[str]:
        cues: List[str] = []
        if gridlines_h or gridlines_v:
            cues.append("rulings")
        if cols >= 3:
            cues.append("columns")
        if rows >= 2 and cols >= 2:
            cues.append("grid")
        if not cues:
            cues.append("layout")
        return cues

    @staticmethod
    def compute_readers_bbox_or_default(bbox: Optional[Iterable[float]], fallback: Iterable[float]) -> List[float]:
        source = list(bbox) if bbox else list(fallback)
        if len(source) != 4:
            source = list(fallback)
        cleaned: List[float] = []
        for value in source[:4]:
            try:
                cleaned.append(round(float(value), 3))
            except Exception:
                cleaned.append(0.0)
        if len(cleaned) < 4:
            cleaned.extend([0.0] * (4 - len(cleaned)))
        return cleaned

    @staticmethod
    def check_readers_bbox_intersects(a: List[float], b: List[float]) -> bool:
        if len(a) < 4 or len(b) < 4:
            return False
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)

    def record_readers_light_candidate(
        self,
        *,
        page: int,
        page_bbox: Iterable[float],
        table_bbox: Optional[Iterable[float]],
        status: str,
        extraction_tool: str,
        decision: str,
        metrics: Optional[Dict[str, Any]],
        geometry: Optional[Dict[str, Any]],
        text_blocks: Iterable[Dict[str, Any]],
        rotation: float,
    ) -> None:
        rows = int(metrics.get("rows", 0) or 0) if metrics else 0
        cols = int(metrics.get("cols", 0) or 0) if metrics else 0
        cell_count = int(metrics.get("cell_count", 0) or 0) if metrics else 0
        gridlines_h = len(geometry.get("row_lines", [])) if geometry else 0
        gridlines_v = len(geometry.get("col_lines", [])) if geometry else 0

        method = "morph" if (gridlines_h or gridlines_v) else "text-alignment"
        if method == "morph" and not self._enable_morph:
            method = "text-alignment"
        if method == "text-alignment" and not self._enable_text_alignment:
            method = "morph" if self._enable_morph else "text-alignment"
        if not self._enable_morph and not self._enable_text_alignment:
            method = extraction_tool.lower() or "unknown"
        if extraction_tool.lower() == "ocr" and self._enable_text_alignment:
            method = "text-alignment"

        cues = self.compute_readers_light_cues(rows, cols, gridlines_h, gridlines_v)
        confidence = self.compute_readers_light_confidence(status, rows, cols, cell_count)

        page_box = self.compute_readers_bbox_or_default(page_bbox, [0.0, 0.0, 0.0, 0.0])
        bbox = self.compute_readers_bbox_or_default(table_bbox, page_box)

        overlaps = False
        for block in text_blocks or []:
            block_bbox = block.get("bbox")
            if isinstance(block_bbox, list):
                block_box = self.compute_readers_bbox_or_default(block_bbox, [0.0, 0.0, 0.0, 0.0])
                if self.check_readers_bbox_intersects(bbox, block_box):
                    overlaps = True
                    break

        candidate = {
            "page": int(page),
            "bbox": bbox,
            "confidence": confidence,
            "cues": cues,
            "overlaps_text": overlaps,
            "method": method,
            "gridlines_h": gridlines_h,
            "gridlines_v": gridlines_v,
            "rotation_deg": round(float(rotation or 0.0), 2),
            "status": status,
            "tool": extraction_tool,
            "decision": decision,
            "rows": rows,
            "cols": cols,
            "cell_count": cell_count,
        }
        self._candidates.append(candidate)

    def emit_readers_light_candidates(self) -> None:
        self.readers_dir.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            for candidate in self._candidates:
                handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")


ReadersLightTableDetector = LightTableDetector

__all__ = ["LightTableDetector", "ReadersLightTableDetector"]






\


# Backwards-compatible aliases
LightTableDetector.reset = LightTableDetector.process_readers_reset_light_tables
LightTableDetector.add_candidate = LightTableDetector.record_readers_light_candidate
LightTableDetector.flush = LightTableDetector.emit_readers_light_candidates
LightTableDetector._clamp_confidence = LightTableDetector.compute_readers_light_clamp_confidence
LightTableDetector._compute_confidence = LightTableDetector.compute_readers_light_confidence
LightTableDetector._compute_cues = LightTableDetector.compute_readers_light_cues
LightTableDetector._bbox_or_default = LightTableDetector.compute_readers_bbox_or_default
LightTableDetector._bbox_intersects = LightTableDetector.check_readers_bbox_intersects



# Backwards-compatible aliases
LightTableDetector.reset = LightTableDetector.process_readers_reset_light_tables
LightTableDetector.add_candidate = LightTableDetector.record_readers_light_candidate
LightTableDetector.flush = LightTableDetector.emit_readers_light_candidates
LightTableDetector._clamp_confidence = LightTableDetector.compute_readers_light_clamp_confidence
LightTableDetector._compute_confidence = LightTableDetector.compute_readers_light_confidence
LightTableDetector._compute_cues = LightTableDetector.compute_readers_light_cues
LightTableDetector._bbox_or_default = LightTableDetector.compute_readers_bbox_or_default
LightTableDetector._bbox_intersects = LightTableDetector.check_readers_bbox_intersects


# Backwards-compatible aliases
LightTableDetector.reset = LightTableDetector.process_readers_reset_light_tables
LightTableDetector.add_candidate = LightTableDetector.record_readers_light_candidate
LightTableDetector.flush = LightTableDetector.emit_readers_light_candidates
LightTableDetector._clamp_confidence = LightTableDetector.compute_readers_light_clamp_confidence
LightTableDetector._compute_confidence = LightTableDetector.compute_readers_light_confidence
LightTableDetector._compute_cues = LightTableDetector.compute_readers_light_cues
LightTableDetector._bbox_or_default = LightTableDetector.compute_readers_bbox_or_default
LightTableDetector._bbox_intersects = LightTableDetector.check_readers_bbox_intersects

