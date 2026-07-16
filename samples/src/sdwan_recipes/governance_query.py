"""Query builders for alarms, events, and audit log POST APIs."""

from __future__ import annotations

from typing import Any

from sdwan_recipes.client import ManagerClient


def rule_last_n_hours(hours: int, *, field: str = "entry_time") -> dict[str, Any]:
    return {
        "field": field,
        "type": "date",
        "operator": "last_n_hours",
        "value": [str(hours)],
    }


def rule_in(field: str, values: list[str], *, type: str = "string") -> dict[str, Any]:
    return {
        "field": field,
        "type": type,
        "operator": "in",
        "value": [str(v) for v in values],
    }


def rule_equal(field: str, value: str, *, type: str = "string") -> dict[str, Any]:
    return {
        "field": field,
        "type": type,
        "operator": "equal",
        "value": [str(value)],
    }


def rule_between_dates(field: str, start_utc: str, end_utc: str) -> dict[str, Any]:
    return {
        "field": field,
        "type": "date",
        "operator": "between",
        "value": [start_utc, end_utc],
    }


def build_query(
    rules: list[dict[str, Any]],
    *,
    condition: str = "AND",
    size: int = 10000,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": {
            "condition": condition,
            "rules": rules,
        },
    }
    if size is not None:
        payload["size"] = size
    return payload


def query_last_n_hours(client: ManagerClient, path: str, hours: int, *, size: int = 10000) -> dict[str, Any]:
    """POST a time-window query to alarms, events, or auditlog."""
    payload = build_query([rule_last_n_hours(hours)], size=size)
    return client.dataservice_post_json(path, json_body=payload)


FIELD_DISCOVERY_PATHS: dict[str, list[str]] = {
    "alarms": [
        "/dataservice/alarms/fields",
        "/dataservice/alarms/query/fields",
    ],
    "events": [
        "/dataservice/events/fields",
        "/dataservice/events/query/fields",
    ],
    "audit": [
        "/dataservice/auditlog/fields",
    ],
}


def fetch_query_fields(client: ManagerClient, resource: str) -> dict[str, Any]:
    """GET field metadata for alarms, events, or audit."""
    paths = FIELD_DISCOVERY_PATHS.get(resource)
    if not paths:
        raise ValueError(f"unknown resource: {resource!r}; use alarms, events, or audit")
    out: dict[str, Any] = {}
    for path in paths:
        try:
            out[path] = client.dataservice_json(path)
        except Exception as exc:  # noqa: BLE001 — probe all paths
            out[path] = {"error": str(exc)}
    return out


def discover_all_fields(client: ManagerClient) -> dict[str, Any]:
    return {name: fetch_query_fields(client, name) for name in FIELD_DISCOVERY_PATHS}


def records_from_response(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, list):
        return [x for x in response if isinstance(x, dict)]
    if not isinstance(response, dict):
        return []
    data = response.get("data")
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def count_from_response(response: Any) -> int:
    records = records_from_response(response)
    if records:
        if len(records) == 1 and "count" in records[0]:
            try:
                return int(records[0]["count"])
            except (TypeError, ValueError):
                pass
        return len(records)
    if isinstance(response, dict):
        count = response.get("count")
        if isinstance(count, int):
            return count
    return 0
