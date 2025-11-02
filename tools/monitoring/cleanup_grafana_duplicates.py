from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _request(method: str, url: str, data: dict | None = None, token: str | None = None, basic: str | None = None):
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif basic:
        import base64

        headers["Authorization"] = "Basic " + base64.b64encode(basic.encode("utf-8")).decode("ascii")
    req = Request(url, data=body, headers=headers, method=method)
    return urlopen(req)  # nosec B310


def _get_json(url: str, token: str | None = None, basic: str | None = None):
    try:
        with _request("GET", url, token=token, basic=basic) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _delete_dashboard_by_uid(grafana_url: str, uid: str, token: str | None, basic: str | None) -> bool:
    try:
        with _request("DELETE", f"{grafana_url}/api/dashboards/uid/{uid}", token=token, basic=basic) as resp:
            return resp.status == 200
    except HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def main() -> None:
    grafana_url = os.environ.get("GRAFANA_URL", "http://localhost:3000").rstrip("/")
    api_token = os.environ.get("GRAFANA_API_TOKEN")
    basic_auth = os.environ.get("GRAFANA_BASIC_AUTH")  # e.g., admin:admin
    if not api_token and not basic_auth:
        print("GRAFANA_API_TOKEN or GRAFANA_BASIC_AUTH must be set", file=sys.stderr)
        sys.exit(2)

    dashboards_dir = Path(__file__).resolve().parent / "dashboards"
    files = sorted(dashboards_dir.glob("*.json"))
    if not files:
        print(f"No dashboards found in {dashboards_dir}")
        return

    # Find duplicates in the General folder (id 0) that are not provisioned
    removed = 0
    for p in files:
        try:
            dashboard = json.loads(p.read_text(encoding="utf-8"))
            uid = dashboard.get("uid")
            title = dashboard.get("title")
            if not uid:
                continue

            meta = _get_json(f"{grafana_url}/api/dashboards/uid/{uid}", token=api_token, basic=basic_auth)
            if not meta:
                continue
            is_provisioned = meta.get("meta", {}).get("provisioned")
            folder_id = meta.get("meta", {}).get("folderId")
            if not is_provisioned and folder_id == 0:
                if _delete_dashboard_by_uid(grafana_url, uid, api_token, basic_auth):
                    removed += 1
                    print(f"Removed duplicate '{title}' (uid={uid}) from General")
        except (HTTPError, URLError) as exc:
            print(f"Failed while processing {p.name}: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"Error reading {p.name}: {exc}", file=sys.stderr)

    # Also remove any dashboards with title containing 'MedFlux' in General (covers cases with differing UIDs)
    try:
        search = _get_json(f"{grafana_url}/api/search?type=dash-db&query=MedFlux&folderIds=0", token=api_token, basic=basic_auth) or []
        for item in search:
            uid = item.get("uid")
            title = item.get("title")
            if not uid:
                continue
            meta = _get_json(f"{grafana_url}/api/dashboards/uid/{uid}", token=api_token, basic=basic_auth)
            if meta and not meta.get("meta", {}).get("provisioned"):
                if _delete_dashboard_by_uid(grafana_url, uid, api_token, basic_auth):
                    removed += 1
                    print(f"Removed duplicate '{title}' (uid={uid}) from General via search")
    except (HTTPError, URLError) as exc:
        print(f"Search cleanup failed: {exc}", file=sys.stderr)

    # Remove non-provisioned duplicates inside 'MedFlux' folder too (keep provisioned ones)
    try:
        folders = _get_json(f"{grafana_url}/api/folders", token=api_token, basic=basic_auth) or []
        medflux_folder_id = next((f.get("id") for f in folders if f.get("title") == "MedFlux"), None)
        if medflux_folder_id is not None:
            search = _get_json(
                f"{grafana_url}/api/search?type=dash-db&query=MedFlux&folderIds={medflux_folder_id}",
                token=api_token,
                basic=basic_auth,
            ) or []
            for item in search:
                uid = item.get("uid")
                title = item.get("title")
                if not uid:
                    continue
                meta = _get_json(f"{grafana_url}/api/dashboards/uid/{uid}", token=api_token, basic=basic_auth)
                # Keep provisioned ones, delete only non-provisioned duplicates (e.g., imported via API)
                if meta and not meta.get("meta", {}).get("provisioned"):
                    if _delete_dashboard_by_uid(grafana_url, uid, api_token, basic=basic_auth):
                        removed += 1
                        print(f"Removed duplicate '{title}' (uid={uid}) from MedFlux folder")
    except (HTTPError, URLError) as exc:
        print(f"MedFlux folder cleanup failed: {exc}", file=sys.stderr)

    print(f"Done. Removed {removed} duplicate dashboards.")


if __name__ == "__main__":
    main()
