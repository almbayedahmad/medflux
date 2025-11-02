from __future__ import annotations

import os
import time

from core.monitoring import init_monitoring
from core.monitoring.metrics import record_validation


def main() -> None:
    # Enable monitoring; prefer a non-default port
    os.environ.setdefault("MEDFLUX_MONITORING", "1")
    os.environ.setdefault("MEDFLUX_PROM_PORT", "8001")
    init_monitoring()
    # Emit some metrics
    for _ in range(3):
        record_validation("input", "selfcheck", True, None, 3.2)
        record_validation("output", "selfcheck", False, "VL-E999", 12.5)
    # Keep process alive briefly so /metrics can be scraped manually
    time.sleep(1.0)
    print("Self-check emitted validation metrics on port", os.environ.get("MEDFLUX_PROM_PORT"))


if __name__ == "__main__":
    main()
