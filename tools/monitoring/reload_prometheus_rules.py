from __future__ import annotations

import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def main() -> None:
    url = os.environ.get("PROMETHEUS_URL", "http://localhost:9090").rstrip("/") + "/-/reload"
    req = Request(url, data=b"", method="POST")
    try:
        with urlopen(req) as resp:  # nosec B310
            print("Prometheus reload: HTTP", resp.status)
    except (HTTPError, URLError) as exc:
        print("Failed to reload Prometheus:", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
