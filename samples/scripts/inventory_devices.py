#!/usr/bin/env python3
"""
Device inventory: list devices, then fetch interface inventory per device.

See docs/recipes/inventory-devices.md
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
log = logging.getLogger("inventory_devices")


def _device_key(row: dict) -> str | None:
    return (
        row.get("system-ip")
        or row.get("systemIp")
        or row.get("deviceId")
        or row.get("uuid")
    )


def main() -> int:
    p = argparse.ArgumentParser(description="SD-WAN Manager device + interface inventory sample")
    p.add_argument("--limit", type=int, default=20, help="Max devices to detail")
    p.add_argument("--output", type=Path, default=None, help="Write JSON to file")
    args = p.parse_args()

    settings = Settings.load()
    out: dict = {"devices": [], "interfaces_by_device": {}}

    with ManagerClient(settings) as client:
        client.login()
        devices_payload = client.dataservice_json("/dataservice/device")
        rows = device_rows(devices_payload)
        out["devices"] = rows[: args.limit]

        for row in out["devices"]:
            key = _device_key(row)
            if not key:
                log.warning("Skipping row without device key: %s", row.get("host-name"))
                continue
            ifpath = "/dataservice/device/interface"
            r = client.request("GET", ifpath, params={"deviceId": key})
            if not r.is_success:
                log.warning("Interface fetch failed for %s: %s %s", key, r.status_code, r.text[:120])
                out["interfaces_by_device"][key] = {"error": r.status_code, "body": r.text[:500]}
                continue
            try:
                out["interfaces_by_device"][key] = unwrap_data(r.json())
            except json.JSONDecodeError:
                out["interfaces_by_device"][key] = {"raw": r.text[:500]}

    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
