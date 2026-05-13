#!/usr/bin/env python3
"""
Multi-endpoint dashboard snapshot (devices, health merge, per-device drilldown, alarms, audit).

Ported from the incorporated starter pack; uses this repo's httpx-based ManagerClient.

See docs/dashboard-architecture.md and docs/api-selection-guide.md
"""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("collect_dashboard_snapshot")


def _ensure_password() -> None:
    if os.getenv("SDWAN_JWT_TOKEN", "").strip():
        return
    if os.getenv("SDWAN_PASSWORD"):
        return
    if os.getenv("SDWAN_PASSWORD_PROMPT") == "1" or sys.stdin.isatty():
        os.environ["SDWAN_PASSWORD"] = getpass.getpass("SD-WAN Manager password: ")
    else:
        raise SystemExit(
            "Set SDWAN_PASSWORD, SDWAN_PASSWORD_PROMPT=1, or SDWAN_JWT_TOKEN for interactive/bearer auth"
        )


def collect_snapshot(
    client: ManagerClient, hours: int, include_cellular: bool
) -> dict[str, Any]:
    collected_at = datetime.now(UTC).isoformat()
    # Fetch inventory first so a 403 on health can be distinguished from total auth failure.
    r_inv = client.request("GET", "/dataservice/device")
    r_inv.raise_for_status()
    inventory = r_inv.json()

    devices_health: Any
    try:
        devices_health = client.dataservice_json("/dataservice/health/devices")
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == httpx.codes.FORBIDDEN:
            log.warning(
                "GET /dataservice/health/devices returned 403 (likely RBAC or token scope). "
                "Continuing with inventory-only merge; health-specific fields will be empty."
            )
            devices_health = {"data": []}
        else:
            raise

    alarms_degraded = False
    try:
        alarms = query_last_n_hours(client, "/dataservice/alarms", hours)
    except SdwanApiError as exc:
        msg = str(exc)
        if "403" in msg or "Forbidden" in msg:
            alarms_degraded = True
            log.warning(
                "POST /dataservice/alarms returned 403 (e.g. RBAC or SessionTokenFilter when "
                "Bearer was not paired with the same /jwt/login session). Skipping alarms export."
            )
            alarms = {"data": []}
        else:
            raise

    audit_degraded = False
    try:
        auditlog = query_last_n_hours(client, "/dataservice/auditlog", hours)
    except SdwanApiError as exc:
        msg = str(exc)
        if "403" in msg or "Forbidden" in msg:
            audit_degraded = True
            log.warning(
                "POST /dataservice/auditlog returned 403; skipping audit export."
            )
            auditlog = {"data": []}
        else:
            raise

    devices = normalize_devices(devices_health, inventory)
    drilldowns: list[dict[str, Any]] = []
    for device in devices:
        if device.get("reachability") != "reachable":
            continue
        system_ip = device.get("system_ip")
        if not system_ip:
            continue
        drilldowns.append(collect_device_drilldown(client, str(system_ip), include_cellular))

    return {
        "collected_at": collected_at,
        "window_hours": hours,
        "summary": {
            "device_count": len(devices),
            "reachable_count": sum(1 for item in devices if item.get("reachability") == "reachable"),
            "alarm_count": count_records(alarms),
            "audit_count": count_records(auditlog),
            "alarms_export_degraded": alarms_degraded,
            "audit_export_degraded": audit_degraded,
        },
        "devices": devices,
        "device_drilldowns": drilldowns,
        "alarms": records_from_response(alarms),
        "auditlog": records_from_response(auditlog),
    }


def collect_device_drilldown(
    client: ManagerClient, system_ip: str, include_cellular: bool
) -> dict[str, Any]:
    result: dict[str, Any] = {"system_ip": system_ip}
    for name, path in {
        "bfd_summary": "/dataservice/device/bfd/summary",
        "bfd_sessions": "/dataservice/device/bfd/sessions",
        "interfaces": "/dataservice/device/interface",
    }.items():
        try:
            result[name] = records_from_response(
                client.dataservice_json(path, params={"deviceId": system_ip})
            )
        except (SdwanApiError, httpx.HTTPError, json.JSONDecodeError) as exc:
            result[name] = {"error": str(exc)}

    if include_cellular:
        for name, path in {
            "cellular_status": "/dataservice/device/cellular/status",
            "cellular_radio": "/dataservice/device/cellularEiolte/radio",
        }.items():
            try:
                result[name] = records_from_response(
                    client.dataservice_json(path, params={"deviceId": system_ip})
                )
            except (SdwanApiError, httpx.HTTPError, json.JSONDecodeError) as exc:
                result[name] = {"error": str(exc)}

    return result


