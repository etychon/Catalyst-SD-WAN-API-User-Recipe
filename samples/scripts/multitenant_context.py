#!/usr/bin/env python3
"""
Probe multi-tenant / single-tenant context: server info, tenant list, device sample.

See docs/multitenant-clusters.md and docs/recipes/multitenant-connectivity.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings
from sdwan_recipes.util import device_rows, unwrap_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("multitenant_context")


def _safe_json(client: ManagerClient, method: str, path: str) -> dict[str, Any]:
    try:
        r = client.request(method, path)
        body: dict[str, Any] = {
            "http_status": r.status_code,
            "content_type": r.headers.get("content-type", ""),
        }
        if r.headers.get("content-type", "").startswith("application/json"):
            body["json"] = r.json()
        else:
            body["text_preview"] = (r.text or "")[:400]
        return body
    except (httpx.HTTPError, json.JSONDecodeError, SdwanApiError) as exc:
        return {"error": str(exc)}


def main() -> int:
    p = argparse.ArgumentParser(description="SD-WAN Manager multi-tenant / tenancy context probe")
    p.add_argument("--output", type=Path, default=None, help="Write JSON report to this path")
    args = p.parse_args()

    settings = Settings.load()
    report: dict[str, Any] = {
        "base_url": settings.base_url,
        "auth_mode": settings.auth_mode,
        "tenant_env_set": bool(settings.tenant),
        "tenant_subdomain_env": settings.tenant_subdomain or "",
        "vsession_from_env": bool(settings.vsession_id),
    }

    with ManagerClient(settings) as client:
        client.login()
        report["server"] = _safe_json(client, "GET", "/dataservice/client/server")
        report["tenant_get"] = _safe_json(client, "GET", "/dataservice/tenant")

        # Device probe (read-only, common RBAC)
        try:
            dev = client.dataservice_json("/dataservice/device")
            rows = device_rows(dev)
            report["device_sample"] = {
                "count": len(rows),
                "first_hostnames": [r.get("host-name") or r.get("hostname") for r in rows[:5]],
            }
        except (httpx.HTTPError, SdwanApiError, json.JSONDecodeError) as exc:
            report["device_sample"] = {"error": str(exc)}

        tg = report.get("tenant_get", {})
        inner = tg.get("json") if isinstance(tg, dict) else None
        if isinstance(inner, dict):
            data = unwrap_data(inner)
            if isinstance(data, list):
                report["tenant_rows_preview"] = [
                    {
                        "name": x.get("name") if isinstance(x, dict) else None,
                        "subDomain": (x.get("subDomain") or x.get("subdomain")) if isinstance(x, dict) else None,
                        "tenantId": (x.get("tenantId") or x.get("tenant_id")) if isinstance(x, dict) else None,
                    }
                    for x in data[:20]
                    if isinstance(x, dict)
                ]
                report["tenant_list_count"] = len(data)

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        log.info("Wrote %s", args.output)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
