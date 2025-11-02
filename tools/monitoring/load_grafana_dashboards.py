from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _request(method: str, url: str, data: Dict[str, object] | None = None, token: str | None = None, basic: str | None = None):
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif basic:
        import base64

        headers["Authorization"] = "Basic " + base64.b64encode(basic.encode("utf-8")).decode("ascii")
    req = Request(url, data=body, headers=headers, method=method)
    return urlopen(req)  # nosec B310


def _post_json(url: str, data: Dict[str, object], token: str | None = None, basic: str | None = None) -> int:
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif basic:
        import base64

        headers["Authorization"] = "Basic " + base64.b64encode(basic.encode("utf-8")).decode("ascii")
    req = Request(url, data=body, headers=headers, method="POST")
    with urlopen(req) as resp:  # nosec B310
        return resp.status


def _get_json(url: str, token: str | None = None, basic: str | None = None):
    try:
        with _request("GET", url, token=token, basic=basic) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _ensure_folder(title: str, grafana_url: str, token: str | None, basic: str | None) -> int:
    # Try to find existing folder
    folders = _get_json(f"{grafana_url}/api/folders", token=token, basic=basic) or []
    for f in folders:
        if f.get("title") == title:
            return f.get("id")
    # Create it
    payload = {"title": title}
    with _request("POST", f"{grafana_url}/api/folders", data=payload, token=token, basic=basic) as resp:
        created = json.loads(resp.read().decode("utf-8"))
        return created.get("id")


def main() -> None:
    grafana_url = os.environ.get("GRAFANA_URL", "http://localhost:3000").rstrip("/")
    api_token = os.environ.get("GRAFANA_API_TOKEN")
    basic_auth = os.environ.get("GRAFANA_BASIC_AUTH")  # e.g., admin:admin
    if not api_token and not basic_auth:
        print("GRAFANA_API_TOKEN or GRAFANA_BASIC_AUTH must be set", file=sys.stderr)
        sys.exit(2)

    dashboards_dir = Path(__file__).resolve().parent / "dashboards"
    folder_title = os.environ.get("GRAFANA_FOLDER", "MedFlux")
    files = sorted(dashboards_dir.glob("*.json"))
    if not files:
        print(f"No dashboards found in {dashboards_dir}")
        return

    # Ensure target folder exists
    try:
        folder_id = _ensure_folder(folder_title, grafana_url, api_token, basic_auth)
    except (HTTPError, URLError) as exc:
        print(f"Failed to ensure folder '{folder_title}': {exc}", file=sys.stderr)
        sys.exit(1)

    failures = 0
    for p in files:
        try:
            dashboard = json.loads(p.read_text(encoding="utf-8"))
            uid = dashboard.get("uid")
            # Skip if provisioned to avoid duplicates
            if uid:
                meta = _get_json(f"{grafana_url}/api/dashboards/uid/{uid}", token=api_token, basic=basic_auth)
                if meta and meta.get("meta", {}).get("provisioned"):
                    print(f"Skipped {p.name} (provisioned)")
                    continue
            payload = {"dashboard": dashboard, "folderId": folder_id, "overwrite": True}
            status = _post_json(f"{grafana_url}/api/dashboards/db", payload, token=api_token, basic=basic_auth)
            print(f"Imported {p.name} into folder '{folder_title}' (HTTP {status})")
        except (HTTPError, URLError) as exc:
            print(f"Failed to import {p.name}: {exc}", file=sys.stderr)
            failures += 1
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to load {p.name}: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
