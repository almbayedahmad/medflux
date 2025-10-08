from __future__ import annotations

"""Visual artifact helpers for the readers runtime orchestrator."""

try:  # Optional at runtime
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None

from typing import List, Optional, Tuple


def compute_readers_visual_artifact(bbox: List[float], page_rect) -> Optional[Tuple[str, float]]:
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


def process_readers_collect_image_artifacts(orchestrator, page, page_no: int) -> None:
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
        classified = compute_readers_visual_artifact(coords, page_rect)
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
        orchestrator._visual_artifacts.append(entry)
        orchestrator._log_tool_event(
            "visual_artifact",
            "detected",
            page=page_no,
            details={"kind": kind, "confidence": entry["confidence"]},
        )


__all__ = ["compute_readers_visual_artifact", "process_readers_collect_image_artifacts"]
