#!/usr/bin/env python3
"""
EIOLTE statistics: per-interface RSSI history as a one-line Braille sparkline per device.

Only queries devices that have a cellular-like interface in inventory (see
_is_cellular_like). Others are skipped without error.

Uses POST /dataservice/statistics/eiolte/uniqueAggregation — query fields per
DevNet include ``vdevice_name`` and ``entry_time`` (default ``SDWAN_STATS_DEVICE_FIELD``).

See docs/recipes/cellular-signal-thresholds.md

Example (from samples/ with .env)::

    python scripts/cellular_signal_history.py --device-id 10.100.5.111 --hours 48
    python scripts/cellular_signal_history.py --device-id 10.100.5.111 --fresh-jwt-login --hours 48
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dotenv import load_dotenv

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings
from sdwan_recipes.signal_terminal_plot import signal_strength_terminal_plot
from sdwan_recipes.util import device_rows, unwrap_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("cellular_signal_history")

EIOLTE_AGG_PATH = "/dataservice/statistics/eiolte/uniqueAggregation"

_STATS_DEVICE_FIELD = os.getenv("SDWAN_STATS_DEVICE_FIELD", "vdevice_name").strip()


def _key(row: dict) -> str | None:
    return row.get("system-ip") or row.get("systemIp") or row.get("deviceId")


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
    """Heuristic for WAN modem / LTE / eSIM style interfaces (names vary by platform)."""
    label = _iface_label(iface).lower()
    for token in ("cellular", "lte", "5g", "wwan", "modem", "esim"):
        if token in label:
            return True
    itype = str(
        iface.get("interface-type") or iface.get("interface_type") or iface.get("type") or ""
    ).lower()
    if "cellular" in itype or "lte" in itype or "wwan" in itype:
        return True
    return False


def _row_matches_ip(row: dict, want_ip: str) -> bool:
    w = want_ip.strip()
    if not w:
        return False
    for k in (
        "system-ip",
        "systemIp",
        "deviceId",
        "local-system-ip",
        "localSystemIp",
        "device-ip",
        "deviceIP",
    ):
        v = row.get(k)
        if v is not None and str(v).strip() == w:
            return True
    return False


def _device_has_cellular(client: ManagerClient, system_ip: str) -> bool:
    r = client.request("GET", "/dataservice/device/interface", params={"deviceId": system_ip})
    if not r.is_success:
        return False
    ifaces = _interface_dicts(r.json())
    return any(_is_cellular_like(i) for i in ifaces)


# Dimension fields from DevNet "unique aggregation request" (POST …/eiolte/uniqueAggregation).
_EIOLTE_UNIQUE_AGG_FIELD_DIMS: tuple[dict[str, Any], ...] = (
    {"property": "rsrp", "sequence": 1},
    {"property": "rsrq", "sequence": 2},
    {"property": "mcc", "sequence": 3},
    {"property": "mnc", "sequence": 4},
    {"property": "carrier", "sequence": 5},
    {"property": "rat", "sequence": 6},
    {"property": "ps_domain", "sequence": 7},
    {"property": "emm_state", "sequence": 8},
    {"property": "lteband", "sequence": 9},
    {"property": "ltebw", "sequence": 10},
    {"property": "lteca", "sequence": 11},
    {"property": "active_sim", "sequence": 12},
    {"property": "bandclass", "sequence": 13},
    {"property": "slot", "sequence": 14},
    {"property": "pci", "sequence": 15},
)


def _build_unique_aggregation_body(
    system_ip: str,
    hours: int,
    size: int,
    *,
    histogram_minutes: int = 30,
    ps_domain_values: list[str] | None,
) -> dict[str, Any]:
    """Body aligned with working Manager payloads (entry_time, vdevice_name, rssi, ps_domain, aggregation)."""
    rules: list[dict[str, Any]] = [
        {
            "value": [str(hours)],
            "field": "entry_time",
            "type": "date",
            "operator": "last_n_hours",
        },
        {
            "value": [system_ip],
            "field": _STATS_DEVICE_FIELD,
            "type": "string",
            "operator": "in",
        },
        {
            "value": ["0"],
            "field": "rssi",
            "type": "string",
            "operator": "not_equal",
        },
    ]
    if ps_domain_values:
        rules.append(
            {
                "value": ps_domain_values,
                "field": "ps_domain",
                "type": "string",
                "operator": "in",
            }
        )
    return {
        "query": {"condition": "AND", "rules": rules},
        "aggregation": {
            "field": [dict(x) for x in _EIOLTE_UNIQUE_AGG_FIELD_DIMS],
            # Manager expects avg on rssi for this path; sparkline uses RSSI from each row.
            "metrics": [{"property": "rssi", "type": "avg"}],
            "histogram": {
                "property": "entry_time",
                "type": "minute",
                "interval": max(1, int(histogram_minutes)),
                "order": "asc",
            },
        },
        "size": size,
    }


def _rows_from_eiolte_response(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def _metric_series(rows: list[dict[str, Any]], metric: str) -> list[tuple[int, float]]:
    """Pairs (entry_time_ms, value) sorted by time."""
    pairs: list[tuple[int, float]] = []
    for row in rows:
        et = row.get("entry_time")
        if not isinstance(et, (int, float)):
            continue
        v = row.get(metric)
        if isinstance(v, bool):
            continue
        if isinstance(v, int) or isinstance(v, float):
            pairs.append((int(et), float(v)))
        elif isinstance(v, str):
            try:
                pairs.append((int(et), float(v)))
            except ValueError:
                continue
    pairs.sort(key=lambda x: x[0])
    return pairs


def _iface_stat_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """EIOLTE row dimensions that identify a modem / SIM slice (best-effort)."""
    return (row.get("slot"), row.get("active_sim"))


def _group_stat_rows_by_interface(
    rows: list[dict[str, Any]],
) -> list[tuple[tuple[Any, ...], list[dict[str, Any]]]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        k = _iface_stat_key(row)
        buckets.setdefault(k, []).append(row)
    return sorted(buckets.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1])))


def _format_iface_key(key: tuple[Any, ...]) -> str:
    slot, sim = (key[0], key[1]) if len(key) >= 2 else (None, None)
    if slot is None and sim is None:
        return "cellular"
    parts: list[str] = []
    if slot is not None:
        parts.append(f"slot {slot}")
    if sim is not None:
        parts.append(f"SIM {sim}")
    return " · ".join(parts) if parts else "cellular"


def _dedupe_time_last(pairs: list[tuple[int, float]]) -> list[tuple[int, float]]:
    """One RSSI sample per ``entry_time`` (last wins if duplicates)."""
    best: dict[int, float] = {}
    for t, v in pairs:
        best[t] = v
    return sorted(best.items(), key=lambda x: x[0])


def _truncate(s: str, max_len: int) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Print per-device, per-interface RSSI as Braille sparklines (EIOLTE uniqueAggregation)"
    )
    p.add_argument("--hours", type=int, default=48, help="Lookback for entry_time last_n_hours")
    p.add_argument("--limit", type=int, default=40, help="Max devices: unfiltered scan cap; with --hostname-contains, max matches after cellular gate")
    p.add_argument("--width", type=int, default=56, help="Braille sparkline width (characters)")
    p.add_argument("--size", type=int, default=10000, help="POST body size cap (statistics)")
    p.add_argument(
        "--ps-domain",
        default="Attached",
        help="Comma-separated ps_domain values for the 'in' query rule (default: Attached)",
    )
    p.add_argument(
        "--omit-ps-domain-filter",
        action="store_true",
        help="Omit the ps_domain rule (use if your modem uses other ps_domain strings)",
    )
    p.add_argument(
        "--device-id",
        type=str,
        default="",
        help="Only this system IP (e.g. 10.100.5.111); skip inventory scan for others",
    )
    p.add_argument(
        "--hostname-contains",
        type=str,
        default="",
        help="Only devices whose host-name contains this substring (case-insensitive)",
    )
    p.add_argument(
        "--scan-limit",
        type=int,
        default=5000,
        help="Max inventory rows to scan when filtering by hostname (default 5000)",
    )
    p.add_argument(
        "--assume-cellular",
        action="store_true",
        help="Skip GET /device/interface cellular heuristic (use when naming differs but EIOLTE stats exist)",
    )
    p.add_argument(
        "--fresh-jwt-login",
        action="store_true",
        help="Ignore SDWAN_JWT_TOKEN in .env and call POST /jwt/login (pairs Bearer + csrf for statistics POSTs)",
    )
    p.add_argument("--insecure", action="store_true", help="Disable TLS verification (lab only)")
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors (also respects NO_COLOR in the environment)",
    )
    args = p.parse_args()

    load_dotenv(_REPO / ".env")
    load_dotenv(_REPO / ".env.local", override=False)

    base = Settings.load()
    settings = replace(base, verify_ssl=False if args.insecure else base.verify_ssl)
    if args.fresh_jwt_login:
        settings = replace(
            settings,
            jwt_token=None,
            jwt_csrf=None,
            jwt_refresh=None,
        )
        log.info("Using POST /jwt/login (SDWAN_JWT_TOKEN ignored for this run)")

    want_ip = args.device_id.strip()
    want_host = args.hostname_contains.strip().lower()

    with ManagerClient(settings) as client:
        client.login()
        all_rows = device_rows(client.dataservice_json("/dataservice/device"))

        if want_ip:
            rows = [r for r in all_rows if _row_matches_ip(r, want_ip)]
            if not rows:
                log.warning(
                    "No inventory row matches --device-id %s (checked system-ip, deviceId, local-system-ip, …)",
                    want_ip,
                )
                return 1
        elif want_host:
            cap = max(1, args.scan_limit)
            rows = [
                r
                for r in all_rows[:cap]
                if isinstance(r, dict)
                and want_host in str(r.get("host-name") or r.get("hostname") or "").lower()
            ]
            if args.limit > 0:
                rows = rows[: args.limit]
        else:
            rows = all_rows[: args.limit]

        candidates: list[tuple[str, str]] = []
        for row in rows:
            ip = _key(row)
            if not ip:
                continue
            host = str(row.get("host-name") or row.get("hostname") or "")
            if args.assume_cellular:
                has_cell = True
            else:
                has_cell = _device_has_cellular(client, ip)
            if not has_cell:
                continue
            candidates.append((ip, host))

        if not candidates:
            log.warning(
                "No devices matched (cellular interface + filters). "
                "Try --device-id <system-ip> or widen --limit; check SDWAN_STATS_DEVICE_FIELD if POST fails."
            )
            return 1

        if args.omit_ps_domain_filter:
            ps_domain_values: list[str] | None = None
        else:
            parts = [s.strip() for s in args.ps_domain.split(",") if s.strip()]
            ps_domain_values = parts if parts else ["Attached"]

        for system_ip, hostname in candidates:
            body = _build_unique_aggregation_body(
                system_ip,
                args.hours,
                args.size,
                ps_domain_values=ps_domain_values,
            )
            try:
                payload = client.dataservice_post_json(EIOLTE_AGG_PATH, json_body=body)
            except SdwanApiError as exc:
                log.error("%s | %s  ->  %s", hostname, system_ip, exc)
                if "SessionTokenFilter" in str(exc):
                    log.info(
                        "Hint: use --fresh-jwt-login with SDWAN_USERNAME/PASSWORD, or set SDWAN_JWT_CSRF "
                        "from the same /jwt/login response as SDWAN_JWT_TOKEN"
                    )
                continue

            stat_rows = _rows_from_eiolte_response(payload)
            label = _truncate(hostname or "(no hostname)", 36)
            print(f"{label:38} {system_ip:16}")

            groups = _group_stat_rows_by_interface(stat_rows)
            if not groups:
                print("  (no EIOLTE data rows)")
                continue

            for iface_key, iface_rows in groups:
                pairs = _dedupe_time_last(_metric_series(iface_rows, "rssi"))
                values = [v for _, v in pairs]
                iface_label = _format_iface_key(iface_key)
                if values:
                    vmin, vmax = min(values), max(values)
                    meta = f"RSSI {vmin:.0f}..{vmax:.0f} dBm n={len(values)}"
                else:
                    meta = "RSSI (no samples in window)"

                plot = signal_strength_terminal_plot(
                    values,
                    width=args.width,
                    scale="rssi",
                    use_color=False if args.no_color else None,
                )
                print(f"  {iface_label:22}  {meta:30}  {plot}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
