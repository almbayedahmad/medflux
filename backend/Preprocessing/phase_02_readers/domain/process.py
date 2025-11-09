# PURPOSE:#   Domain processing entry point for phase_02_readers (v2 layout).#   Contains the main readers execution logic previously located in#   domain readers core modules.## OUTCOME:#   Provides typed processing functions used by the phase API. Enables#   retirement of legacy core_functions while preserving behavior.from __future__ import annotationsimport jsonimport timefrom pathlib import Pathfrom typing import Any, Dict, List, Sequencefrom .orchestrator import ReadersOrchestratorfrom .ops.readers_core_params import compute_readers_params, get_readers_optionsfrom ..connectors.metadata import (    compute_readers_run_metadata,    get_readers_detect_meta,    get_readers_encoding_meta,)from .ops.readers_core_meta import compute_readers_doc_meta_payloadfrom core.monitoring import (    record_doc_processed,    observe_phase_step_duration,    observe_io_duration,    record_io_error,)class ReadersSegmentError(RuntimeError):    """Raised when the readers stage encounters invalid input."""def compute_readers_doc_meta(    *,    input_path: Path,    detect_meta: Dict[str, Any],    encoding_meta: Dict[str, Any],    readers_result: Dict[str, Any],    timings: Dict[str, Any],    run_id: str,    pipeline_id: str,) -> Dict[str, Any]:    """Construct readers document metadata payload.    Args:        input_path: Input document path.        detect_meta: Detection-derived metadata.        encoding_meta: Encoding-derived metadata.        readers_result: Readers orchestrator output summary.        timings: Step timings in milliseconds.        run_id: Current run identifier.        pipeline_id: Pipeline identifier.    Returns:        JSON-serializable document metadata mapping.    Outcome:        Stable, structured metadata for downstream phases.    """    return compute_readers_doc_meta_payload(        input_path=input_path,        detect_meta=detect_meta,        encoding_meta=encoding_meta,        readers_result=readers_result,        timings=timings,        run_id=run_id,        pipeline_id=pipeline_id,    )def process_readers_segment(    generic_items: Sequence[Dict[str, Any]] | None,    *,    io_config: Dict[str, Any],    options_config: Dict[str, Any],    run_metadata: Dict[str, Any] | None = None,) -> Dict[str, Any]:    """Execute the readers runtime for each input document.    Args:        generic_items: Sequence of item dicts with at least 'path'.        io_config: IO configuration mapping; expects 'out_root'.        options_config: Readers options defaults.        run_metadata: Optional run metadata; if missing it's computed.    Returns:        Mapping with 'items', 'stage_stats', and 'summary' keys.    Outcome:        Deterministic, structured outputs with timing and summary details.    """    items = list(generic_items or [])    if not items:        raise ReadersSegmentError("readers stage requires at least one input item")    run_meta = dict(run_metadata or compute_readers_run_metadata())    out_root = Path(io_config.get("out_root") or "outputs/phase_02_readers")    out_root.mkdir(parents=True, exist_ok=True)    aggregated: List[Dict[str, Any]] = []    total_conf = 0.0    total_docs = 0    warnings_total = 0    for item in items:        path_value = item.get("path") or item.get("file_path") or item.get("input")        if not path_value:            raise ReadersSegmentError("readers stage item missing 'path'")        input_path = Path(path_value)        if not input_path.exists():            raise ReadersSegmentError(f"input file not found: {input_path}")        item_overrides = {k: v for k, v in item.items() if k not in {"path", "file_path", "input"}}        file_outdir = out_root / input_path.stem        file_outdir.mkdir(parents=True, exist_ok=True)        timings: Dict[str, Any] = {            "cleaning": None,            "normalization": None,            "segmentation": None,            "merge": None,        }        detect_start = time.perf_counter()        detect_meta = get_readers_detect_meta(input_path)        timings["detect"] = (time.perf_counter() - detect_start) * 1000.0        encoding_start = time.perf_counter()        encoding_meta = get_readers_encoding_meta(input_path, detect_meta.get("file_type", ""))        timings["encoding"] = (time.perf_counter() - encoding_start) * 1000.0        try:            fsz = input_path.stat().st_size        except Exception:            fsz = None        try:            record_doc_processed("phase_02_readers", str(detect_meta.get("file_type", "")) or "unknown", bytes_count=fsz)        except Exception:            pass        params = compute_readers_params(detect_meta, options_config, item_overrides)        options = get_readers_options(params, options_config, item_overrides)        readers_start = time.perf_counter()        runner = ReadersOrchestrator(file_outdir, options)        readers_result = runner.process([input_path])        readers_elapsed = (time.perf_counter() - readers_start) * 1000.0        summary = dict(readers_result.get("summary") or {})        timings["readers"] = summary.get("timings_ms", {}).get("total_ms", readers_elapsed)        try:            observe_phase_step_duration("phase_02_readers", "detect", float(timings.get("detect") or 0.0))            observe_phase_step_duration("phase_02_readers", "encoding", float(timings.get("encoding") or 0.0))            observe_phase_step_duration("phase_02_readers", "readers", float(timings.get("readers") or readers_elapsed))        except Exception:            pass        tool_log = list(readers_result.get("tool_log") or summary.get("tool_log") or [])        if tool_log:            summary["tool_log"] = tool_log        readers_dir = Path(readers_result.get("outdir") or runner.readers_dir)        doc_meta = compute_readers_doc_meta(            input_path=input_path,            detect_meta=detect_meta,            encoding_meta=encoding_meta,            readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": tool_log},            timings=timings,            run_id=run_meta["run_id"],            pipeline_id=run_meta["pipeline_id"],        )        try:            _io_t0 = time.perf_counter()            (file_outdir / "doc_meta.json").write_text(                json.dumps(doc_meta, ensure_ascii=False, indent=2),                encoding="utf-8",            )            observe_io_duration("write", "readers_doc_meta", (time.perf_counter() - _io_t0) * 1000.0)        except Exception:            record_io_error("write", "readers_doc_meta")            raise        aggregated.append(            {                "input": str(input_path),                "outdir": str(file_outdir),                "doc_meta": doc_meta,                "summary": summary,                "timings": timings,            }        )        total_conf += float(summary.get("avg_conf") or 0.0)        total_docs += 1        warnings_total += len(summary.get("warnings") or [])    avg_conf = total_conf / total_docs if total_docs else 0.0    stage_stats = {        "documents": total_docs,        "items_processed": len(aggregated),        "avg_conf": avg_conf,        "warnings": warnings_total,    }    summary_payload = {        "run_id": run_meta["run_id"],        "pipeline_id": run_meta["pipeline_id"],        "items": aggregated,        "stage_stats": stage_stats,    }    return {        "items": aggregated,        "stage_stats": stage_stats,        "summary": summary_payload,    }__all__ = ["process_readers_segment", "ReadersSegmentError", "compute_readers_doc_meta"]
# PURPOSE:
#   Domain processing entry point for phase_02_readers (v2 layout).
#   Contains the main readers execution logic previously located in
#   domain readers core modules.
#
# OUTCOME:
#   Provides typed processing functions used by the phase API. Enables
#   retirement of legacy core_functions while preserving behavior.

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .orchestrator import ReadersOrchestrator
from .ops.readers_core_params import compute_readers_params, get_readers_options
from ..connectors.metadata import (
    compute_readers_run_metadata,
    get_readers_detect_meta,
    get_readers_encoding_meta,
)
from .ops.readers_core_meta import compute_readers_doc_meta_payload
from core.monitoring import (
    record_doc_processed,
    observe_phase_step_duration,
    observe_io_duration,
    record_io_error,
)


