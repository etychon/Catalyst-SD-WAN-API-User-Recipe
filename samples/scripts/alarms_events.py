#!/usr/bin/env python3
"""
Alarms, events, and audit log sample (field discovery + filtered POST queries).

See docs/recipes/syslog-alarms-audit-rbac.md
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

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings
from sdwan_recipes.governance_query import (
    build_query,
    count_from_response,
    discover_all_fields,
    fetch_query_fields,
    records_from_response,
    rule_equal,
    rule_in,
    rule_last_n_hours,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("alarms_events")

LEGACY_GET_PATHS = (
    "/dataservice/event",
    "/dataservice/message/events",
)


def _try_get_json(client: ManagerClient, path: str, params: dict | None = None) -> dict[str, Any]:
    r = client.request("GET", path, params=params)
    out: dict[str, Any] = {"http_status": r.status_code, "path": path}
    if not r.is_success:
        out["body_preview"] = r.text[:400]
        return out
    try:
        out["json"] = r.json()
    except json.JSONDecodeError:
        out["raw_preview"] = r.text[:400]
    return out


def _post_query(client: ManagerClient, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        body = client.dataservice_post_json(path, json_body=payload)
        records = records_from_response(body)
        return {
            "path": path,
            "http_status": 200,
            "count": count_from_response(body),
            "records": records[:20],
            "truncated": len(records) > 20,
        }
    except SdwanApiError as exc:
        return {"path": path, "error": str(exc)}


def _query_events(client: ManagerClient, payload: dict[str, Any]) -> dict[str, Any]:
    result = _post_query(client, "/dataservice/events", payload)
    if "error" in result and "404" in result["error"]:
        log.warning("POST /dataservice/events returned 404; trying GET /dataservice/event (legacy)")
        legacy = _try_get_json(client, "/dataservice/event")
        if legacy.get("http_status") == 200:
            body = legacy.get("json")
            records = records_from_response(body) if body else []
            return {
                "path": "/dataservice/event",
                "http_status": 200,
                "count": len(records),
                "records": records[:20],
                "truncated": len(records) > 20,
                "degraded": "legacy_get_no_query_filters",
            }
    return result


def _build_alarm_rules(args: argparse.Namespace) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = [rule_last_n_hours(args.hours)]
    if args.severity:
        rules.append(rule_in("severity", args.severity))
    if args.system_ip:
        rules.append(rule_in("system_ip", args.system_ip))
    if args.site_id:
        rules.append(rule_in("site_id", args.site_id))
    if args.device_name:
        rules.append(rule_in("vdevice_name", args.device_name))
    if args.alarm_type:
        rules.append(rule_in("rule_name_display", args.alarm_type))
    if args.active is not None:
        rules.append(rule_equal("active", "true" if args.active else "false", type="boolean"))
    return rules


def _build_event_rules(args: argparse.Namespace) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = [rule_last_n_hours(args.hours)]
    if args.severity:
        rules.append(rule_in("severity_level", [s.lower() for s in args.severity]))
    if args.event_component:
        rules.append(rule_in("component", args.event_component))
    if args.event_name:
        rules.append(rule_in("eventname", args.event_name))
    return rules


def _build_audit_rules(args: argparse.Namespace) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = [rule_last_n_hours(args.hours)]
    if args.severity:
        rules.append(rule_in("severity_level", [s.lower() for s in args.severity]))
    if args.audit_user:
        rules.append(rule_in("loguser", args.audit_user))
    if args.audit_feature:
        rules.append(rule_in("logfeature", args.audit_feature))
    if args.audit_module:
        rules.append(rule_in("logmodule", args.audit_module))
    if args.system_ip:
        rules.append(rule_in("logdeviceid", args.system_ip))
    return rules


def _run_queries(client: ManagerClient, args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {"window_hours": args.hours}
    resources = {"alarms", "events", "audit"} if args.resource == "all" else {args.resource}

    if "alarms" in resources:
        payload = build_query(_build_alarm_rules(args), size=args.size)
        result["alarms"] = _post_query(client, "/dataservice/alarms", payload)
        if args.include_count:
            result["alarms_count"] = _post_query(
                client, "/dataservice/alarms/count", {"query": payload["query"]}
            )

    if "events" in resources:
        payload = build_query(_build_event_rules(args), size=args.size)
        result["events"] = _query_events(client, payload)

    if "audit" in resources:
        payload = build_query(_build_audit_rules(args), size=args.size)
        result["auditlog"] = _post_query(client, "/dataservice/auditlog", payload)

    if args.probe_legacy:
        result["legacy_probes"] = [_try_get_json(client, path) for path in LEGACY_GET_PATHS]

    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Alarms, events, and audit REST sample")
    p.add_argument("--output", type=Path, default=None, help="Write JSON output to file")
    p.add_argument(
        "--discover-fields",
        action="store_true",
        help="GET field metadata for alarms, events, and audit (no POST queries)",
    )
    p.add_argument(
        "--resource",
        choices=["all", "alarms", "events", "audit"],
        default="all",
        help="Which resource families to query (default: all)",
    )
    p.add_argument("--hours", type=int, default=24, help="Lookback window (entry_time last_n_hours)")
    p.add_argument("--size", type=int, default=10000, help="Max records per POST query")
    p.add_argument("--severity", action="append", default=[], help="Severity filter (repeatable)")
    p.add_argument("--system-ip", action="append", default=[], dest="system_ip")
    p.add_argument("--site-id", action="append", default=[], dest="site_id")
    p.add_argument("--device-name", action="append", default=[], dest="device_name")
    p.add_argument("--alarm-type", action="append", default=[], dest="alarm_type")
    p.add_argument(
        "--active",
        action="store_true",
        default=None,
        help="Alarms only: filter active=true",
    )
    p.add_argument(
        "--cleared",
        action="store_true",
        help="Alarms only: filter active=false",
    )
    p.add_argument("--event-component", action="append", default=[], dest="event_component")
    p.add_argument("--event-name", action="append", default=[], dest="event_name")
    p.add_argument("--audit-user", action="append", default=[], dest="audit_user")
    p.add_argument("--audit-feature", action="append", default=[], dest="audit_feature")
    p.add_argument("--audit-module", action="append", default=[], dest="audit_module")
    p.add_argument(
        "--include-count",
        action="store_true",
        help="Also POST /alarms/count with the same alarm query",
    )
    p.add_argument(
        "--probe-legacy",
        action="store_true",
        help="Optional GET probes for legacy /event and /message/events paths",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.cleared:
        args.active = False

    settings = Settings.load()
    result: dict[str, Any] = {}

    with ManagerClient(settings) as client:
        client.login()
        if args.discover_fields:
            if args.resource == "all":
                result = discover_all_fields(client)
            else:
                result = {args.resource: fetch_query_fields(client, args.resource)}
        else:
            result = _run_queries(client, args)

    text = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
