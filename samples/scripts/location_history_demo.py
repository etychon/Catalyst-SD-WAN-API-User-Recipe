#!/usr/bin/env python3
"""
Demo: append current device location-ish fields to a local SQLite file.

NOT for 20k-scale production — illustrates ETL pattern only.

See docs/recipes/location-history-retention.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdwan_recipes.client import ManagerClient
from sdwan_recipes.config import Settings
from sdwan_recipes.util import device_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("location_history_demo")

DDL = """
CREATE TABLE IF NOT EXISTS device_location_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  device_id TEXT,
  host_name TEXT,
  site_id TEXT,
  latitude REAL,
  longitude REAL,
  payload_json TEXT
);
"""


def _pick_float(row: dict, *keys: str) -> float | None:
    for k in keys:
        v = row.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def main() -> int:
    p = argparse.ArgumentParser(description="SQLite demo for location snapshots")
    p.add_argument("--db", type=Path, default=Path("location_history_demo.sqlite3"))
    args = p.parse_args()

    settings = Settings.load()
    now = datetime.now(timezone.utc).isoformat()

    with ManagerClient(settings) as client:
        client.login()
        rows = device_rows(client.dataservice_json("/dataservice/device"))

    conn = sqlite3.connect(args.db)
    try:
        conn.execute(DDL)
        inserted = 0
        for row in rows:
            did = row.get("uuid") or row.get("deviceId") or row.get("system-ip")
            lat = _pick_float(row, "latitude", "deviceLatitude")
            lon = _pick_float(row, "longitude", "deviceLongitude")
            conn.execute(
                """
                INSERT INTO device_location_snapshots
                (ts, device_id, host_name, site_id, latitude, longitude, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    str(did) if did else None,
                    row.get("host-name"),
                    str(row.get("site-id")) if row.get("site-id") is not None else None,
                    lat,
                    lon,
                    json.dumps(row)[:16000],
                ),
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()

    log.info("Inserted %s rows into %s", inserted, args.db)
    print(json.dumps({"database": str(args.db.resolve()), "inserted": inserted, "ts": now}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
