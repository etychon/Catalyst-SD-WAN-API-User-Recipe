"""UX 2.0 configuration group helpers (Manager 20.18)."""

from __future__ import annotations

from typing import Any

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.util import device_rows, unwrap_data

UX2_SOLUTIONS = ("sdwan", "sd-routing")


def _as_group_list(payload: Any) -> list[dict[str, Any]]:
    inner = unwrap_data(payload)
    if isinstance(inner, list):
        return [x for x in inner if isinstance(x, dict)]
    if isinstance(inner, dict):
        return [inner]
    return []


def list_config_groups(
    client: ManagerClient,
    *,
    solution: str | None = None,
) -> list[dict[str, Any]]:
    """
    GET /dataservice/v1/config-group?solution=...
    solution: sdwan, sd-routing, or None for both (two calls).
    """
    if solution and solution not in UX2_SOLUTIONS and solution != "all":
        raise ValueError(f"solution must be one of {UX2_SOLUTIONS + ('all',)}")

    targets: tuple[str, ...]
    if solution is None or solution == "all":
        targets = UX2_SOLUTIONS
    else:
        targets = (solution,)

    groups: list[dict[str, Any]] = []
    for sol in targets:
        payload = client.dataservice_json(
            "/dataservice/v1/config-group",
            params={"solution": sol},
        )
        for row in _as_group_list(payload):
            row.setdefault("solution", sol)
            groups.append(row)
    return groups


def get_group_associations(
    client: ManagerClient,
    config_group_id: str,
) -> list[dict[str, Any]]:
    """GET /dataservice/v1/config-group/{id}/device/associate"""
    path = f"/dataservice/v1/config-group/{config_group_id}/device/associate"
    payload = client.dataservice_json(path)
    if isinstance(payload, dict):
        devices = payload.get("devices")
        if isinstance(devices, list):
            return [x for x in devices if isinstance(x, dict)]
    inner = unwrap_data(payload)
    if isinstance(inner, list):
        return [x for x in inner if isinstance(x, dict)]
    return []


def build_reachability_index(inventory_payload: Any) -> dict[str, dict[str, Any]]:
    """Map multiple keys (uuid, system-ip, host-name, id) -> inventory row."""
    index: dict[str, dict[str, Any]] = {}
    for row in device_rows(inventory_payload):
        keys = [
            row.get("uuid"),
            row.get("deviceId"),
            row.get("system-ip"),
            row.get("systemIp"),
            row.get("host-name"),
            row.get("hostName"),
            row.get("chasisNumber"),
            row.get("chassis-number"),
        ]
        for k in keys:
            if k is not None and str(k).strip():
                index[str(k).strip()] = row
    return index


def device_reachability(
    assoc: dict[str, Any],
    reach_index: dict[str, dict[str, Any]],
) -> str | None:
    """Return reachability string from inventory join, or None if unknown."""
    candidates = [
        assoc.get("id"),
        assoc.get("deviceIP"),
        assoc.get("host-name"),
        assoc.get("hostName"),
    ]
    for c in candidates:
        if c is None:
            continue
        inv = reach_index.get(str(c).strip())
        if inv:
            return inv.get("reachability")
    return None


def is_config_group_up_to_date(assoc: dict[str, Any]) -> bool | None:
    """
    Interpret configGroupUpToDate from association API.
    Returns True/False, or None if unknown.
    """
    raw = assoc.get("configGroupUpToDate")
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().lower()
    if s in ("true", "yes", "1"):
        return True
    if s in ("false", "no", "0"):
        return False
    return None


def is_out_of_sync(assoc: dict[str, Any]) -> bool:
    up = is_config_group_up_to_date(assoc)
    if up is False:
        return True
    if up is True:
        return False
    msg = (assoc.get("configStatusMessage") or "").lower()
    if "out of sync" in msg or "not in sync" in msg:
        return True
    return False


def deploy_config_group(
    client: ManagerClient,
    config_group_id: str,
    device_ids: list[str],
) -> dict[str, Any]:
    """
    POST /dataservice/v1/config-group/{configGroupId}/device/deploy
    """
    if not device_ids:
        raise SdwanApiError("deploy requires at least one device id")
    body = {"devices": [{"id": did} for did in device_ids]}
    path = f"/dataservice/v1/config-group/{config_group_id}/device/deploy"
    result = client.dataservice_post_json(path, json_body=body)
    if not isinstance(result, dict):
        return {"raw": result}
    return result
