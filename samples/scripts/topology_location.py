#!/usr/bin/env python3
"""
Topology and location: sites (if available) + device rows with site-id / GPS fields.

See docs/recipes/topology-location-gps.md
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
log = logging.getLogger("topology_location")


def main() -> int:
    p = argparse.ArgumentParser(description="Site and device location fields sample")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    out: dict = {"sites": None, "devices": []}

    site_paths = ("/dataservice/site", "/dataservice/sites")

    with ManagerClient(settings) as client:
        client.login()
        for sp in site_paths:
            r = client.request("GET", sp)
            if r.is_success:
                try:
                    out["sites"] = {"path": sp, "data": unwrap_data(r.json())}
                    break
                except json.JSONDecodeError:
                    out["sites"] = {"path": sp, "raw": r.text[:400]}
        out["devices"] = device_rows(client.dataservice_json("/dataservice/device"))

    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
