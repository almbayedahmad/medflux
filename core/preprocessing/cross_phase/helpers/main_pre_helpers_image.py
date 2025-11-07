from __future__ import annotations

"""Image optimisation helpers for OCR pipelines.

If OpenCV (cv2) is not available, preprocessing steps are skipped gracefully,
and conversions fall back to lightweight numpy/PIL operations.
"""

from typing import Iterable

import numpy as np

try:  # optional dependency
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # type: ignore


def to_readers_cv_image(img_pil):
    """Convert a PIL image into an OpenCV BGR array."""
    arr = np.array(img_pil)
    if arr.ndim == 2:
        return arr
    if cv2 is None:
        # Without cv2, return RGB array (some callers only pass through)
        return arr
    if arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def to_readers_pil_image(img_cv):
    """Convert an OpenCV image back into a PIL image."""
    import PIL.Image as Image  # lazy import to avoid hard dependency upstream
    if len(getattr(img_cv, "shape", ())) == 0:
        return Image.fromarray(np.array(img_cv))
    if len(img_cv.shape) == 2:
        return Image.fromarray(img_cv)
    if cv2 is None:
        # Assume already RGB-like
        return Image.fromarray(img_cv)
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))


def compute_readers_skew_hough(gray: np.ndarray) -> float:
    """Estimate a small skew angle using Hough lines."""

    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=100,
        minLineLength=max(20, gray.shape[1] // 10),
        maxLineGap=10,
    )
    if lines is None:
        return 0.0

    angles = []
    for x1, y1, x2, y2 in lines[:, 0, :]:
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            continue
        ang = np.degrees(np.arctan2(dy, dx))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        if -45 <= ang <= 45:
            angles.append(ang)

    if not angles:
        return 0.0

    angles = np.array(angles, dtype=np.float32)
    q1, q3 = np.percentile(angles, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    filtered = angles[(angles >= lo) & (angles <= hi)]
    if filtered.size == 0:
        filtered = angles
    median = float(np.median(filtered))
    median = float(max(-15.0, min(15.0, median)))
    return 0.0 if abs(median) < 0.5 else median


def process_readersprocess_readers_rotate_center(img: np.ndarray, angle_deg: float) -> np.ndarray:
    h, w = img.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle_deg, 1.0)
    return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def compute_readers_osd_orientation(gray: np.ndarray) -> float | None:
    """Use Tesseract OSD to detect coarse rotation (0/90/180/270)."""

    try:
        import pytesseract  # type: ignore

        osd = pytesseract.image_to_osd(gray)
        for line in osd.splitlines():
            line = line.strip()
            if line.lower().startswith("rotate:"):
                value = int(line.split(":", 1)[1].strip())
                if value in {0, 90, 180, 270}:
                    return float(value)
    except Exception:
        return None
    return None


def process_readers_auto_deskew(img_cv: np.ndarray) -> np.ndarray:
    """Deskew an OpenCV image using OSD + Hough-based refinement."""
    if cv2 is None:
        return img_cv
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv
    rotation = compute_readers_osd_orientation(gray)
    if rotation and rotation in {90.0, 180.0, 270.0}:
        img_cv = process_readers_rotate_center(img_cv, -rotation)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv

    angle = compute_readers_skew_hough(gray)
    if angle:
        img_cv = process_readers_rotate_center(img_cv, angle)
    return img_cv


def process_readers_clahe_contrast(img_cv: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return img_cv
    lab = (
        cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        if len(img_cv.shape) == 3
        else cv2.cvtColor(cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2LAB)
    )
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)


def process_readers_unsharp_filter(img_cv: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return img_cv
    blur = cv2.GaussianBlur(img_cv, (0, 0), 1.0)
    return cv2.addWeighted(img_cv, 1.5, blur, -0.5, 0)


def process_readers_denoise_light(img_cv: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return img_cv
    if len(img_cv.shape) == 2:
        return cv2.fastNlMeansDenoising(img_cv, None, 7, 7, 21)
    return cv2.fastNlMeansDenoisingColored(img_cv, None, 5, 5, 7, 21)


def process_readers_safe_grayscale(img_cv: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return img_cv
    if len(img_cv.shape) == 3:
        return cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    return img_cv


def process_readers_adaptive_threshold(img_cv: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return img_cv
    gray = process_readers_safe_grayscale(img_cv)
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_,
        cv2.THRESH_BINARY,
        35,
        10,
    )


def process_readers_preprocess_pipeline(pil_img, steps: Iterable[str]):
    """Apply a sequence of light-weight preprocessing steps to a PIL image."""
    if cv2 is None:
        # OpenCV not available: skip preprocessing gracefully
        return pil_img
    img_cv = to_readers_cv_image(pil_img)
    for step in steps:
        name = step.strip().lower()
        if name == "deskew":
            img_cv = process_readers_auto_deskew(img_cv)
        elif name == "clahe":
            img_cv = process_readers_clahe_contrast(img_cv)
        elif name == "unsharp":
            img_cv = process_readers_unsharp_filter(img_cv)
        elif name == "denoise":
            img_cv = process_readers_denoise_light(img_cv)
        elif name == "grayscale":
            img_cv = process_readers_safe_grayscale(img_cv)
        elif name == "adaptive":
            img_cv = process_readers_adaptive_threshold(img_cv)
    return to_readers_pil_image(img_cv)


get_image_as_cv = to_readers_cv_image
get_readers_image_as_cv = to_readers_cv_image
get_image_as_pil = to_readers_pil_image
get_readers_image_as_pil = to_readers_pil_image
normalize_image_orientation = process_readers_auto_deskew
normalize_readers_image_orientation = process_readers_auto_deskew

__all__ = [
    "to_readers_cv_image",
    "to_readers_pil_image",
    "process_readers_auto_deskew",
    "process_readers_clahe_contrast",
    "process_readers_unsharp_filter",
    "process_readers_denoise_light",
    "process_readers_safe_grayscale",
    "process_readers_adaptive_threshold",
    "process_readers_preprocess_pipeline",
    "get_image_as_cv",
    "get_readers_image_as_cv",
    "get_image_as_pil",
    "get_readers_image_as_pil",
    "normalize_image_orientation",
    "normalize_readers_image_orientation",
]
