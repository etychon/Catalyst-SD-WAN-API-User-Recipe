#!/usr/bin/env python3
"""
Hosted Edge Services (IOx) monitoring snapshot — read-only.

Uses POST /dataservice/statistics/apphosting/page (and optional interface family).
Provision/deploy is documented in config-group recipes; start/stop is v2 (lab OpenAPI).

See docs/recipes/hosted-edge-services-iox.md

Example::

    python scripts/hosted_edge_services.py --hours 24 --output output/hosted_edge.json
    python scripts/hosted_edge_services.py --device 10.20.1.10 --discover-fields
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings
from sdwan_recipes.hosted_edge import (
    DEFAULT_STATS_DEVICE_FIELD,
    apphosting_doccount_value,
    build_apphosting_page_query,
    discover_apphosting_query_fields,
    join_apphosting_to_inventory,
    list_custom_apps,
    normalize_apphosting_rows,
    query_apphosting_doccount,
    query_apphosting_page,
    query_apphostinginterface_doccount,
    query_apphostinginterface_page,
    summarize_apphosting_rows,
)
from sdwan_recipes.util import device_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("hosted_edge_services")

_STATS_DEVICE_FIELD = os.getenv("SDWAN_STATS_DEVICE_FIELD", DEFAULT_STATS_DEVICE_FIELD).strip()
_DEVICE_PATH = "/dataservice/device"


def _safe_inventory(client: ManagerClient) -> dict[str, Any]:
    try:
        payload = client.dataservice_json(_DEVICE_PATH)
        return {
            "ok": True,
            "label": "inventory",
            "device_count": len(device_rows(payload)),
            "payload": payload,
        }
    except SdwanApiError as exc:
        log.warning("inventory failed: %s", exc)
        return {"ok": False, "label": "inventory", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — report unexpected errors in JSON
        log.warning("inventory failed: %s", exc)
        return {"ok": False, "label": "inventory", "error": str(exc)}


def _safe_page_call(label: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        payload = fn()
        rows = normalize_apphosting_rows(payload)
        return {
            "ok": True,
            "label": label,
            "row_count": len(rows),
            "summary": summarize_apphosting_rows(rows),
            "payload": payload,
            "rows": rows,
        }
    except SdwanApiError as exc:
        log.warning("%s failed: %s", label, exc)
        return {"ok": False, "label": label, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — report unexpected errors in JSON
        log.warning("%s failed: %s", label, exc)
        return {"ok": False, "label": label, "error": str(exc)}


def _safe_doccount_call(label: str, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        payload = fn()
        return {
            "ok": True,
            "label": label,
            "count": apphosting_doccount_value(payload),
            "payload": payload,
        }
    except SdwanApiError as exc:
        log.warning("%s failed: %s", label, exc)
        return {"ok": False, "label": label, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — report unexpected errors in JSON
        log.warning("%s failed: %s", label, exc)
        return {"ok": False, "label": label, "error": str(exc)}


def _maybe_join_inventory(
    page_result: dict[str, Any],
    inventory_payload: Any | None,
) -> None:
    if not page_result.get("ok"):
        return
    rows = page_result.pop("rows", [])
    if inventory_payload is None:
        page_result["rows"] = rows
        page_result["inventory_join"] = "skipped"
        return
    page_result["rows"] = join_apphosting_to_inventory(rows, inventory_payload)
    page_result["inventory_join"] = "ok"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Hosted Edge Services (IOx) monitoring snapshot (read-only)"
    )
    p.add_argument("--hours", type=int, default=24, help="Lookback for entry_time rule")
    p.add_argument("--device", help="Filter to one device (system-ip / vdevice_name rule value)")
    p.add_argument("--size", type=int, default=10000, help="Max rows in statistics page query")
    p.add_argument(
        "--device-field",
        default=_STATS_DEVICE_FIELD,
        help="Statistics query rule field for --device (default from SDWAN_STATS_DEVICE_FIELD)",
    )
    p.add_argument(
        "--discover-fields",
        action="store_true",
        help="Print apphosting query field metadata and exit",
    )
    p.add_argument(
        "--include-interfaces",
        action="store_true",
        help="Also query statistics/apphostinginterface/page",
    )
    p.add_argument(
        "--include-custom-apps",
        action="store_true",
        help="Also GET /sdavc/customapps (SD-AVC registry, not Hosted Edge monitor)",
    )
    p.add_argument("--tenant", help="Provider-as-tenant: activate VSessionId")
    p.add_argument("--output", type=Path, help="Write JSON report to file")
    args = p.parse_args()

    settings = Settings.load()
    report: dict[str, Any] = {
        "mode": "hosted-edge-services-snapshot",
        "hours": args.hours,
        "device_filter": args.device,
        "device_field": args.device_field,
    }

    with ManagerClient(settings) as client:
        client.login()
        tenant_key = args.tenant or settings.tenant_name or settings.tenant_subdomain
        if tenant_key:
            client.activate_tenant_context(tenant_key)

        if args.discover_fields:
            report["discover_fields"] = discover_apphosting_query_fields(client)
            text = json.dumps(report, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text)
            else:
                print(text)
            return 0

        query_body = build_apphosting_page_query(
            args.hours,
            device_system_ip=args.device,
            device_field=args.device_field,
            size=args.size,
        )
        report["query"] = query_body

        inventory_result = _safe_inventory(client)
        report["inventory"] = {
            k: v for k, v in inventory_result.items() if k != "payload"
        }
        inventory_payload = (
            inventory_result.get("payload") if inventory_result.get("ok") else None
        )

        page_result = _safe_page_call(
            "apphosting_page",
            lambda: query_apphosting_page(client, query_body),
        )
        _maybe_join_inventory(page_result, inventory_payload)
        report["apphosting_page"] = page_result

        report["apphosting_doccount"] = _safe_doccount_call(
            "apphosting_doccount",
            lambda: query_apphosting_doccount(client, query_body),
        )

        if args.include_interfaces:
            iface_page = _safe_page_call(
                "apphostinginterface_page",
                lambda: query_apphostinginterface_page(client, query_body),
            )
            _maybe_join_inventory(iface_page, inventory_payload)
            report["apphostinginterface_page"] = iface_page
            report["apphostinginterface_doccount"] = _safe_doccount_call(
                "apphostinginterface_doccount",
                lambda: query_apphostinginterface_doccount(client, query_body),
            )

        if args.include_custom_apps:
            try:
                report["sdavc_customapps"] = list_custom_apps(client)
            except SdwanApiError as exc:
                report["sdavc_customapps"] = {"error": str(exc)}

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)

    # Exit 0 when read-only snapshot ran; non-fatal API gaps (403/404) stay in report.
    if not report.get("apphosting_page", {}).get("ok"):
        log.warning(
            "apphosting_page did not succeed — feature may be disabled or RBAC missing; see report JSON"
        )
    if not report.get("inventory", {}).get("ok"):
        log.warning(
            "inventory did not succeed — rows omit reachability join; see report JSON"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
