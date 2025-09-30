from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class LightTableDetector:
    """Collects lightweight table candidates and emits a JSONL artifact."""

    def __init__(self, readers_dir: Path):
        self.readers_dir = Path(readers_dir)
        self._path = self.readers_dir / "table_candidates.jsonl"
        self._candidates: List[Dict[str, Any]] = []

    def reset(self) -> None:
        self._candidates = []
        if self._path.exists():
            try:
                self._path.unlink()
            except Exception:
                pass

    @staticmethod
    def _clamp_confidence(value: float) -> float:
        return max(0.0, min(1.0, round(value, 4)))

    @staticmethod
    def _compute_confidence(status: str, rows: int, cols: int, cell_count: int) -> float:
        status = (status or "failed").lower()
        base = 0.2
        if status == "ok":
            base = 0.85
        elif status == "fallback":
            base = 0.6
        elif status in {"detect", "candidate"}:
            base = 0.5
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
        return LightTableDetector._clamp_confidence(base + 0.25 * richness + structure)

    @staticmethod
    def _compute_cues(rows: int, cols: int, gridlines_h: int, gridlines_v: int) -> List[str]:
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
    def _bbox_or_default(bbox: Optional[Iterable[float]], fallback: Iterable[float]) -> List[float]:
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
    def _bbox_intersects(a: List[float], b: List[float]) -> bool:
        if len(a) < 4 or len(b) < 4:
            return False
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)

    def add_candidate(
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
        if extraction_tool.lower() == "ocr":
            method = "text-alignment"

        cues = self._compute_cues(rows, cols, gridlines_h, gridlines_v)
        confidence = self._compute_confidence(status, rows, cols, cell_count)

        page_box = self._bbox_or_default(page_bbox, [0.0, 0.0, 0.0, 0.0])
        bbox = self._bbox_or_default(table_bbox, page_box)

        overlaps = False
        for block in text_blocks or []:
            block_bbox = block.get("bbox")
            if isinstance(block_bbox, list) and self._bbox_intersects(bbox, self._bbox_or_default(block_bbox, [0.0, 0.0, 0.0, 0.0])):
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

    def flush(self) -> None:
        self.readers_dir.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            for candidate in self._candidates:
                handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")
