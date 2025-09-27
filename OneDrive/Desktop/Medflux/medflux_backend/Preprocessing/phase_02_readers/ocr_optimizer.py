import cv2
import numpy as np


def to_cv(img_pil):
    arr = np.array(img_pil)
    if arr.ndim == 2:
        return arr
    if arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def to_pil(img_cv):
    import PIL.Image as Image
    if len(img_cv.shape) == 2:
        return Image.fromarray(img_cv)
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))


# --------- Safe deskew helpers ---------


def _estimate_skew_hough(gray):
    """
    Estimate the skew angle using Hough lines detected along the edges.
    Returns an angle in degrees within [-15, 15]; returns 0 if no lines are found.
    """
    # Apply a light blur before edge detection
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)

    # Candidate Hough lines
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
    for l in lines:
        x1, y1, x2, y2 = l[0]
        dx, dy = x2 - x1, y2 - y1
        if dx == 0:  # Perfectly vertical line; skip it
            continue
        ang = np.degrees(np.arctan2(dy, dx))  # [-180, 180]
        # Wrap angles back toward the horizontal range (~0 degrees)
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        # After wrapping, near-horizontal angles cluster around zero
        if -45 <= ang <= 45:
            angles.append(ang)

    if not angles:
        return 0.0

    # Use a robust threshold to drop outliers
    angles = np.array(angles, dtype=np.float32)
    med = float(np.median(angles))
    # Remove extreme outliers outside the IQR to stabilise the median
    q1, q3 = np.percentile(angles, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    filt = angles[(angles >= lo) & (angles <= hi)]
    if filt.size == 0:
        filt = angles
    med = float(np.median(filt))

    # Clamp the result to a safe range
    if med < -15:
        med = -15.0
    if med > 15:
        med = 15.0
    # Ignore very small skew values
    if abs(med) < 0.5:
        return 0.0
    return med


def _rotate_center(img, angle_deg):
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle_deg, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def _fix_orientation_osd(gray):
    """
    Use Tesseract OSD to detect 90/180/270 degree orientation.
    Returns the rotation value in degrees or None if detection fails.
    """
    try:
        import pytesseract
        osd = pytesseract.image_to_osd(gray)
        # Look for the line that contains "Rotate: X"
        for line in osd.splitlines():
            line = line.strip()
            if line.lower().startswith("rotate:"):
                val = line.split(":")[1].strip()
                rot = int(val)
                if rot in (0, 90, 180, 270):
                    return rot
        return None
    except Exception:
        return None


def auto_deskew(img_cv):
    """
    Safe deskew routine:
      1) Fix coarse orientation with OSD (0/90/180/270) when available.
      2) Estimate residual skew via Hough lines when it lies between 0.5 and 15 degrees.
    """
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv

    # (Optional) correct 90/180/270 orientation first
    rot = _fix_orientation_osd(gray)
    if rot and rot in (90, 180, 270):
        # Rotate in the opposite direction to restore the upright baseline
        img_cv = _rotate_center(img_cv, -float(rot))
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv

    # Estimate any remaining small skew
    ang = _estimate_skew_hough(gray)
    if ang != 0.0:
        img_cv = _rotate_center(img_cv, ang)
    return img_cv


# --------- Other light enhancements ---------


def clahe_contrast(img_cv):
    lab = (
        cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        if len(img_cv.shape) == 3
        else cv2.cvtColor(cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2LAB)
    )
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    out = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    return out


def unsharp(img_cv):
    blur = cv2.GaussianBlur(img_cv, (0, 0), 1.0)
    sharp = cv2.addWeighted(img_cv, 1.5, blur, -0.5, 0)
    return sharp


def denoise_light(img_cv):
    if len(img_cv.shape) == 2:
        return cv2.fastNlMeansDenoising(img_cv, None, 7, 7, 21)
    else:
        return cv2.fastNlMeansDenoisingColored(img_cv, None, 5, 5, 7, 21)


def safe_grayscale(img_cv):
    if len(img_cv.shape) == 3:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_cv
    return gray


def adaptive_threshold(img_cv):
    gray = safe_grayscale(img_cv)
    th = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_,
        cv2.THRESH_BINARY,
        35,
        10,
    )
    return th


def apply_pipeline(pil_img, steps):
    """
    Supported steps: deskew (safe), clahe, unsharp, denoise, grayscale, adaptive.
    Tip: run deskew first; add clahe -> unsharp only when the input needs it.
    Avoid the adaptive threshold unless the page quality is very poor.
    """
    img_cv = to_cv(pil_img)
    for s in steps:
        ss = s.strip().lower()
        if ss == "deskew":
            img_cv = auto_deskew(img_cv)
        elif ss == "clahe":
            img_cv = clahe_contrast(img_cv)
        elif ss == "unsharp":
            img_cv = unsharp(img_cv)
        elif ss == "denoise":
            img_cv = denoise_light(img_cv)
        elif ss == "grayscale":
            img_cv = safe_grayscale(img_cv)
        elif ss == "adaptive":
            img_cv = adaptive_threshold(img_cv)
    return to_pil(img_cv)
