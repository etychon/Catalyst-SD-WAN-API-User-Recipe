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


def get_config_group_detail(
    client: ManagerClient,
    config_group_id: str,
    *,
    device_list: bool = True,
) -> dict[str, Any]:
    """GET /dataservice/v1/config-group/{configGroupId}"""
    path = f"/dataservice/v1/config-group/{config_group_id}"
    payload = client.dataservice_json(path, params={"deviceList": device_list})
    if isinstance(payload, dict):
        return payload
    inner = unwrap_data(payload)
    if isinstance(inner, dict):
        return inner
    return {}


def resolve_config_group_by_name(
    client: ManagerClient,
    name: str,
    *,
    solution: str | None = "all",
) -> dict[str, Any]:
    """Find a config group by exact name (case-sensitive)."""
    want = name.strip()
    matches = [g for g in list_config_groups(client, solution=solution) if str(g.get("name") or "") == want]
    if not matches:
        raise SdwanApiError(f"No configuration group named {name!r}")
    if len(matches) > 1:
        ids = [str(g.get("id")) for g in matches]
        raise SdwanApiError(f"Multiple configuration groups named {name!r}: {ids}")
    return matches[0]


def inventory_device_keys(row: dict[str, Any]) -> set[str]:
    """Normalized lookup keys for an inventory device row."""
    keys: set[str] = set()
    for field in (
        "uuid",
        "deviceId",
        "system-ip",
        "systemIp",
        "host-name",
        "hostName",
        "chasisNumber",
        "chassis-number",
        "board-serial",
        "serialNumber",
        "serial-number",
    ):
        val = row.get(field)
        if val is not None and str(val).strip():
            keys.add(str(val).strip())
    return keys


def inventory_association_id(row: dict[str, Any]) -> str | None:
    """
    Best device id for config-group associate/deploy APIs.
    Prefer uuid/deviceId; fall back to other inventory keys.
    """
    for field in ("uuid", "deviceId", "chasisNumber", "chassis-number", "board-serial"):
        val = row.get(field)
        if val is not None and str(val).strip():
            return str(val).strip()
    keys = inventory_device_keys(row)
    return next(iter(keys)) if keys else None


def inventory_serial(row: dict[str, Any]) -> str | None:
    for field in ("board-serial", "serialNumber", "serial-number", "chasisNumber", "chassis-number"):
        val = row.get(field)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def collect_all_associated_device_ids(
    client: ManagerClient,
    *,
    solution: str | None = "all",
) -> set[str]:
    """Union of device ids associated to any UX 2.0 config group."""
    associated: set[str] = set()
    for group in list_config_groups(client, solution=solution):
        gid = str(group.get("id") or "")
        if not gid:
            continue
        try:
            rows = get_group_associations(client, gid)
        except SdwanApiError:
            continue
        for row in rows:
            did = row.get("id")
            if did is not None and str(did).strip():
                associated.add(str(did).strip())
    return associated


def find_unassigned_reachable_devices(
    client: ManagerClient,
    *,
    solution: str | None = "all",
) -> list[dict[str, Any]]:
    """
    Reachable inventory devices not associated to any UX 2.0 config group.
    """
    inventory = client.dataservice_json("/dataservice/device")
    associated = collect_all_associated_device_ids(client, solution=solution)
    out: list[dict[str, Any]] = []
    for row in device_rows(inventory):
        if row.get("reachability") != "reachable":
            continue
        keys = inventory_device_keys(row)
        assoc_id = inventory_association_id(row)
        if (assoc_id and assoc_id in associated) or (keys & associated):
            continue
        out.append(
            {
                "association_id": assoc_id,
                "serial_number": inventory_serial(row),
                "host-name": row.get("host-name") or row.get("hostName"),
                "system-ip": row.get("system-ip") or row.get("systemIp"),
                "site-id": row.get("site-id") or row.get("siteId"),
                "device-model": row.get("device-model") or row.get("deviceModel"),
                "reachability": row.get("reachability"),
                "uuid": row.get("uuid"),
            }
        )
    return out


