from __future__ import annotations

"""Table extraction helpers for the readers runtime orchestrator."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schemas.readers_schema_models import TableRecord

try:  # Optional at runtime
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None

try:  # Optional at runtime
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None

try:
    from .readers_core_ocr_tables import extract_tables_from_image
except Exception:  # pragma: no cover - legacy extractor missing
    extract_tables_from_image = None


def record_readers_table_candidate_entry(
    orchestrator,
    page,
    page_no: int,
    decision: str,
    status: str,
    extraction_tool: str,
    bbox: Optional[List[float]],
    metrics: Optional[Dict[str, Any]],
    geometry: Optional[Dict[str, Any]],
) -> None:
    try:
        rect = getattr(page, "rect") if page is not None else None
        page_bbox = [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)] if rect else [0.0, 0.0, 0.0, 0.0]
    except Exception:
        page_bbox = [0.0, 0.0, 0.0, 0.0]
    try:
        rotation = float(getattr(page, "rotation", 0) or 0.0) if page is not None else 0.0
    except Exception:
        rotation = 0.0
    text_blocks = orchestrator._blocks_for_page(page_no)
    orchestrator._light_tables.add_candidate(
        page=page_no,
        page_bbox=page_bbox,
        table_bbox=bbox,
        status=status,
        extraction_tool=extraction_tool,
        decision=decision or "",
        metrics=metrics,
        geometry=geometry,
        text_blocks=text_blocks,
        rotation=rotation,
    )


def compute_readers_table_bbox_from_geometry(geometry: Dict[str, Any], page, zoom: float) -> Optional[List[float]]:
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


def compute_readers_cell_bbox_from_geometry(
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


def process_readers_append_table_raw(
    orchestrator,
    page_no: int,
    extraction_tool: str,
    status: str,
    bbox: Optional[List[float]] = None,
    cells: Optional[List[Dict[str, Any]]] = None,
    table_text: Optional[str] = None,
) -> None:
    if status == "ok":
        orchestrator._table_counts[page_no] += 1
    orchestrator._log_tool_event(
        "table_extract",
        status,
        page=page_no,
        details={"tool": extraction_tool},
    )
    orchestrator._tables_raw.append(
        {
            "page": page_no,
            "bbox": bbox,
            "cells": cells,
            "text": table_text,
            "tool": extraction_tool,
            "status": status,
        }
    )


def process_readers_collect_tables(
    orchestrator,
    page,
    pdf_path: Path,
    page_no: int,
    decision: str,
    ocr_data: Optional[Dict[str, object]],
) -> None:
    mode_value = orchestrator._tables_mode or "off"
    if extract_tables_from_image is None or np is None or fitz is None:
        if mode_value != "off":
            orchestrator._log_warning("tables_unavailable")
        return
    if mode_value == "off":
        return

    detect_only = mode_value in {"detect", "detect-only", "check", "flag", "light"}
    if detect_only:
        dpi_hint = max(int(getattr(orchestrator.opts, "dpi", 220)) or 220, 220)
    else:
        dpi_hint = int(ocr_data.get("dpi") or orchestrator.opts.dpi or 300) if ocr_data else max(orchestrator.opts.dpi, 220)
    zoom = max(dpi_hint / 72.0, 2.0)

    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    except Exception as exc:
        orchestrator._log_warning(f"table_render_error:p{page_no}:{exc}")
        tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
        record_readers_table_candidate_entry(orchestrator, page, page_no, decision, "failed", tool, None, None, None)
        process_readers_append_table_raw(orchestrator, page_no, tool, "failed")
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
        orchestrator._log_warning(f"table_np_error:p{page_no}:{exc}")
        tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
        record_readers_table_candidate_entry(orchestrator, page, page_no, decision, "failed", tool, None, None, None)
        process_readers_append_table_raw(orchestrator, page_no, tool, "failed")
        return

    export_dir = str(orchestrator.readers_dir / "tables") if orchestrator.opts.save_table_crops and not detect_only else None
    sensitivity = "high" if mode_value == "full" else "normal"
    start_extract = time.perf_counter()
    try:
        rows, metrics, geometry = extract_tables_from_image(
            arr,
            lang=orchestrator.opts.lang,
            sensitivity=sensitivity,
            export_dir=export_dir,
            page_tag=f"{page_no:04d}",
            allow_borderless=True,
            ocr_cells=not detect_only,
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - start_extract) * 1000.0
        if detect_only:
            orchestrator._timings["table_detect"] += elapsed
        else:
            orchestrator._timings["table_extract"] += elapsed
        orchestrator._log_warning(f"table_extract_error:p{page_no}:{exc}")
        tool = "ocr" if "ocr" in (decision or "").lower() else "camelot"
        process_readers_append_table_raw(orchestrator, page_no, tool, "failed")
        return

    elapsed = (time.perf_counter() - start_extract) * 1000.0
    if detect_only:
        orchestrator._timings["table_detect"] += elapsed
    else:
        orchestrator._timings["table_extract"] += elapsed

    geometry = geometry or {}
    geometry.setdefault("row_lines", [])
    geometry.setdefault("col_lines", [])
    if arr.ndim >= 2:
        geometry.setdefault("image_height", int(arr.shape[0]))
        geometry.setdefault("image_width", int(arr.shape[1]))
    geometry.setdefault("page_width", float(page.rect.width))
    geometry.setdefault("page_height", float(page.rect.height))
    geometry["zoom"] = zoom

    table_bbox = compute_readers_table_bbox_from_geometry(geometry, page, zoom)
    decision_lower = (decision or "").lower()
    extraction_tool = "ocr" if "ocr" in decision_lower else "camelot"

    metrics = metrics or {}
    metrics_clean = {
        "rows": int(metrics.get("rows", 0) or 0),
        "cols": int(metrics.get("cols", 0) or 0),
        "cell_count": int(metrics.get("cell_count", 0) or 0),
        "avg_cell_height": float(metrics.get("avg_cell_height", 0.0) or 0.0),
        "avg_cell_width": float(metrics.get("avg_cell_width", 0.0) or 0.0),
        "avg_cell_area": float(metrics.get("avg_cell_area", 0.0) or 0.0),
    }

    if not rows:
        table_text = None
        status = "failed"
        if ocr_data and ocr_data.get("text"):
            table_text = ocr_data.get("text")
            status = "fallback"
        record_readers_table_candidate_entry(orchestrator, page, page_no, decision, status, extraction_tool, table_bbox, metrics_clean, geometry)
        process_readers_append_table_raw(orchestrator, page_no, extraction_tool, status, bbox=table_bbox, table_text=table_text)
        return

    cell_count = metrics_clean["cell_count"]
    avg_cell_area = metrics_clean["avg_cell_area"]
    if detect_only:
        min_area = float(getattr(orchestrator.opts, "table_detect_min_area", 9000.0) or 0.0)
        max_cells = int(getattr(orchestrator.opts, "table_detect_max_cells", 600) or 0)
        if cell_count == 0 or cell_count > max_cells or avg_cell_area < min_area:
            orchestrator._log_warning(
                f"table_candidate_filtered:p{page_no}:cells{cell_count}:area{avg_cell_area:.0f}"
            )
            record_readers_table_candidate_entry(orchestrator, page, page_no, decision, "failed", extraction_tool, table_bbox, metrics_clean, geometry)
            process_readers_append_table_raw(orchestrator, page_no, extraction_tool, "failed", bbox=table_bbox)
            return
        rows = [["" for _ in row_cells] for row_cells in rows]
    else:
        min_words = max(int(getattr(orchestrator.opts, "tables_min_words", 0)), 0)
        total_words = sum(len(str(cell).split()) for row in rows for cell in row)
        if min_words and total_words < min_words:
            record_readers_table_candidate_entry(orchestrator, page, page_no, decision, "failed", extraction_tool, table_bbox, metrics_clean, geometry)
            process_readers_append_table_raw(orchestrator, page_no, extraction_tool, "failed", bbox=table_bbox)
            return

    cells_payload: List[Dict[str, Any]] = []
    for r_index, row_cells in enumerate(rows):
        for c_index, text_value in enumerate(row_cells):
            cell_bbox = compute_readers_cell_bbox_from_geometry(geometry, page, zoom, r_index, c_index)
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

    status_value = "detect" if detect_only else "ok"
    record_readers_table_candidate_entry(orchestrator, page, page_no, decision, status_value, extraction_tool, table_bbox, metrics_clean, geometry)
    process_readers_append_table_raw(
        orchestrator,
        page_no,
        extraction_tool,
        "ok" if status_value == "detect" else status_value,
        bbox=table_bbox,
        cells=cells_payload,
    )

    table_record = TableRecord(file=str(pdf_path), page=page_no, rows=rows, decision=decision, metrics=metrics_clean)
    orchestrator._tables.append(table_record)
    orchestrator._table_flags.add(page_no)
    orchestrator._table_candidates[page_no] = metrics_clean


__all__ = [
    "record_table_candidate",
    "compute_table_bbox",
    "cell_bbox_from_geometry",
    "append_table_raw",
    "maybe_collect_tables",
]
