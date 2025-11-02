from __future__ import annotations

import argparse
import random
import string
import time
from typing import List

from http.client import HTTPConnection
from urllib.parse import urlparse


def _payload(n: int = 128) -> str:
    return "".join(random.choice(string.ascii_letters + string.digits + " ") for _ in range(n))


def hit(base: str, route: str, method: str = "GET", timeout: float = 3.0) -> int:
    u = urlparse(base)
    path = route if route.startswith("/") else f"/{route}"
    conn = HTTPConnection(u.hostname or "localhost", u.port or (80 if u.scheme == "http" else 443), timeout=timeout)
    try:
        headers = {"User-Agent": "medflux-traffic/1.0"}
        body = None
        if method.upper() == "POST":
            body = _payload(256)
            headers["Content-Type"] = "text/plain; charset=utf-8"
        conn.request(method.upper(), path, body=body, headers=headers)
        resp = conn.getresponse()
        # drain
        try:
            resp.read()  # nosec - just to close the connection
        except Exception:
            pass
        return int(resp.status or 0)
    except Exception:
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run(base: str, routes: List[str], duration_s: int, rate_per_s: float) -> None:
    t_end = time.time() + max(1, duration_s)
    interval = 1.0 / max(0.1, rate_per_s)
    methods = ["GET", "POST"]
    sent = 0
    ok = 0
    while time.time() < t_end:
        route = random.choice(routes)
        method = random.choice(methods)
        status = hit(base, route, method)
        sent += 1
        if 200 <= status < 500:
            ok += 1
        # jitter
        time.sleep(max(0.0, interval * random.uniform(0.5, 1.5)))
    print(f"traffic done: sent={sent} ok={ok}")


def main() -> None:
    p = argparse.ArgumentParser(description="Generate simple API traffic against a base URL.")
    p.add_argument("--base", default="http://localhost:8000", help="Base URL, e.g., http://localhost:8000")
    p.add_argument(
        "--routes",
        nargs="*",
        default=["/api/v1/health", "/api/v1/validate", "/api/v1/upload", "/metrics", "/does-not-exist"],
        help="Routes to hit under the base URL",
    )
    p.add_argument("--duration", type=int, default=60, help="Duration seconds")
    p.add_argument("--rate", type=float, default=5.0, help="Requests per second")
    args = p.parse_args()
    run(args.base, list(args.routes), args.duration, args.rate)


if __name__ == "__main__":
    main()