def associate_devices_to_group(
    client: ManagerClient,
    config_group_id: str,
    device_ids: list[str],
) -> Any:
    """
    POST /dataservice/v1/config-group/{configGroupId}/device/associate
    """
    if not device_ids:
        raise SdwanApiError("associate requires at least one device id")
    body = {"devices": [{"id": did} for did in device_ids]}
    path = f"/dataservice/v1/config-group/{config_group_id}/device/associate"
    return client.dataservice_post_json(path, json_body=body)


def get_group_device_variables(
    client: ManagerClient,
    config_group_id: str,
    *,
    device_ids: list[str] | None = None,
) -> dict[str, Any]:
    """GET /dataservice/v1/config-group/{configGroupId}/device/variables"""
    path = f"/dataservice/v1/config-group/{config_group_id}/device/variables"
    params: dict[str, Any] | None = None
    if device_ids:
        params = {"device-id": ",".join(device_ids)}
    payload = client.dataservice_json(path, params=params)
    if isinstance(payload, dict):
        return payload
    inner = unwrap_data(payload)
    if isinstance(inner, dict):
        return inner
    return {}


def get_group_variables_schema(
    client: ManagerClient,
    config_group_id: str,
    *,
    all_vars: bool = True,
) -> Any:
    """GET /dataservice/v1/config-group/{configGroupId}/device/variables/schema"""
    path = f"/dataservice/v1/config-group/{config_group_id}/device/variables/schema"
    return client.dataservice_json(path, params={"all": all_vars})


def set_group_device_variables(
    client: ManagerClient,
    config_group_id: str,
    solution: str,
    devices: list[dict[str, Any]],
) -> Any:
    """
    PUT /dataservice/v1/config-group/{configGroupId}/device/variables
    devices: list of {"device-id": "...", "variables": [{"name": "...", "value": ...}, ...]}
    """
    if not devices:
        raise SdwanApiError("set_group_device_variables requires at least one device")
    body = {"solution": solution, "devices": devices}
    path = f"/dataservice/v1/config-group/{config_group_id}/device/variables"
    return client.dataservice_put_json(path, json_body=body)


def schema_variable_names(schema: Any) -> list[str]:
    """Extract variable names from variables schema payload (best-effort)."""
    names: list[str] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "name" in node and isinstance(node.get("name"), str):
                n = node["name"]
                if n not in seen:
                    seen.add(n)
                    names.append(n)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    return names


def group_has_app_hosting_hint(group: dict[str, Any]) -> bool:
    """Heuristic: config group may include Custom Application / app-hosting."""
    text_parts: list[str] = []
    for profile in group.get("profiles") or []:
        if not isinstance(profile, dict):
            continue
        for key in ("name", "type", "description"):
            val = profile.get(key)
            if val:
                text_parts.append(str(val).lower())
    blob = " ".join(text_parts)
    hints = ("app-hosting", "app hosting", "custom application", "custom-app", "other")
    return any(h in blob for h in hints)


def verify_association_deployed(
    client: ManagerClient,
    config_group_id: str,
    device_id: str,
) -> dict[str, Any]:
    """Return association row and interpreted sync state for one device."""
    for row in get_group_associations(client, config_group_id):
        if str(row.get("id") or "") == device_id:
            up = is_config_group_up_to_date(row)
            msg = str(row.get("configStatusMessage") or "")
            ok = up is True or ("success" in msg.lower() and "fail" not in msg.lower())
            return {
                "device_id": device_id,
                "configGroupUpToDate": row.get("configGroupUpToDate"),
                "configStatusMessage": msg,
                "device-lock": row.get("device-lock"),
                "unsupportedFeatures": row.get("unsupportedFeatures"),
                "deployed_ok": ok,
            }
    return {
        "device_id": device_id,
        "deployed_ok": False,
        "error": "device not found in group association list",
    }
