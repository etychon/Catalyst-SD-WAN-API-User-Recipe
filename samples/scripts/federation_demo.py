#!/usr/bin/env python3
"""
Merge device inventory from multiple Manager base URLs (multi-cluster sketch).

Set SDWAN_FEDERATION as JSON array of objects:
[{"cluster_id":"A","base_url":"https://m1:8443"},{"cluster_id":"B","base_url":"https://m2:8443"}]

Credentials default to global SDWAN_USERNAME / SDWAN_PASSWORD unless overridden per cluster.
Optional per-cluster keys jwt_token, jwt_csrf, jwt_refresh override SDWAN_JWT_* from the environment.

See docs/02-rate-limits-scale.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import replace
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdwan_recipes.client import ManagerClient
from sdwan_recipes.config import Settings
from sdwan_recipes.util import device_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("federation_demo")


def main() -> int:
    p = argparse.ArgumentParser(description="Multi-Manager inventory merge demo")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    raw = os.getenv("SDWAN_FEDERATION", "").strip()
    if not raw:
        log.error("Set SDWAN_FEDERATION to a JSON list of {cluster_id, base_url} objects")
        return 2

    clusters = json.loads(raw)
    base_settings = Settings.load()
    merged = []

    for c in clusters:
        cid = c["cluster_id"]
        url = c["base_url"].rstrip("/")
        user = c.get("username", base_settings.username)
        password = c.get("password", base_settings.password)
        jwt_t = (c.get("jwt_token") or "").strip() or base_settings.jwt_token
        jwt_csrf = (c.get("jwt_csrf") or "").strip() or base_settings.jwt_csrf
        jwt_ref = (c.get("jwt_refresh") or "").strip() or base_settings.jwt_refresh
        s = replace(
            base_settings,
            base_url=url,
            username=user,
            password=password,
            jwt_token=jwt_t,
            jwt_csrf=jwt_csrf,
            jwt_refresh=jwt_ref,
        )
        with ManagerClient(s) as client:
            client.login()
            rows = device_rows(client.dataservice_json("/dataservice/device"))
        for r in rows:
            r = dict(r)
            r["cluster_id"] = cid
            merged.append(r)

    text = json.dumps({"devices": merged, "count": len(merged)}, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
