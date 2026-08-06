"""
UX 2.0 configuration group helpers (Cisco Catalyst SD-WAN Manager 20.18).

Wraps ``/dataservice/v1/config-group`` REST APIs for ``sdwan`` and ``sd-routing`` solutions.
Used by ``config_group_onboard.py`` and ``config_group_ux2.py`` recipe scripts.

Key flows:
- List groups, resolve by name, fetch detail and associations
- Discover unassigned reachable devices (inventory minus all group associations)
- Associate devices, GET/PUT device variables, deploy, verify sync state

Classic device templates are not managed here; detach templates before association.
"""

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
    Push configuration group to associated devices (async task).

    ``POST /dataservice/v1/config-group/{configGroupId}/device/deploy``

    Response typically includes ``parentTaskId`` for polling via
    ``device_actions.poll_action_status``. Custom Application install, when configured
    in the group, is triggered by this deploy—not by a separate install API in our samples.

    Args:
        client: Authenticated Manager client.
        config_group_id: Group UUID.
        device_ids: Subset of associated device ids to deploy.

    Returns:
        Response dict (often includes ``parentTaskId``); non-dict responses wrapped as ``{"raw": ...}``.

    Raises:
        SdwanApiError: Empty ``device_ids`` or HTTP/API error.
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
    """
    Resolve a UX 2.0 configuration group by exact display name.

    Args:
        client: Authenticated Manager client.
        name: Case-sensitive group name (Manager ``name`` field).
        solution: ``sdwan``, ``sd-routing``, or ``all`` when searching.

    Returns:
        Single matching group dict (includes ``id``, ``name``, ``solution``).

    Raises:
        SdwanApiError: No match or ambiguous duplicate names across solutions.
    """
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
    Derive the device ``id`` used by config-group associate/deploy/variables APIs.

    Preference order: ``uuid``, ``deviceId``, chassis/serial fields, then any key from
    ``inventory_device_keys``. Manager expects this id in ``{"devices": [{"id": "..."}]}``
    bodies—not necessarily the CSV serial number.

    Args:
        row: Single row from ``GET /dataservice/device``.

    Returns:
        Association id string, or ``None`` if no usable identifier found.
    """
    for field in ("uuid", "deviceId", "chasisNumber", "chassis-number", "board-serial"):
        val = row.get(field)
        if val is not None and str(val).strip():
            return str(val).strip()
    keys = inventory_device_keys(row)
    return next(iter(keys)) if keys else None


def inventory_serial(row: dict[str, Any]) -> str | None:
    """
    Extract hardware serial from an inventory row for CSV matching.

    Checks ``board-serial``, ``serialNumber``, ``serial-number``, ``chasisNumber``,
    ``chassis-number`` (Manager field names vary by platform).

    Returns:
        Serial string or ``None``.
    """
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
    """
    Build the set of device ids already associated to any UX 2.0 config group.

    Enumerates all groups (optionally filtered by ``solution``), calls
    ``GET .../device/associate`` per group, and unions ``id`` fields. Groups that
    fail to list associations are skipped (logged only via exception swallow in caller).

    Used by ``find_unassigned_reachable_devices`` to compute set difference against inventory.
    """
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
    List reachable inventory devices not yet in any UX 2.0 config group.

    Algorithm:
    1. ``GET /dataservice/device`` — keep rows with ``reachability == "reachable"``.
    2. ``collect_all_associated_device_ids`` — ids already in a config group.
    3. Exclude device if association id or any ``inventory_device_keys`` entry is in that set.

    Returns:
        List of summary dicts (``association_id``, ``serial_number``, ``host-name``,
        ``system-ip``, ``site-id``, ``device-model``, ``reachability``, ``uuid``).
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
    Associate devices to a configuration group (membership only; does not deploy).

    ``POST /dataservice/v1/config-group/{configGroupId}/device/associate``

    Args:
        client: Authenticated Manager client.
        config_group_id: UX 2.0 group UUID from list/detail API.
        device_ids: Manager device ids (see ``inventory_association_id``).

    Returns:
        Parsed JSON response body (shape varies).

    Raises:
        SdwanApiError: Empty ``device_ids`` or HTTP/API error from client.
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
    Set per-device variable values before deploy.

    ``PUT /dataservice/v1/config-group/{configGroupId}/device/variables``

    Args:
        client: Authenticated Manager client.
        config_group_id: Group UUID.
        solution: ``sdwan`` or ``sd-routing`` (required in request body).
        devices: List of ``{"device-id": "<id>", "variables": [{"name": "...", "value": ...}, ...]}``.

    Returns:
        Parsed JSON response body.

    Raises:
        SdwanApiError: Empty ``devices`` or HTTP/API error.
    """
    if not devices:
        raise SdwanApiError("set_group_device_variables requires at least one device")
    body = {"solution": solution, "devices": devices}
    path = f"/dataservice/v1/config-group/{config_group_id}/device/variables"
    return client.dataservice_put_json(path, json_body=body)


def schema_variable_names(schema: Any) -> list[str]:
    """
    Extract device variable names from a variables schema response (best-effort).

    Recursively walks nested dict/list JSON from
    ``GET .../device/variables/schema`` and collects unique ``name`` string fields.
    Order follows depth-first discovery; validate names against your group in lab.

    Args:
        schema: Raw JSON from ``get_group_variables_schema``.

    Returns:
        De-duplicated list of variable name strings (may be empty if schema shape differs).
    """
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
    """
    Heuristic: group profile metadata suggests Custom Application / app-hosting.

    Scans ``profiles[].name``, ``type``, and ``description`` for substrings such as
    ``app-hosting``, ``custom application``, ``other`` (service profile). A False result
    does not prove the group lacks app hosting—only that no hint was detected in metadata.

    Args:
        group: Config group detail dict from ``get_config_group_detail``.

    Returns:
        True if any hint substring matches.
    """
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
    """
    Check post-deploy sync state for one device in a config group.

    Reads ``GET .../device/associate`` and finds the row matching ``device_id``.
    ``deployed_ok`` is True when ``configGroupUpToDate`` is True or ``configStatusMessage``
    contains ``success`` without ``fail``.

    Args:
        client: Authenticated Manager client.
        config_group_id: Group UUID.
        device_id: Device id used in associate/deploy APIs.

    Returns:
        Dict with ``device_id``, ``configGroupUpToDate``, ``configStatusMessage``,
        ``device-lock``, ``unsupportedFeatures``, ``deployed_ok``; or ``error`` if not found.
    """
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
