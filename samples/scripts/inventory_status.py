#!/usr/bin/env python3
"""
Inventory operational status: devices plus configuration / sync style endpoints.

See docs/recipes/inventory-status-config-groups.md
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
log = logging.getLogger("inventory_status")


def _try(client: ManagerClient, path: str, params: dict | None = None):
    r = client.request("GET", path, params=params)
    row = {"path": path, "status": r.status_code}
    if r.is_success:
        try:
            row["json"] = r.json()
        except json.JSONDecodeError:
            row["preview"] = r.text[:400]
    else:
        row["preview"] = r.text[:400]
    return row


def main() -> int:
    p = argparse.ArgumentParser(description="Device inventory + config status sample")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    bundle: dict = {"devices": [], "extra": []}

    status_paths = (
        "/dataservice/device/config/status",
        "/dataservice/template/device/config/attached",
        "/dataservice/device/config/group",
    )

    with ManagerClient(settings) as client:
        client.login()
        bundle["devices"] = device_rows(client.dataservice_json("/dataservice/device"))
        for path in status_paths:
            bundle["extra"].append(_try(client, path))

    text = json.dumps(bundle, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
