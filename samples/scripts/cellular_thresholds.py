#!/usr/bin/env python3
"""
Cellular metrics + partner-defined signal bands (client-side thresholds).

See docs/recipes/cellular-signal-thresholds.md
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

from sdwan_recipes.client import ManagerClient
from sdwan_recipes.config import Settings
from sdwan_recipes.util import device_rows, unwrap_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("cellular_thresholds")


def _key(row: dict) -> str | None:
    return row.get("system-ip") or row.get("systemIp") or row.get("deviceId")


def _band_rsrp(value: float | None) -> str:
    """Example partner bands on RSRP (dBm) — tune for your RF engineering policy."""
    if value is None:
        return "unknown"
    if value >= -80:
        return "excellent"
    if value >= -90:
        return "good"
    if value >= -100:
        return "fair"
    return "poor"


def _extract_rsrp(iface: dict) -> float | None:
    for k in ("rsrp", "RSRP", "cellular-rsrp", "signal-strength"):
        v = iface.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                continue
    return None


def _interface_dicts(payload: Any) -> list[dict]:
    data = unwrap_data(payload)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _iface_label(iface: dict) -> str:
    parts = [
        iface.get("ifname"),
        iface.get("if-name"),
        iface.get("vpn-ifname"),
        iface.get("vpn-if-name"),
        iface.get("interfaceName"),
    ]
    return " ".join(str(p) for p in parts if p)


def _is_cellular_like(iface: dict) -> bool:
    """Heuristic: inventory shows a cellular-style interface (name or type)."""
    label = _iface_label(iface).lower()
    if "cellular" in label:
        return True
    itype = str(
        iface.get("interface-type") or iface.get("interface_type") or iface.get("type") or ""
    ).lower()
    if "cellular" in itype or "lte" in itype:
        return True
    return False


def main() -> int:
    p = argparse.ArgumentParser(description="Cellular-like interfaces + custom bands")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args()

    settings = Settings.load()
    out: dict = {"devices": []}

    cellular_paths = (
        "/dataservice/device/cellular",
        "/dataservice/cellular/devices",
    )

    with ManagerClient(settings) as client:
        client.login()
        rows = device_rows(client.dataservice_json("/dataservice/device"))[: args.limit]

        for row in rows:
            k = _key(row)
            if not k:
                continue
            entry: dict = {"deviceId": k, "host-name": row.get("host-name"), "cellular": []}

            r_if = client.request("GET", "/dataservice/device/interface", params={"deviceId": k})
            ifaces = _interface_dicts(r_if.json()) if r_if.is_success else []
            if not r_if.is_success:
                log.warning(
                    "GET /dataservice/device/interface HTTP %s for deviceId=%s",
                    r_if.status_code,
                    k,
                )

            has_cellular_like = any(_is_cellular_like(i) for i in ifaces)

            if has_cellular_like:
                for cp in cellular_paths:
                    r = client.request("GET", cp, params={"deviceId": k})
                    if r.is_success:
                        try:
                            entry["cellular"].append({"path": cp, "data": unwrap_data(r.json())})
                        except json.JSONDecodeError:
                            entry["cellular"].append({"path": cp, "raw": r.text[:300]})
            else:
                entry["cellular_api_skipped_reason"] = (
                    "no_cellular_like_interface_in_inventory"
                )
                log.info(
                    "Skipping cellular dataservice paths for %s (no cellular-like interface in inventory)",
                    k,
                )

            for iface in ifaces:
                if not _is_cellular_like(iface):
                    continue
                name = str(iface.get("ifname") or _iface_label(iface) or "")
                rsrp = _extract_rsrp(iface)
                iface_view = {
                    "ifname": name,
                    "rsrp_dbm": rsrp,
                    "partner_band": _band_rsrp(rsrp),
                }
                entry.setdefault("interfaces_cellular", []).append(iface_view)

            out["devices"].append(entry)

    text = json.dumps(out, indent=2)
    if args.output:
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
