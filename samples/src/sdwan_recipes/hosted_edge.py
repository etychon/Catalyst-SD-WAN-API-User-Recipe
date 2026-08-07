"""
Hosted Edge Services (IOx / app-hosting) monitoring helpers — read-only v1.

Wraps statistics-plane App Hosting APIs (``POST /statistics/apphosting/page``, etc.)
and inventory joins. Deploy/start/stop are out of scope here; see config-group recipes
and docs/recipes/hosted-edge-services-iox.md.

Validate request/response shapes against your Manager ``/apidocs`` OpenAPI (20.18.x).
"""

from __future__ import annotations

from typing import Any

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.governance_query import build_query, rule_in, rule_last_n_hours
from sdwan_recipes.util import device_rows, unwrap_data

APPHOSTING_PAGE = "/dataservice/statistics/apphosting/page"
APPHOSTING_DOCCOUNT = "/dataservice/statistics/apphosting/doccount"
APPHOSTINGINTERFACE_PAGE = "/dataservice/statistics/apphostinginterface/page"
APPHOSTINGINTERFACE_DOCCOUNT = "/dataservice/statistics/apphostinginterface/doccount"
CUSTOM_APPS_PATH = "/dataservice/sdavc/customapps"

# Default statistics device rule field (override via env in script if lab differs).
DEFAULT_STATS_DEVICE_FIELD = "vdevice_name"

APPHOSTING_FIELD_PATHS = (
    "/dataservice/statistics/apphosting/query/fields",
    "/dataservice/statistics/apphosting/fields",
)
APPHOSTINGINTERFACE_FIELD_PATHS = (
    "/dataservice/statistics/apphostinginterface/query/fields",
    "/dataservice/statistics/apphostinginterface/fields",
)


def build_apphosting_page_query(
    hours: int,
    *,
    device_system_ip: str | None = None,
    device_field: str = DEFAULT_STATS_DEVICE_FIELD,
    size: int = 10000,
) -> dict[str, Any]:
    """
    Build POST body for ``/statistics/apphosting/page``.

    Uses the same query DSL as alarms/events (``entry_time`` + optional device rule).
    Field names are illustrative — confirm with ``GET …/apphosting/query/fields`` in lab.
    """
    rules = [rule_last_n_hours(hours)]
    if device_system_ip:
        rules.append(rule_in(device_field, [device_system_ip.strip()]))
    return build_query(rules, size=size)


def query_apphosting_page(
    client: ManagerClient,
    body: dict[str, Any],
) -> Any:
    """POST ``/dataservice/statistics/apphosting/page``."""
    return client.dataservice_post_json(APPHOSTING_PAGE, json_body=body)


def query_apphosting_doccount(
    client: ManagerClient,
    body: dict[str, Any],
) -> Any:
    """POST doccount with the same query body (common statistics pattern)."""
    return client.dataservice_post_json(APPHOSTING_DOCCOUNT, json_body=body)


def query_apphostinginterface_page(
    client: ManagerClient,
    body: dict[str, Any],
) -> Any:
    """POST ``/dataservice/statistics/apphostinginterface/page``."""
    return client.dataservice_post_json(APPHOSTINGINTERFACE_PAGE, json_body=body)


def query_apphostinginterface_doccount(
    client: ManagerClient,
    body: dict[str, Any],
) -> Any:
    """POST interface family doccount."""
    return client.dataservice_post_json(APPHOSTINGINTERFACE_DOCCOUNT, json_body=body)


def _probe_paths(client: ManagerClient, paths: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in paths:
        try:
            out[path] = client.dataservice_json(path)
        except SdwanApiError as exc:
            out[path] = {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001 — field discovery probes
            out[path] = {"error": str(exc)}
    return out


def discover_apphosting_query_fields(client: ManagerClient) -> dict[str, Any]:
    """Try known field-metadata paths; 404 is normal when the family is disabled."""
    return {
        "apphosting": _probe_paths(client, APPHOSTING_FIELD_PATHS),
        "apphostinginterface": _probe_paths(client, APPHOSTINGINTERFACE_FIELD_PATHS),
    }


def list_custom_apps(client: ManagerClient) -> Any:
    """
    GET ``/dataservice/sdavc/customapps`` — SD-AVC user-defined apps (related, not Hosted Edge monitor).
    """
    return client.dataservice_json(CUSTOM_APPS_PATH)


def normalize_apphosting_rows(payload: Any) -> list[dict[str, Any]]:
    """
    Extract row dicts from apphosting page/doccount responses.

    Handles ``data[]``, nested ``items[].data``, or a top-level list (validate in lab).
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    rows: list[dict[str, Any]] = []
    data = payload.get("data")
    if isinstance(data, list):
        rows.extend(x for x in data if isinstance(x, dict))

    items = payload.get("items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            inner = item.get("data")
            if isinstance(inner, list):
                rows.extend(x for x in inner if isinstance(x, dict))
            elif isinstance(inner, dict):
                rows.append(inner)

    if rows:
        return rows

    inner = unwrap_data(payload)
    if isinstance(inner, list):
        return [x for x in inner if isinstance(x, dict)]
    if isinstance(inner, dict):
        return [inner]
    return []


def _inventory_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field in (
        "system-ip",
        "systemIp",
        "deviceId",
        "local-system-ip",
        "localSystemIp",
        "host-name",
        "hostName",
        "uuid",
        "vdevice-name",
        "vdevice_name",
    ):
        val = row.get(field)
        if val is not None and str(val).strip():
            keys.add(str(val).strip())
    return keys


def _row_device_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field in (
        "vdevice_name",
        "vdevice-name",
        "system-ip",
        "systemIp",
        "deviceId",
        "device-ip",
        "deviceIP",
        "host-name",
        "hostName",
    ):
        val = row.get(field)
        if val is not None and str(val).strip():
            keys.add(str(val).strip())
    return keys


def join_apphosting_to_inventory(
    rows: list[dict[str, Any]],
    inventory_payload: Any,
) -> list[dict[str, Any]]:
    """
    Enrich apphosting statistics rows with inventory reachability and site metadata.

    Join is best-effort on system-ip / vdevice_name / deviceId (lab-validate keys).
    """
    index: dict[str, dict[str, Any]] = {}
    for inv in device_rows(inventory_payload):
        for key in _inventory_keys(inv):
            index[key] = inv

    enriched: list[dict[str, Any]] = []
    for row in rows:
        merged = dict(row)
        inv: dict[str, Any] | None = None
        for key in _row_device_keys(row):
            inv = index.get(key)
            if inv:
                break
        if inv:
            merged["inventory"] = {
                "host-name": inv.get("host-name") or inv.get("hostName"),
                "system-ip": inv.get("system-ip") or inv.get("systemIp"),
                "site-id": inv.get("site-id") or inv.get("siteId"),
                "reachability": inv.get("reachability"),
                "device-model": inv.get("device-model") or inv.get("deviceModel"),
            }
        else:
            merged["inventory"] = None
        enriched.append(merged)
    return enriched


def summarize_apphosting_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Lightweight fleet summary for JSON reports."""
    apps: set[str] = set()
    devices: set[str] = set()
    for row in rows:
        for field in ("app_name", "appName", "application", "application_name", "name"):
            val = row.get(field)
            if val:
                apps.add(str(val))
        for field in ("vdevice_name", "vdevice-name", "system-ip", "systemIp", "deviceId"):
            val = row.get(field)
            if val:
                devices.add(str(val))
    return {
        "row_count": len(rows),
        "distinct_app_names": sorted(apps),
        "distinct_device_keys": sorted(devices),
    }