def query_last_n_hours(client: ManagerClient, path: str, hours: int) -> dict[str, Any]:
    payload = {
        "query": {
            "condition": "AND",
            "rules": [
                {
                    "value": [str(hours)],
                    "field": "entry_time",
                    "type": "date",
                    "operator": "last_n_hours",
                }
            ],
        },
        "size": 10000,
    }
    return client.dataservice_post_json(path, json_body=payload)


def normalize_devices(health: Any, inventory: Any) -> list[dict[str, Any]]:
    by_system_ip: dict[str, dict[str, Any]] = {}
    for item in records_from_response(inventory):
        system_ip = item.get("system-ip") or item.get("system_ip") or item.get("deviceIP")
        if not system_ip:
            continue
        by_system_ip[str(system_ip)] = {
            "system_ip": str(system_ip),
            "uuid": item.get("uuid") or item.get("deviceId"),
            "hostname": item.get("host-name") or item.get("name"),
            "site_id": item.get("site-id") or item.get("site_id"),
            "device_model": item.get("device-model") or item.get("device_model"),
            "version": item.get("version"),
            "reachability": item.get("reachability"),
            "status": item.get("status") or item.get("state"),
            "latitude": parse_float(item.get("latitude")),
            "longitude": parse_float(item.get("longitude")),
            "has_geo_data": item.get("isDeviceGeoData") or item.get("has_geo_data"),
        }

    for item in records_from_response(health):
        system_ip = item.get("system_ip") or item.get("system-ip")
        if not system_ip:
            continue
        system_ip = str(system_ip)
        device = by_system_ip.setdefault(system_ip, {"system_ip": system_ip})
        device.update(
            {
                "hostname": device.get("hostname") or item.get("name"),
                "site_id": device.get("site_id") or item.get("site_id"),
                "reachability": item.get("reachability") or device.get("reachability"),
                "health": item.get("health"),
                "cpu_load": item.get("cpu_load"),
                "memory_utilization": item.get("memory_utilization"),
                "control_connections_up": item.get("control_connections_up"),
                "control_connections": item.get("control_connections"),
                "bfd_sessions_up": item.get("bfd_sessions_up"),
                "bfd_sessions": item.get("bfd_sessions"),
                "omp_peers_up": item.get("omp_peers_up"),
                "omp_peers": item.get("omp_peers"),
                "latitude": device.get("latitude") or parse_float(item.get("latitude")),
                "longitude": device.get("longitude") or parse_float(item.get("longitude")),
                "has_geo_data": device.get("has_geo_data") or item.get("has_geo_data"),
            }
        )

    return sorted(by_system_ip.values(), key=lambda item: str(item.get("system_ip")))


def records_from_response(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [x for x in response if isinstance(x, dict)]
    if not isinstance(response, dict):
        return []
    data = response.get("data")
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    devices = response.get("devices")
    if isinstance(devices, list):
        return [x for x in devices if isinstance(x, dict)]
    if isinstance(response, list):
        return [x for x in response if isinstance(x, dict)]
    return []


def count_records(response: Any) -> int:
    records = records_from_response(response)
    if records:
        return len(records)
    count = response.get("count")
    return int(count) if isinstance(count, int) else 0


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Collect a dashboard-oriented SD-WAN Manager snapshot")
    p.add_argument("--hours", type=int, default=24, help="Alarm/audit lookback window")
    p.add_argument("--include-cellular", action="store_true", help="Collect cellular status and radio details")
    p.add_argument("--insecure", action="store_true", help="Disable TLS verification (lab only)")
    p.add_argument(
        "--auth-mode",
        choices=["auto", "jwt", "session"],
        default=None,
        help="Override SDWAN_AUTH_MODE for this run",
    )
    p.add_argument("--output", type=Path, default=Path("output/dashboard_snapshot.json"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    # Load .env before password checks (Settings.load() also calls load_dotenv).
    from dotenv import load_dotenv

    load_dotenv()
    _ensure_password()
    base = Settings.load()
    settings = replace(
        base,
        verify_ssl=False if args.insecure else base.verify_ssl,
        auth_mode=args.auth_mode or base.auth_mode,
    )

    try:
        with ManagerClient(settings) as client:
            client.login()
            snapshot = collect_snapshot(client, hours=args.hours, include_cellular=args.include_cellular)
    except (SdwanApiError, httpx.HTTPError, ValueError) as exc:
        log.error("%s", exc)
        return 2

    write_json(args.output, snapshot)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
