from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .detect_type_pipeline import run_detect_type_pipeline
from core.logging import configure_logging, configure_log_destination, get_logger, log_context
from core.logging.context import set_ctx
from core.logging.uncaught import install_uncaught_hook
from core.logging.queue_setup import stop_queue
import uuid, os, socket
from datetime import datetime
from core.versioning import make_artifact_stamp
from core.monitoring import init_monitoring, start_phase_span, record_phase_run


def _generate_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]


def _build_items(paths: list[str]) -> list[Dict[str, Any]]:
    return [{"path": path} for path in paths]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run File Type Detection stage")
    parser.add_argument("paths", nargs="+", help="File paths to classify")
    parser.add_argument("--stage", default="detect_type", help="Stage name override")
    parser.add_argument("--log-level", choices=["DEBUG","INFO","WARNING","ERROR","CRITICAL"])  # noqa: E501
    parser.add_argument("--log-json", action="store_true")
    parser.add_argument("--log-profile", choices=["dev","prod"])
    parser.add_argument("--log-stderr", action="store_true")
    args = parser.parse_args()

    # Apply logging overrides then configure
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
    phase = "phase_00_detect_type"
    log = get_logger(__name__)
    # set destination JSONL file
    configure_log_destination(run_id, phase)

    items = _build_items(list(args.paths))
    set_ctx(run_id=run_id, flow="preprocessing", phase=phase)
    try:
        with log_context(log, run_id=run_id, flow="preprocessing", phase=phase, hostname=socket.gethostname(), pid=os.getpid()):
            with start_phase_span(phase, run_id):
                log.info("CLI start")
                payload = run_detect_type_pipeline(items, stage_name=args.stage, run_id=run_id)
            print(
                json.dumps(
                    {
                        "run_id": run_id,
                        "unified_document": payload["unified_document"],
                        "stage_stats": payload["stage_stats"],
                        **make_artifact_stamp(schema_name="phase_00_detect_type_output"),
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
    main()
