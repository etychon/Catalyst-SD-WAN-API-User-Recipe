#!/usr/bin/env python3
"""
Device health: reuse device list, then attempt tunnel / system status endpoints.

See docs/recipes/health-cpu-mem-tunnels.md
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
from sdwan_recipes.util import device_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("health_tunnels")


def _device_key(row: dict) -> str | None:
    return row.get("system-ip") or row.get("systemIp") or row.get("deviceId")


def _try_json(client: ManagerClient, path: str, params: dict | None = None):
    r = client.request("GET", path, params=params)
    if not r.is_success:
        return None, r.status_code
    try:
        return r.json(), r.status_code
    except json.JSONDecodeError:
        return {"raw": r.text[:500]}, r.status_code


def main() -> int:
    p = argparse.ArgumentParser(description="Device health + tunnel statistics sample")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    report: dict = {"devices": [], "tunnel_attempts": []}

    tunnel_paths = (
        "/dataservice/device/tunnel",
        "/dataservice/device/tunnel/statistics",
    )

    with ManagerClient(settings) as client:
        client.login()
        rows = device_rows(client.dataservice_json("/dataservice/device"))[: args.limit]
        report["devices"] = rows

        for row in rows:
            key = _device_key(row)
            if not key:
                continue
            entry = {"deviceId": key, "paths": {}}
            for tp in tunnel_paths:
                data, code = _try_json(client, tp, params={"deviceId": key})
                entry["paths"][tp] = {"status": code, "data": data}
            report["tunnel_attempts"].append(entry)

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
