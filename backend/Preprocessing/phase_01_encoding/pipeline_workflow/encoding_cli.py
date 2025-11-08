from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .encoding_pipeline import run_encoding_pipeline
from core.logging import configure_logging, configure_log_destination, get_logger, log_context
from core.logging.context import set_ctx
from core.logging.uncaught import install_uncaught_hook
from core.logging.queue_setup import stop_queue
import uuid, os, socket
from datetime import datetime
from core.versioning import make_artifact_stamp
from core.monitoring import init_monitoring, start_phase_span, record_phase_run


def process_encoding_build_items(paths: list[str], normalize: bool) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    for path in paths:
        entry: Dict[str, Any] = {"path": path}
        if normalize:
            entry["normalize"] = True
        items.append(entry)
    return items


def _generate_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]


def run_encoding_cli() -> None:
    parser = argparse.ArgumentParser(description="Run Encoding stage")
    parser.add_argument("paths", nargs="+", help="Input files to analyse")
    parser.add_argument("--stage", default="encoding", help="Stage name override")
    parser.add_argument("--normalize", action="store_true", help="Enable UTF-8 normalization")
    parser.add_argument("--dest-outdir", help="Destination directory for normalized files")
    parser.add_argument("--newline", choices=["lf", "crlf"], help="Newline normalization policy")
    parser.add_argument("--errors", choices=["strict", "replace", "ignore"], help="Decoding error policy")
    parser.add_argument("--log-level", choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"])  # noqa: E501
    parser.add_argument("--log-json", action="store_true")
    parser.add_argument("--log-profile", choices=["dev","prod"])
    parser.add_argument("--log-stderr", action="store_true")
    args = parser.parse_args()

    if args.log_level:
        os.environ["MEDFLUX_LOG_LEVEL"] = args.log_level
    if args.log_json:
        os.environ["MEDFLUX_LOG_FORMAT"] = "json"
    if args.log_profile:
        os.environ["MEDFLUX_LOG_PROFILE"] = args.log_profile
    if args.log_stderr:
        os.environ["MEDFLUX_LOG_TO_STDERR"] = "1"
    configure_logging(force=True)
    init_monitoring()
    install_uncaught_hook()

    run_id = _generate_run_id()
    phase = "phase_01_encoding"
    log = get_logger(__name__)
    configure_log_destination(run_id, phase)

    items = process_encoding_build_items(list(args.paths), args.normalize)

    overrides: Dict[str, Any] = {}
    normalization_cfg: Dict[str, Any] = {}
    if args.normalize:
        normalization_cfg["enabled"] = True
    if args.dest_outdir:
        normalization_cfg["out_dir"] = args.dest_outdir
    if args.newline:
        normalization_cfg["newline_policy"] = args.newline
    if args.errors:
        normalization_cfg["errors"] = args.errors
    if normalization_cfg:
        overrides["normalization"] = normalization_cfg

    set_ctx(run_id=run_id, flow="preprocessing", phase=phase)
    try:
        with log_context(log, run_id=run_id, flow="preprocessing", phase=phase, hostname=socket.gethostname(), pid=os.getpid()):
            with start_phase_span(phase, run_id):
                log.info("CLI start")
                payload = run_encoding_pipeline(
                    items,
                    stage_name=args.stage,
                    config_overrides=overrides or None,
                    run_id=run_id,
                )

            print(
                json.dumps(
                    {
                        "run_id": run_id,
                        "unified_document": payload["unified_document"],
                        "stage_stats": payload["stage_stats"],
                        **make_artifact_stamp(schema_name="phase_01_encoding_output"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            log.info("CLI done")
            record_phase_run(phase, "ok")
    except Exception:
        try:
            record_phase_run(phase, "error")
        except Exception:
            pass
        raise
    finally:
        stop_queue()


if __name__ == "__main__":
    run_encoding_cli()
