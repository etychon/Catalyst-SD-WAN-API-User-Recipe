"""Device action task status helpers (deploy, install, template push)."""

from __future__ import annotations

import json
import time
from typing import Any

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.util import unwrap_data

_TERMINAL = frozenset({"success", "done", "complete", "completed", "failure", "failed", "error", "cancelled"})


def get_action_status(client: ManagerClient, process_id: str) -> Any:
    """
    GET /dataservice/device/action/status/{processId}
    """
    pid = process_id.strip()
    if not pid:
        raise SdwanApiError("process_id is required")
    path = f"/dataservice/device/action/status/{pid}"
    r = client.request("GET", path)
    if r.status_code >= 400:
        raise SdwanApiError(f"{path} failed HTTP {r.status_code}: {r.text[:400]}")
    text = (r.text or "").strip()
    if not text:
        return {}
    try:
        return r.json()
    except json.JSONDecodeError as exc:
        raise SdwanApiError(f"{path} did not return JSON") from exc


def _normalize_status(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _task_complete(payload: Any) -> tuple[bool, bool, str]:
    """
    Return (finished, success, summary_message).
    Handles common Manager task response shapes (validate in lab).
    """
    if isinstance(payload, list):
        if not payload:
            return False, False, "empty status list"
        statuses = [_normalize_status(item.get("status") if isinstance(item, dict) else item) for item in payload]
        if any(s in _TERMINAL for s in statuses):
            failed = any(s in {"failure", "failed", "error", "cancelled"} for s in statuses)
            done = all(s in _TERMINAL or s == "" for s in statuses)
            if done:
                return True, not failed, f"per-device statuses: {statuses}"
        return False, False, f"in progress: {statuses}"

    if not isinstance(payload, dict):
        return False, False, "unexpected status payload"

    for key in ("status", "state", "activity"):
        st = _normalize_status(payload.get(key))
        if st in _TERMINAL:
            failed = st in {"failure", "failed", "error", "cancelled"}
            return True, not failed, st

    data = unwrap_data(payload)
    if isinstance(data, list) and data:
        return _task_complete(data)

    if isinstance(data, dict):
        return _task_complete(data)

    summary = payload.get("summary") or payload.get("message")
    if summary:
        s = _normalize_status(summary)
        if s in _TERMINAL:
            failed = s in {"failure", "failed", "error", "cancelled"}
            return True, not failed, str(summary)

    return False, False, "still running"


def poll_action_status(
    client: ManagerClient,
    process_id: str,
    *,
    timeout_sec: float = 900.0,
    interval_sec: float = 15.0,
) -> dict[str, Any]:
    """
    Poll GET /dataservice/device/action/status/{processId} until complete or timeout.
    """
    deadline = time.monotonic() + timeout_sec
    last_payload: Any = {}
    attempts = 0
    while True:
        attempts += 1
        last_payload = get_action_status(client, process_id)
        finished, success, summary = _task_complete(last_payload)
        if finished:
            return {
                "process_id": process_id,
                "finished": True,
                "success": success,
                "summary": summary,
                "attempts": attempts,
                "last_status": last_payload,
            }
        if time.monotonic() >= deadline:
            return {
                "process_id": process_id,
                "finished": False,
                "success": False,
                "summary": f"timeout after {timeout_sec}s",
                "attempts": attempts,
                "last_status": last_payload,
            }
        time.sleep(interval_sec)
