#!/usr/bin/env python3
"""
Operational "show-style" data at scale: sequential batching, optional dry-run.

Live command execution varies by platform and RBAC — default is dry-run listing.

See docs/recipes/cli-equivalents-scale.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdwan_recipes.client import ManagerClient
from sdwan_recipes.config import Settings
from sdwan_recipes.util import device_rows, unwrap_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("cli_bulk_demo")


def _key(row: dict) -> str | None:
    return row.get("system-ip") or row.get("systemIp") or row.get("deviceId")


def _fetch_live(client: ManagerClient, device_id: str):
    # Read-only diagnostics first; extend using DevNet "device action" APIs if approved.
    paths = (
        "/dataservice/device/system/properties",
        "/dataservice/device/system/status",
    )
    out = {}
    for p in paths:
        r = client.request("GET", p, params={"deviceId": device_id})
        out[p] = {"http_status": r.status_code}
        if r.is_success:
            try:
                out[p]["json"] = unwrap_data(r.json())
            except json.JSONDecodeError:
                out[p]["preview"] = r.text[:400]
        else:
            out[p]["preview"] = r.text[:200]
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Bulk read-only device diagnostics sample")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument(
        "--execute",
        action="store_true",
        help="Perform GET diagnostics (still read-only). Without this, dry-run plan only.",
    )
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    rows = []
    with ManagerClient(settings) as client:
        client.login()
        rows = device_rows(client.dataservice_json("/dataservice/device"))[: args.limit]

    plan = [{"deviceId": _key(r), "host-name": r.get("host-name")} for r in rows if _key(r)]
    if not args.execute:
        print(json.dumps({"dry_run": True, "would_query": plan}, indent=2))
        return 0

    results = []
    with ManagerClient(settings) as client:
        client.login()
        for item in plan:
            did = item["deviceId"]
            results.append({"deviceId": did, "data": _fetch_live(client, did)})

    text = json.dumps({"results": results}, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
