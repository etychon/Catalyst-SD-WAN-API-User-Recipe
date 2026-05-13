#!/usr/bin/env python3
"""
Transport / underlay oriented view: WAN interfaces and counters where exposed.

See docs/recipes/transport-underlay-monitoring.md
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
log = logging.getLogger("transport_underlay")


def _key(row: dict) -> str | None:
    return row.get("system-ip") or row.get("systemIp") or row.get("deviceId")


def main() -> int:
    p = argparse.ArgumentParser(description="WAN / transport interface sample")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    out: dict = {"wan_by_device": {}}

    with ManagerClient(settings) as client:
        client.login()
        rows = device_rows(client.dataservice_json("/dataservice/device"))[: args.limit]
        for row in rows:
            k = _key(row)
            if not k:
                continue
            r = client.request("GET", "/dataservice/device/interface", params={"deviceId": k})
            if not r.is_success:
                out["wan_by_device"][k] = {"error": r.status_code}
                continue
            interfaces = unwrap_data(r.json())
            if isinstance(interfaces, list):
                wanish = [
                    x
                    for x in interfaces
                    if isinstance(x, dict)
                    and (
                        "WAN" in str(x.get("ifname", "")).upper()
                        or "Cellular" in str(x.get("ifname", ""))
                        or "GigabitEthernet" in str(x.get("ifname", ""))
                    )
                ]
                out["wan_by_device"][k] = {"interfaces_filtered": wanish, "all_count": len(interfaces)}
            else:
                out["wan_by_device"][k] = {"interfaces": interfaces}

    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
