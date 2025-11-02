from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, List
from urllib.request import Request, urlopen


def _parse_kv(pairs: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"Invalid KEY=VALUE pair: {p}")
        k, v = p.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Send a synthetic alert to Alertmanager for testing")
    ap.add_argument("--url", default=os.environ.get("ALERTMANAGER_URL", "http://localhost:9093"), help="Alertmanager base URL")
    ap.add_argument("--severity", choices=["warning", "critical"], default="warning")
    ap.add_argument("--alertname", default="MedFluxTestAlert")
    ap.add_argument("--summary", default="Test alert from tools/monitoring/send_test_alert.py")
    ap.add_argument("--description", default="This is a synthetic alert to validate routing (Slack/Email)")
    ap.add_argument("--label", action="append", default=[], help="Extra label KEY=VALUE (repeat)")
    ap.add_argument("--annotation", action="append", default=[], help="Extra annotation KEY=VALUE (repeat)")
    ap.add_argument("--resolve", action="store_true", help="Send a resolve for this alert (endsAt=now)")
    args = ap.parse_args()

    labels: Dict[str, str] = {
        "alertname": args.alertname,
        "severity": args.severity,
        "job": "medflux",
        "instance": "local",
    }
    labels.update(_parse_kv(args.label))

    annotations: Dict[str, str] = {
        "summary": args.summary,
        "description": args.description,
    }
    annotations.update(_parse_kv(args.annotation))

    now = datetime.now(timezone.utc).isoformat()
    payload = [
        {
            "labels": labels,
            "annotations": annotations,
            "startsAt": now,
            **({"endsAt": now} if args.resolve else {}),
            "generatorURL": "medflux://tools/send_test_alert",
        }
    ]

    url = args.url.rstrip("/") + "/api/v2/alerts"
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:  # nosec B310
        code = resp.getcode()
        body = resp.read().decode("utf-8", errors="replace")
        print(f"Alertmanager response: {code}\n{body}")


if __name__ == "__main__":
    main()
