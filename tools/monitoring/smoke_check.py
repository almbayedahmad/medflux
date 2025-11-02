from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Tuple

import httpx


PROM = "http://localhost:9090"
GRAFANA = "http://localhost:3000"
LOKI = "http://localhost:3100"
TEMPO = "http://localhost:3200"
AM = "http://localhost:9093"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


async def _get_json(client: httpx.AsyncClient, url: str) -> Tuple[bool, str]:
    try:
        r = await client.get(url, timeout=5)
        r.raise_for_status()
        return True, r.text
    except Exception as e:
        return False, str(e)


async def check_prometheus(client: httpx.AsyncClient) -> CheckResult:
    ok, detail = await _get_json(client, f"{PROM}/api/v1/targets")
    return CheckResult("prometheus.targets", ok, detail)


async def check_grafana(client: httpx.AsyncClient) -> CheckResult:
    ok, detail = await _get_json(client, f"{GRAFANA}/api/health")
    return CheckResult("grafana.health", ok, detail)


async def check_loki(client: httpx.AsyncClient) -> CheckResult:
    ok, detail = await _get_json(client, f"{LOKI}/ready")
    return CheckResult("loki.ready", ok, detail)


async def check_tempo(client: httpx.AsyncClient) -> CheckResult:
    ok, detail = await _get_json(client, f"{TEMPO}/status")
    return CheckResult("tempo.status", ok, detail)


async def check_alertmanager(client: httpx.AsyncClient) -> CheckResult:
    ok, detail = await _get_json(client, f"{AM}/api/v2/status")
    return CheckResult("alertmanager.status", ok, detail)


async def check_prom_query(client: httpx.AsyncClient, expr: str, name: str) -> CheckResult:
    try:
        r = await client.get(f"{PROM}/api/v1/query", params={"query": expr}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "success":
            return CheckResult(name, True, str(data.get("data", {})))
        return CheckResult(name, False, r.text)
    except Exception as e:
        return CheckResult(name, False, str(e))


async def main() -> int:
    results: List[CheckResult] = []
    async with httpx.AsyncClient() as client:
        checks = [
            check_prometheus(client),
            check_grafana(client),
            check_loki(client),
            check_tempo(client),
            check_alertmanager(client),
            check_prom_query(client, "sum(up)", "prometheus.sum_up"),
            check_prom_query(client, "sum(rate(medflux_validation_failed_total[5m]))", "prometheus.medflux_failed_rate"),
        ]
        results = await asyncio.gather(*checks)

    # Print a concise report
    any_fail = False
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"{r.name:28} {status}")
        if not r.ok:
            any_fail = True
            print(f"  detail: {r.detail[:300]}")
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
