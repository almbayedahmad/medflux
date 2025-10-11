from __future__ import annotations

"""Table extraction helpers backed by OpenCV."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    cv2 = None  # type: ignore
    CV2_IMPORT_ERROR = exc
else:
    CV2_IMPORT_ERROR = None

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None


def validate_readers_cv2_dependency() -> None:
    if cv2 is None:  # pragma: no cover
        raise RuntimeError(
            "OpenCV (cv2) is required for table extraction; install opencv-python-headless"
        ) from CV2_IMPORT_ERROR


def process_readers_to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported image dimensions for table extraction")


def process_readers_binarize_image(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return 255 - th if np.mean(th) > 127 else th


def compute_readers_dynamic_kernels(width: int, height: int, sensitivity: str) -> Tuple[int, int]:
    scale = 50 if sensitivity == "high" else 80
    return max(10, width // scale), max(10, height // scale)


def compute_readers_line_maps(binarized: np.ndarray, sensitivity: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    h, w = binarized.shape[:2]
    hor_k, ver_k = compute_readers_dynamic_kernels(w, h, sensitivity)
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k))
    horiz = cv2.dilate(cv2.erode(binarized, kernel_h, iterations=1), kernel_h, iterations=1)
    vert = cv2.dilate(cv2.erode(binarized, kernel_v, iterations=1), kernel_v, iterations=1)
    grid = cv2.add(horiz, vert)
    return horiz, vert, grid


def compute_readers_project_peaks(img: np.ndarray, axis: int, min_gap: int = 5) -> List[int]:
    profile = np.sum(img > 0, axis=axis)
    if profile.size == 0 or np.max(profile) == 0:
        return []
    threshold = max(5, int(0.1 * int(np.max(profile))))
    indices = np.where(profile > threshold)[0]
    if len(indices) == 0:
        return []
    groups: List[List[int]] = [[int(indices[0])]]
    for value in indices[1:]:
        value = int(value)
        if abs(value - groups[-1][-1]) <= min_gap:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [int(np.mean(group)) for group in groups]


def process_readers_crop_cell(img: np.ndarray, y1: int, y2: int, x1: int, x2: int, pad: int = 1) -> np.ndarray:
    h, w = img.shape[:2]
    y1p = max(0, y1 + pad)
    y2p = min(h, y2 - pad)
    x1p = max(0, x1 + pad)
    x2p = min(w, x2 - pad)
    if y2p <= y1p or x2p <= x1p:
        return img[0:0, 0:0]
    return img[y1p:y2p, x1p:x2p]


def process_readers_ocr_cell(img: np.ndarray, lang: str) -> str:
    if pytesseract is None:
        return ""
    try:
        return pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 6").strip()
    except Exception:
        return ""


def validate_readers_safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def extract_tables_from_image(
    img: np.ndarray,
    *,
    lang: str = "deu+eng",
    sensitivity: str = "normal",
    export_dir: Optional[str] = None,
    page_tag: Optional[str] = None,
    allow_borderless: bool = True,
    ocr_cells: bool = True,
) -> Tuple[List[List[str]], Dict[str, float], Dict[str, Any]]:
    """Detect a simple table grid and return the extracted cell text."""

    validate_readers_cv2_dependency()

    export_root: Optional[Path] = None
    if export_dir:
        export_root = Path(export_dir)
        validate_readers_safe_mkdir(export_root)
        if page_tag:
            validate_readers_safe_mkdir(export_root / "tables_pages")

    gray = process_readers_to_gray(img)
    binarized = process_readers_binarize_image(gray)
    horiz, vert, _ = compute_readers_line_maps(binarized, sensitivity=sensitivity)

    def compute_readers_empty_metadata(metadata: Dict[str, float]) -> Tuple[List[List[str]], Dict[str, float], Dict[str, Any]]:
        geometry: Dict[str, Any] = {
            "row_lines": [],
            "col_lines": [],
            "image_width": int(gray.shape[1]),
            "image_height": int(gray.shape[0]),
        }
        return [], metadata, geometry

    if np.count_nonzero(horiz) == 0 and np.count_nonzero(vert) == 0:
        if allow_borderless and export_root is not None and page_tag:
            try:
                cv2.imwrite(str((export_root / "tables_pages" / f"{page_tag}.png").resolve()), img)
            except Exception:
                pass
        return compute_readers_empty_metadata({
            "rows": 0,
            "cols": 0,
            "cell_count": 0,
            "avg_cell_height": 0.0,
            "avg_cell_width": 0.0,
            "avg_cell_area": 0.0,
        })

    row_lines = compute_readers_project_peaks(horiz, axis=1, min_gap=3)
    col_lines = compute_readers_project_peaks(vert, axis=0, min_gap=3)

    if len(row_lines) < 2 or len(col_lines) < 2:
        if export_root is not None and page_tag:
            try:
                cv2.imwrite(str((export_root / "tables_pages" / f"{page_tag}.png").resolve()), img)
            except Exception:
                pass
        return compute_readers_empty_metadata({
            "rows": max(len(row_lines) - 1, 0),
            "cols": max(len(col_lines) - 1, 0),
            "cell_count": 0,
            "avg_cell_height": 0.0,
            "avg_cell_width": 0.0,
            "avg_cell_area": 0.0,
        })

    def deduplicate_readers_values(values: List[int], tolerance: int = 2) -> List[int]:
        if not values:
            return values
        values = sorted(values)
        result = [values[0]]
        for v in values[1:]:
            if abs(v - result[-1]) > tolerance:
                result.append(v)
        return result

    row_lines = deduplicate_readers_values(row_lines, 2)
    col_lines = deduplicate_readers_values(col_lines, 2)

    row_count = max(len(row_lines) - 1, 0)
    col_count = max(len(col_lines) - 1, 0)
    if row_count == 0 or col_count == 0:
        return compute_readers_empty_metadata({
            "rows": row_count,
            "cols": col_count,
            "cell_count": 0,
            "avg_cell_height": 0.0,
            "avg_cell_width": 0.0,
            "avg_cell_area": 0.0,
        })

    span_height = float(row_lines[-1] - row_lines[0]) if row_count else 0.0
    span_width = float(col_lines[-1] - col_lines[0]) if col_count else 0.0
    avg_cell_height = span_height / row_count if row_count else 0.0
    avg_cell_width = span_width / col_count if col_count else 0.0
    metrics: Dict[str, float] = {
        "rows": float(row_count),
        "cols": float(col_count),
        "cell_count": float(row_count * col_count),
        "avg_cell_height": avg_cell_height,
        "avg_cell_width": avg_cell_width,
        "avg_cell_area": avg_cell_height * avg_cell_width,
    }

    rows_text: List[List[str]] = []
    for r_index in range(row_count):
        y1, y2 = row_lines[r_index], row_lines[r_index + 1]
        row_cells: List[str] = []
        for c_index in range(col_count):
            x1, x2 = col_lines[c_index], col_lines[c_index + 1]
            cell = process_readers_crop_cell(gray, y1, y2, x1, x2, pad=1)
            if cell.size == 0 or not ocr_cells:
                row_cells.append("")
            else:
                row_cells.append(process_readers_ocr_cell(cell, lang=lang))
        rows_text.append(row_cells)

    if export_root is not None:
        try:
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            for y in row_lines:
                cv2.line(vis, (0, y), (vis.shape[1] - 1, y), (0, 255, 0), 1)
            for x in col_lines:
                cv2.line(vis, (x, 0), (x, vis.shape[0] - 1), (255, 0, 0), 1)
            target = export_root / ("tables_pages" if page_tag else ".")
            validate_readers_safe_mkdir(target)
            image_name = f"{page_tag}.png" if page_tag else "tables_debug.png"
            cv2.imwrite(str((target / image_name).resolve()), vis)
        except Exception:
            pass

    geometry: Dict[str, Any] = {
        "row_lines": [int(v) for v in row_lines],
        "col_lines": [int(v) for v in col_lines],
        "image_width": int(gray.shape[1]),
        "image_height": int(gray.shape[0]),
    }

    return rows_text, metrics, geometry


def process_readers_tables_from_image(*args, **kwargs):
    """Compatibility alias that mirrors the legacy function name."""

    return extract_tables_from_image(*args, **kwargs)


__all__ = ["extract_tables_from_image", "process_readers_tables_from_image"]