class ReadersSegmentError(RuntimeError):
    """Raised when the readers stage encounters invalid input."""


def compute_readers_doc_meta(
    *,
    input_path: Path,
    detect_meta: Dict[str, Any],
    encoding_meta: Dict[str, Any],
    readers_result: Dict[str, Any],
    timings: Dict[str, Any],
    run_id: str,
    pipeline_id: str,
) -> Dict[str, Any]:
    """Construct readers document metadata payload.

    Args:
        input_path: Input document path.
        detect_meta: Detection-derived metadata.
        encoding_meta: Encoding-derived metadata.
        readers_result: Readers orchestrator output summary.
        timings: Step timings in milliseconds.
        run_id: Current run identifier.
        pipeline_id: Pipeline identifier.
    Returns:
        JSON-serializable document metadata mapping.
    Outcome:
        Stable, structured metadata for downstream phases.
    """

    return compute_readers_doc_meta_payload(
        input_path=input_path,
        detect_meta=detect_meta,
        encoding_meta=encoding_meta,
        readers_result=readers_result,
        timings=timings,
        run_id=run_id,
        pipeline_id=pipeline_id,
    )


def process_readers_segment(
    generic_items: Sequence[Dict[str, Any]] | None,
    *,
    io_config: Dict[str, Any],
    options_config: Dict[str, Any],
    run_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute the readers runtime for each input document.

    Args:
        generic_items: Sequence of item dicts with at least 'path'.
        io_config: IO configuration mapping; expects 'out_root'.
        options_config: Readers options defaults.
        run_metadata: Optional run metadata; if missing it's computed.
    Returns:
        Mapping with 'items', 'stage_stats', and 'summary' keys.
    Outcome:
        Deterministic, structured outputs with timing and summary details.
    """

    items = list(generic_items or [])
    if not items:
        raise ReadersSegmentError("readers stage requires at least one input item")

    run_meta = dict(run_metadata or compute_readers_run_metadata())
    out_root = Path(io_config.get("out_root") or "outputs/phase_02_readers")
    out_root.mkdir(parents=True, exist_ok=True)

    aggregated: List[Dict[str, Any]] = []
    total_conf = 0.0
    total_docs = 0
    warnings_total = 0

    for item in items:
        path_value = item.get("path") or item.get("file_path") or item.get("input")
        if not path_value:
            raise ReadersSegmentError("readers stage item missing 'path'")
        input_path = Path(path_value)
        if not input_path.exists():
            raise ReadersSegmentError(f"input file not found: {input_path}")

        item_overrides = {k: v for k, v in item.items() if k not in {"path", "file_path", "input"}}
        file_outdir = out_root / input_path.stem
        file_outdir.mkdir(parents=True, exist_ok=True)

        timings: Dict[str, Any] = {
            "cleaning": None,
            "normalization": None,
            "segmentation": None,
            "merge": None,
        }

        detect_start = time.perf_counter()
        detect_meta = get_readers_detect_meta(input_path)
        timings["detect"] = (time.perf_counter() - detect_start) * 1000.0

        encoding_start = time.perf_counter()
        encoding_meta = get_readers_encoding_meta(input_path, detect_meta.get("file_type", ""))
        timings["encoding"] = (time.perf_counter() - encoding_start) * 1000.0

        try:
            fsz = input_path.stat().st_size
        except Exception:
            fsz = None
        try:
            record_doc_processed("phase_02_readers", str(detect_meta.get("file_type", "")) or "unknown", bytes_count=fsz)
        except Exception:
            pass

        params = compute_readers_params(detect_meta, options_config, item_overrides)
        options = get_readers_options(params, options_config, item_overrides)

        readers_start = time.perf_counter()
        runner = ReadersOrchestrator(file_outdir, options)
        readers_result = runner.process([input_path])
        readers_elapsed = (time.perf_counter() - readers_start) * 1000.0

        summary = dict(readers_result.get("summary") or {})
        timings["readers"] = summary.get("timings_ms", {}).get("total_ms", readers_elapsed)
        try:
            observe_phase_step_duration("phase_02_readers", "detect", float(timings.get("detect") or 0.0))
            observe_phase_step_duration("phase_02_readers", "encoding", float(timings.get("encoding") or 0.0))
            observe_phase_step_duration("phase_02_readers", "readers", float(timings.get("readers") or readers_elapsed))
        except Exception:
            pass

        tool_log = list(readers_result.get("tool_log") or summary.get("tool_log") or [])
        if tool_log:
            summary["tool_log"] = tool_log

        readers_dir = Path(readers_result.get("outdir") or runner.readers_dir)
        doc_meta = compute_readers_doc_meta(
            input_path=input_path,
            detect_meta=detect_meta,
            encoding_meta=encoding_meta,
            readers_result={"outdir": str(readers_dir), "summary": summary, "tool_log": tool_log},
            timings=timings,
            run_id=run_meta["run_id"],
            pipeline_id=run_meta["pipeline_id"],
        )
        try:
            _io_t0 = time.perf_counter()
            (file_outdir / "doc_meta.json").write_text(
                json.dumps(doc_meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            observe_io_duration("write", "readers_doc_meta", (time.perf_counter() - _io_t0) * 1000.0)
        except Exception:
            record_io_error("write", "readers_doc_meta")
            raise

        aggregated.append(
            {
                "input": str(input_path),
                "outdir": str(file_outdir),
                "doc_meta": doc_meta,
                "summary": summary,
                "timings": timings,
            }
        )
        total_conf += float(summary.get("avg_conf") or 0.0)
        total_docs += 1
        warnings_total += len(summary.get("warnings") or [])

    avg_conf = total_conf / total_docs if total_docs else 0.0
    stage_stats = {
        "documents": total_docs,
        "items_processed": len(aggregated),
        "avg_conf": avg_conf,
        "warnings": warnings_total,
    }
    summary_payload = {
        "run_id": run_meta["run_id"],
        "pipeline_id": run_meta["pipeline_id"],
        "items": aggregated,
        "stage_stats": stage_stats,
    }
    return {
        "items": aggregated,
        "stage_stats": stage_stats,
        "summary": summary_payload,
    }


__all__ = ["process_readers_segment", "ReadersSegmentError", "compute_readers_doc_meta"]
