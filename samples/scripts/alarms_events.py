#!/usr/bin/env python3
"""
Alarms and events pull sample (multi-step: authenticate, list alarms, list recent events).

See docs/recipes/syslog-alarms-audit-rbac.md
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("alarms_events")


def _try_json(client: ManagerClient, path: str, params: dict | None = None):
    r = client.request("GET", path, params=params)
    out = {"http_status": r.status_code, "path": path}
    if not r.is_success:
        out["body_preview"] = r.text[:400]
        return out
    try:
        out["json"] = r.json()
    except json.JSONDecodeError:
        out["raw_preview"] = r.text[:400]
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Alarms and events REST sample")
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    result = {}

    alarm_candidates = (
        "/dataservice/alarms",
        "/dataservice/alarms/count",
    )
    event_candidates = (
        "/dataservice/event",
        "/dataservice/message/events",
    )

    with ManagerClient(settings) as client:
        client.login()
        result["alarms"] = [_try_json(client, path) for path in alarm_candidates]
        result["events"] = [_try_json(client, path) for path in event_candidates]

    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
