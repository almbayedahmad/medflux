from __future__ import annotations

"""Core business logic for parameter computation in the readers stage."""

from typing import Any, Dict

from ..schemas.readers_schema_options import ReaderOptions


def compute_readers_params(
    detect_meta: Dict[str, Any],
    config_options: Dict[str, Any],
    item_overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compute runtime parameters from detection metadata, config, and overrides."""
    overrides = dict(item_overrides or {})
    params: Dict[str, Any] = {}
    mode = overrides.get("mode") or detect_meta.get("detected_mode") or config_options.get("mode")
    file_type = str(detect_meta.get("file_type") or "").lower()
    confidence = float(detect_meta.get("confidence") or 0.0)
    if file_type.startswith("pdf") and confidence < 0.7:
        mode = "mixed"
    params["mode"] = str(mode or config_options.get("mode") or "mixed").lower()
    params["lang"] = overrides.get("lang") or detect_meta.get("lang") or config_options.get("lang")
    params["dpi"] = int(overrides.get("dpi") or detect_meta.get("dpi") or config_options.get("dpi", 300))
    params["psm"] = int(overrides.get("psm") or detect_meta.get("psm") or config_options.get("psm", 6))
    params["tables_mode"] = overrides.get("tables_mode") or detect_meta.get("tables_mode") or config_options.get("tables_mode", "detect")
    params["blocks_threshold"] = int(overrides.get("blocks_threshold") or config_options.get("blocks_threshold", 3))
    return params


def get_readers_options(
    params: Dict[str, Any],
    config_options: Dict[str, Any],
    item_overrides: Dict[str, Any] | None = None,
) -> ReaderOptions:
    """Build ReaderOptions from computed parameters, config, and overrides."""
    overrides = dict(item_overrides or {})
    tables_mode = params.get("tables_mode") or config_options.get("tables_mode", "detect")
    if tables_mode == "light":
        tables_mode = "detect"
    elif tables_mode == "full":
        tables_mode = "extract"
    return ReaderOptions(
        mode=params.get("mode", config_options.get("mode", "mixed")),
        lang=params.get("lang", config_options.get("lang", "deu+eng")),
        dpi_mode="auto",
        dpi=params.get("dpi", config_options.get("dpi", 300)),
        psm=params.get("psm", config_options.get("psm", 6)),
        oem=int(overrides.get("oem", config_options.get("oem", 3))),
        workers=int(overrides.get("workers", config_options.get("workers", 4))),
        use_pre=bool(overrides.get("use_pre", config_options.get("use_pre", False))),
        export_xlsx=bool(overrides.get("export_xlsx", config_options.get("export_xlsx", False))),
        verbose=bool(overrides.get("verbose", config_options.get("verbose", False))),
        tables_mode=tables_mode,
        save_table_crops=bool(overrides.get("save_table_crops", config_options.get("save_table_crops", False))),
        tables_min_words=int(overrides.get("tables_min_words", config_options.get("tables_min_words", 12))),
        table_detect_min_area=float(overrides.get("table_detect_min_area", config_options.get("table_detect_min_area", 9000.0))),
        table_detect_max_cells=int(overrides.get("table_detect_max_cells", config_options.get("table_detect_max_cells", 600))),
        blocks_threshold=params.get("blocks_threshold", config_options.get("blocks_threshold", 3)),
        native_ocr_overlay=bool(overrides.get("native_ocr_overlay", config_options.get("native_ocr_overlay", False))),
        overlay_area_thr=float(overrides.get("overlay_area_thr", config_options.get("overlay_area_thr", 0.35))),
        overlay_min_images=int(overrides.get("overlay_min_images", config_options.get("overlay_min_images", 1))),
        overlay_if_any_image=bool(overrides.get("overlay_if_any_image", config_options.get("overlay_if_any_image", False))),
    )


__all__ = [
    "compute_readers_params",
    "get_readers_options",
]
