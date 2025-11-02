from __future__ import annotations

import os
import random
import time

from core.monitoring import init_monitoring
from core.monitoring.metrics import record_validation
from core.monitoring import record_phase_run, record_doc_processed, observe_api_request


def main() -> None:
    os.environ.setdefault("MEDFLUX_MONITORING", "1")
    os.environ.setdefault("MEDFLUX_PROM_PORT", os.environ.get("DEV_EXPORTER_PORT", "8001"))
    init_monitoring()
    print("Dev exporter running on port", os.environ["MEDFLUX_PROM_PORT"])  # noqa: T201
    phases = [
        ("phase_00_detect_type", ["input", "output"]),
        ("phase_01_encoding", ["input", "output"]),
        ("phase_02_readers", ["input", "output"]),
    ]
    try:
        while True:
            for phase, kinds in phases:
                for kind in kinds:
                    ok = random.random() > 0.1
                    code = None if ok else random.choice(["VL-E001", "VL-E002", "VL-E010"])
                    dur = random.uniform(2, 40) if ok else random.uniform(50, 300)
                    record_validation(kind, phase, ok, code, dur)
                # Emit a phase run status once per loop for this phase
                record_phase_run(phase, "ok" if ok else "error")
            # Emit sample docs processed and sizes
            for t in ["pdf", "txt", "image"]:
                record_doc_processed(random.choice([p for p, _ in phases]), t, bytes_count=int(random.choice([1500, 8_000, 120_000, 1_500_000])))
            # Simulate a few API requests
            for route in ["/api/v1/health", "/api/v1/validate", "/api/v1/upload"]:
                method = random.choice(["GET", "POST"])
                status = random.choice([200, 200, 200, 400, 500])
                rdur = random.uniform(5, 250) if status < 500 else random.uniform(200, 1200)
                observe_api_request(route, method, status, rdur)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Dev exporter stopped")  # noqa: T201


if __name__ == "__main__":
    main()
