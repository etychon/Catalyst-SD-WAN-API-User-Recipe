"""Helpers for Cisco Catalyst SD-WAN Manager JSON responses."""

from __future__ import annotations

from typing import Any


def unwrap_data(payload: Any) -> Any:
    """
    Many /dataservice responses wrap rows in {"data": [...]}.
    Return the inner list or dict when present; otherwise return payload.
    """
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def device_rows(payload: Any) -> list[dict[str, Any]]:
    inner = unwrap_data(payload)
    if inner is None:
        return []
    if isinstance(inner, list):
        return [x for x in inner if isinstance(x, dict)]
    if isinstance(inner, dict):
        return [inner]
    return []
