from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

try:
    import pytesseract  # type: ignore
except Exception:
    pytesseract = None

def _ensure_cv2():
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) is not installed. Install opencv-python-headless or opencv-python.")

def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported image dimensions.")

def _binarize(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return 255 - th if np.mean(th) > 127 else th

def _dynamic_kernels(w: int, h: int, sensitivity: str) -> Tuple[int, int]:
    scale = 50 if sensitivity == "high" else 80
    return max(10, w // scale), max(10, h // scale)

def _extract_line_maps(binv: np.ndarray, sensitivity: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    h, w = binv.shape[:2]
    hor_k, ver_k = _dynamic_kernels(w, h, sensitivity)
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (hor_k, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, ver_k))
    horiz = cv2.dilate(cv2.erode(binv, kernel_h, iterations=1), kernel_h, iterations=1)
    vert  = cv2.dilate(cv2.erode(binv, kernel_v, iterations=1), kernel_v, iterations=1)
    grid  = cv2.add(horiz, vert)
    return horiz, vert, grid

def _project_peaks(img: np.ndarray, axis: int, min_gap: int = 5) -> List[int]:
    prof = np.sum(img > 0, axis=axis)
    if prof.size == 0 or np.max(prof) == 0:
        return []
    thr = max(5, int(0.1 * int(np.max(prof))))
    idxs = np.where(prof > thr)[0]
    if len(idxs) == 0:
        return []
    groups: List[List[int]] = [[int(idxs[0])]]
    for v in idxs[1:]:
        if abs(int(v) - groups[-1][-1]) <= min_gap:
            groups[-1].append(int(v))
        else:
            groups.append([int(v)])
    return [int(np.mean(g)) for g in groups]

def _crop_cell(img: np.ndarray, y1: int, y2: int, x1: int, x2: int, pad: int = 1) -> np.ndarray:
    h, w = img.shape[:2]
    y1p = max(0, y1 + pad); y2p = min(h, y2 - pad)
    x1p = max(0, x1 + pad); x2p = min(w, x2 - pad)
    if y2p <= y1p or x2p <= x1p:
        return img[0:0, 0:0]
    return img[y1p:y2p, x1p:x2p]

def _ocr_cell(img: np.ndarray, lang: str) -> str:
    if pytesseract is None:
        return ""
    try:
        return pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 6").strip()
    except Exception:
        return ""

def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def extract_tables_from_image(
    img: np.ndarray,
    lang: str = "deu+eng",
    sensitivity: str = "normal",
    export_dir: Optional[str] = None,
    page_tag: Optional[str] = None,
    allow_borderless: bool = True,
) -> List[List[str]]:
    """
    Detect a simple table grid and return it as rows of cell text (rows -> cells).
    Runs without Tesseract (cells become empty strings) and saves a diagnostic PNG
    when export_dir/page_tag is supplied.
    """
    _ensure_cv2()

    export_root: Optional[Path] = None
    if export_dir:
        export_root = Path(export_dir); _safe_mkdir(export_root)
        if page_tag: _safe_mkdir(export_root / "tables_pages")

    gray = _to_gray(img)
    binv = _binarize(gray)
    horiz, vert, _ = _extract_line_maps(binv, sensitivity=sensitivity)

    if np.count_nonzero(horiz) == 0 and np.count_nonzero(vert) == 0:
        if allow_borderless:
            if export_root is not None and page_tag:
                try: cv2.imwrite(str((export_root / "tables_pages" / f"{page_tag}.png").resolve()), img)
                except Exception: pass
            return []

    row_lines = _project_peaks(horiz, axis=1, min_gap=3)
    col_lines = _project_peaks(vert,  axis=0, min_gap=3)

    if len(row_lines) < 2 or len(col_lines) < 2:
        if export_root is not None and page_tag:
            try: cv2.imwrite(str((export_root / "tables_pages" / f"{page_tag}.png").resolve()), img)
            except Exception: pass
        return []

    def _dedup(vals: List[int], tol: int = 2) -> List[int]:
        if not vals: return vals
        vals = sorted(vals); keep = [vals[0]]
        for v in vals[1:]:
            if abs(v - keep[-1]) > tol: keep.append(v)
        return keep

    row_lines = _dedup(row_lines, 2)
    col_lines = _dedup(col_lines, 2)

    rows_text: List[List[str]] = []
    for r in range(len(row_lines) - 1):
        y1, y2 = row_lines[r], row_lines[r + 1]
        row_cells: List[str] = []
        for c in range(len(col_lines) - 1):
            x1, x2 = col_lines[c], col_lines[c + 1]
            cell = _crop_cell(gray, y1, y2, x1, x2, pad=1)
            row_cells.append("" if cell.size == 0 else _ocr_cell(cell, lang=lang))
        rows_text.append(row_cells)

    if export_root is not None:
        try:
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            for y in row_lines: cv2.line(vis, (0, y), (vis.shape[1]-1, y), (0,255,0), 1)
            for x in col_lines: cv2.line(vis, (x, 0), (x, vis.shape[0]-1), (255,0,0), 1)
            outpng = (export_root / ("tables_pages" if page_tag else ".") / (f"{page_tag}.png" if page_tag else "tables_debug.png")).resolve()
            cv2.imwrite(str(outpng), vis)
        except Exception:
            pass

    return rows_text



