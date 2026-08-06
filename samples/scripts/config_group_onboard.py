#!/usr/bin/env python3
"""
UX 2.0 configuration group CSV onboarding CLI (Cisco Catalyst SD-WAN Manager 20.18).

Automates discovery, association, device-variable provisioning, deploy, and post-deploy
verification for ``sdwan`` and ``sd-routing`` configuration groups. Classic device
templates are out of scope.

Operator workflow
-----------------
1. **Discover** reachable devices not yet assigned to any UX 2.0 config group::

       python scripts/config_group_onboard.py --discover-unassigned --output output/unassigned.json

2. **Generate a CSV template** (optional variable columns from a named group)::

       python scripts/config_group_onboard.py \\
         --discover-unassigned --template-group MY_GROUP --output-csv output/onboard.csv

3. **Validate** CSV rows against live inventory (no Manager writes)::

       python scripts/config_group_onboard.py --csv output/onboard.csv --dry-run

4. **Apply and deploy** (requires explicit confirmation flags)::

       python scripts/config_group_onboard.py \\
         --csv output/onboard.csv --apply --confirm-apply --deploy --confirm-deploy

Safety defaults
---------------
- Read-only unless ``--apply --confirm-apply`` is passed (associate + variables PUT).
- Deploy POST runs only with ``--deploy --confirm-deploy`` (and requires ``--apply``).
- Credentials load from ``samples/.env`` via ``Settings``; never log tokens or passwords.

CSV contract
------------
Required columns: ``serial_number``, ``config_group``. Additional columns are treated as
device variables (names should match the group's variables schema). Empty variable cells
are omitted from the PUT payload. Values are coerced: booleans, numbers, JSON literals,
or strings (see ``_coerce_value``).

Custom Application / app-hosting
--------------------------------
This script does **not** call a separate software-install API. Custom Application install
is expected to occur as part of config-group deploy when the group includes an
app-hosting profile. Verification uses deploy task polling plus association sync fields.

Exit codes
----------
- ``0`` — success (all rows ``ok`` when ``results`` present)
- ``1`` — one or more CSV rows failed validation or a write/deploy step
- ``2`` — usage error (missing mode, confirmation flags, etc.)

JSON report
-----------
Stdout or ``--output`` file. Modes: ``discover-unassigned``, ``csv-dry-run``, ``csv-apply``.
Each CSV row gets a ``results[]`` entry with ``stage`` progressing through
``validate`` → ``associate`` → ``variables`` → ``deploy`` and optional ``verification``.

See also: ``docs/recipes/config-group-csv-onboard-deploy.md``
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sdwan_recipes.client import ManagerClient, SdwanApiError
from sdwan_recipes.config import Settings
from sdwan_recipes.config_group import (
    associate_devices_to_group,
    deploy_config_group,
    find_unassigned_reachable_devices,
    get_config_group_detail,
    get_group_associations,
    get_group_variables_schema,
    group_has_app_hosting_hint,
    inventory_association_id,
    inventory_device_keys,
    inventory_serial,
    resolve_config_group_by_name,
    schema_variable_names,
    set_group_device_variables,
    verify_association_deployed,
)
from sdwan_recipes.device_actions import poll_action_status
from sdwan_recipes.util import device_rows, unwrap_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("config_group_onboard")

# CSV columns reserved for routing metadata; all other header names become device variables.
FIXED_CSV_COLUMNS = frozenset({"serial_number", "config_group"})


def _build_serial_index(client: ManagerClient) -> dict[str, dict[str, Any]]:
    """
    Build a case-insensitive lookup from serial / chassis identifiers to inventory rows.

    Uses ``GET /dataservice/device``. Each device's ``board-serial`` (and related fields)
    maps to its row; longer alternate keys (uuid, system-ip, etc.) are indexed when
    at least six characters so operators can match CSV serials flexibly.

    Args:
        client: Authenticated Manager client.

    Returns:
        Dict keyed by lowercased identifier string → full inventory row dict.
    """
    payload = client.dataservice_json("/dataservice/device")
    index: dict[str, dict[str, Any]] = {}
    for row in device_rows(payload):
        serial = inventory_serial(row)
        if serial:
            index[serial.lower()] = row
        for key in inventory_device_keys(row):
            if len(key) >= 6 and key.lower() not in index:
                index[key.lower()] = row
    return index


def _coerce_value(raw: str) -> Any:
    """
    Parse a CSV cell into a JSON-friendly Python value for variable PUT bodies.

    Rules (applied in order):
    - Whitespace-only → empty string ``""`` (caller may skip empty variable columns).
    - ``true``/``yes``/``false``/``no`` (case-insensitive) → bool.
    - Leading ``[`` or ``{`` → ``json.loads``; on failure, keep original string.
    - Integer if no ``.``; else float; on ``ValueError``, keep string.

    Args:
        raw: Raw cell text from CSV (may be empty).

    Returns:
        Coerced value suitable for ``variables[].value`` in the Manager API.
    """
    s = raw.strip()
    if not s:
        return ""
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if s.startswith("[") or s.startswith("{"):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _load_csv(path: Path) -> list[dict[str, str]]:
    """
    Read and validate the onboarding CSV file.

    Requires header columns ``serial_number`` and ``config_group``. Skips blank data rows.
    Strips whitespace from headers and cell values.

    Args:
        path: Path to UTF-8 CSV file.

    Returns:
        List of row dicts (string values) in file order.

    Raises:
        SdwanApiError: Missing header, required columns, or empty required fields (includes line number).
    """
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise SdwanApiError(f"CSV {path} has no header row")
        missing = FIXED_CSV_COLUMNS - {h.strip() for h in reader.fieldnames if h}
        if missing:
            raise SdwanApiError(f"CSV missing required columns: {sorted(missing)}")
        rows: list[dict[str, str]] = []
        for i, row in enumerate(reader, start=2):
            cleaned = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            if not any(cleaned.values()):
                continue
            if not cleaned.get("serial_number"):
                raise SdwanApiError(f"CSV line {i}: serial_number is required")
            if not cleaned.get("config_group"):
                raise SdwanApiError(f"CSV line {i}: config_group is required")
            rows.append(cleaned)
        return rows


def _variable_columns(fieldnames: list[str]) -> list[str]:
    """
    Return CSV header names that represent device variables (not fixed routing columns).

    Args:
        fieldnames: Raw ``DictReader.fieldnames`` list.

    Returns:
        Ordered list of variable column names (preserves CSV column order).
    """
    return [f for f in fieldnames if f and f.strip() not in FIXED_CSV_COLUMNS]


def _row_to_device_payload(row: dict[str, str], var_cols: list[str]) -> dict[str, Any]:
    """
    Convert one CSV row into an internal structure for grouping and API calls.

    Non-empty variable columns become ``{"name", "value"}`` entries with coerced values.

    Args:
        row: Cleaned CSV row dict.
        var_cols: Variable column names from ``_variable_columns``.

    Returns:
        Dict with ``serial_number``, ``config_group``, and ``variables`` list.
    """
    variables = [{"name": col, "value": _coerce_value(row.get(col, ""))} for col in var_cols if row.get(col, "")]
    return {
        "serial_number": row["serial_number"],
        "config_group": row["config_group"],
        "variables": variables,
    }


def _template_attached_serials(client: ManagerClient) -> set[str]:
    """
    Collect serial numbers still attached to classic device templates.

    Used during discover to flag ``template_attached_warning`` on each device. Devices
    must typically be detached from classic templates before UX 2.0 config-group association.

    Calls ``GET /dataservice/template/device/config/attached``. Failures return an empty set
    (non-fatal; discovery still proceeds).

    Args:
        client: Authenticated Manager client.

    Returns:
        Lowercased serial strings found in the attached-template response.
    """
    attached: set[str] = set()
    r = client.request("GET", "/dataservice/template/device/config/attached")
    if not r.is_success:
        return attached
    try:
        payload = r.json()
    except json.JSONDecodeError:
        return attached
    rows = unwrap_data(payload)
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        return attached
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in ("serialNumber", "serial-number", "board-serial", "chasisNumber"):
            val = row.get(field)
            if val:
                attached.add(str(val).strip().lower())
    return attached


def run_discover(
    client: ManagerClient,
    *,
    solution: str,
    output_csv: Path | None,
    template_group: str | None,
) -> dict[str, Any]:
    """
    Discover reachable inventory devices not assigned to any UX 2.0 config group.

    Optionally writes a CSV template with ``serial_number``, ``config_group``, and variable
    columns derived from ``--template-group`` schema (``GET .../device/variables/schema``).

    Args:
        client: Authenticated Manager client.
        solution: ``sdwan``, ``sd-routing``, or ``all`` (filters config-group enumeration).
        output_csv: If set, write CSV template to this path (creates parent dirs).
        template_group: Config group name to pre-fill in CSV and supply variable column headers.

    Returns:
        JSON-serializable report::

            {
              "mode": "discover-unassigned",
              "solution_filter": "...",
              "count": N,
              "devices": [ { association_id, serial_number, ... , template_attached_warning }, ... ],
              "template_config_group": { ... }  # only when template_group set
            }
    """
    devices = find_unassigned_reachable_devices(client, solution=solution)
    template_serials = _template_attached_serials(client)
    for d in devices:
        sn = (d.get("serial_number") or "").lower()
        d["template_attached_warning"] = sn in template_serials if sn else False

    report: dict[str, Any] = {
        "mode": "discover-unassigned",
        "solution_filter": solution,
        "count": len(devices),
        "devices": devices,
    }

    if output_csv:
        var_cols: list[str] = []
        if template_group:
            group = resolve_config_group_by_name(client, template_group, solution=solution)
            gid = str(group.get("id") or "")
            sol = str(group.get("solution") or "sdwan")
            try:
                schema = get_group_variables_schema(client, gid)
                var_cols = schema_variable_names(schema)
            except SdwanApiError as exc:
                log.warning("Could not load variable schema for %s: %s", template_group, exc)
            report["template_config_group"] = {"name": template_group, "id": gid, "solution": sol}
        header = ["serial_number", "config_group", *var_cols]
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
            writer.writeheader()
            for d in devices:
                row = {
                    "serial_number": d.get("serial_number") or "",
                    "config_group": template_group or "",
                }
                writer.writerow(row)
        log.info("Wrote CSV template %s", output_csv)

    return report


def _resolve_row_device(
    row: dict[str, str],
    serial_index: dict[str, dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """
    Map a CSV ``serial_number`` to Manager association id and inventory row.

    Args:
        row: CSV row with ``serial_number``.
        serial_index: Output of ``_build_serial_index``.

    Returns:
        Tuple ``(association_id, inventory_row, error_message)``. On success ``error_message``
        is ``None``; on failure ``association_id`` and possibly ``inventory_row`` are ``None``.
    """
    serial = row["serial_number"].strip()
    inv = serial_index.get(serial.lower())
    if not inv:
        return None, None, f"no inventory match for serial {serial!r}"
    assoc_id = inventory_association_id(inv)
    if not assoc_id:
        return None, inv, f"could not derive association id for serial {serial!r}"
    return assoc_id, inv, None


def run_csv(
    client: ManagerClient,
    *,
    csv_path: Path,
    solution: str,
    dry_run: bool,
    apply: bool,
    deploy: bool,
    skip_locked: bool,
    poll_timeout: float,
    poll_interval: float,
) -> dict[str, Any]:
    """
    Process an onboarding CSV: validate, optionally associate, set variables, deploy, verify.

    Pipeline stages per config group (when ``apply`` is True):

    1. **Validate** — serial → inventory, reachability, resolve group by name, load schema.
    2. **Associate** — ``POST .../device/associate`` with device ids for that group.
    3. **Variables** — ``PUT .../device/variables`` with per-device variable lists.
    4. **Deploy** (if ``deploy``) — ``POST .../device/deploy``, poll ``parentTaskId`` via
       ``GET /device/action/status/{processId}``, then ``verify_association_deployed`` per device.

    Rows are grouped by ``config_group`` column so each group triggers one associate/variables/deploy
    batch. Failures on one group do not stop processing of other groups.

    Args:
        client: Authenticated Manager client.
        csv_path: Input CSV path.
        solution: Filter when resolving group names (``sdwan``, ``sd-routing``, ``all``).
        dry_run: If True (or ``apply`` False), stop after validation; no mutating API calls.
        apply: When True with ``confirm-apply`` (checked in ``main``), run associate + variables.
        deploy: When True with ``confirm-deploy``, run deploy + poll + verification after variables.
        skip_locked: Skip devices whose association row has ``device-lock: Yes`` before associate.
        poll_timeout: Max seconds to poll deploy task status.
        poll_interval: Seconds between poll attempts.

    Returns:
        Report dict with ``mode`` ``csv-dry-run`` or ``csv-apply``, ``groups`` metadata,
        ``results`` per row, and ``deploy_tasks`` when deploy ran.
    """
    rows = _load_csv(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        var_cols = _variable_columns(list(reader.fieldnames or []))

    serial_index = _build_serial_index(client)
    parsed = [_row_to_device_payload(r, var_cols) for r in rows]

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    results: list[dict[str, Any]] = []

    # --- Phase 1: per-row validation and grouping ---
    for raw_row, item in zip(rows, parsed, strict=True):
        assoc_id, inv, err = _resolve_row_device(raw_row, serial_index)
        entry: dict[str, Any] = {
            "serial_number": item["serial_number"],
            "config_group": item["config_group"],
            "stage": "validate",
            "ok": err is None,
        }
        if err:
            entry["error"] = err
            results.append(entry)
            continue
        if inv and inv.get("reachability") != "reachable":
            entry["ok"] = False
            entry["error"] = f"device not reachable (reachability={inv.get('reachability')!r})"
            results.append(entry)
            continue
        entry["association_id"] = assoc_id
        group_name = item["config_group"]
        by_group[group_name].append(
            {
                "serial_number": item["serial_number"],
                "association_id": assoc_id,
                "variables": item["variables"],
            }
        )
        results.append(entry)

    # --- Phase 2: resolve each config group and load variable schema ---
    group_meta: dict[str, dict[str, Any]] = {}
    for group_name in list(by_group.keys()):
        try:
            group = resolve_config_group_by_name(client, group_name, solution=solution)
            gid = str(group.get("id") or "")
            detail = get_config_group_detail(client, gid)
            schema = get_group_variables_schema(client, gid)
            var_names = schema_variable_names(schema)
            group_meta[group_name] = {
                "id": gid,
                "solution": str(group.get("solution") or detail.get("solution") or "sdwan"),
                "variable_names_in_schema": var_names,
                "app_hosting_hint": group_has_app_hosting_hint(detail),
            }
            if not group_meta[group_name]["app_hosting_hint"]:
                log.warning(
                    "Config group %s has no detectable Custom Application / app-hosting profile hint",
                    group_name,
                )
        except SdwanApiError as exc:
            for entry in results:
                if entry.get("config_group") == group_name and entry.get("ok"):
                    entry["ok"] = False
                    entry["error"] = str(exc)
            by_group.pop(group_name, None)

    if dry_run or not apply:
        return {
            "mode": "csv-dry-run",
            "csv": str(csv_path),
            "row_count": len(rows),
            "groups": group_meta,
            "results": results,
        }

    deploy_tasks: list[dict[str, Any]] = []

    # --- Phase 3: mutating API calls per config group ---
    for group_name, members in by_group.items():
        meta = group_meta[group_name]
        gid = meta["id"]
        sol = meta["solution"]
        device_ids = [m["association_id"] for m in members]

        if skip_locked:
            locked: list[str] = []
            try:
                for assoc in get_group_associations(client, gid):
                    if str(assoc.get("id")) in device_ids and str(assoc.get("device-lock", "")).lower() == "yes":
                        locked.append(str(assoc.get("id")))
            except SdwanApiError:
                pass
            if locked:
                log.warning("Skipping locked devices in %s: %s", group_name, locked)
                device_ids = [d for d in device_ids if d not in locked]

        try:
            associate_devices_to_group(client, gid, device_ids)
            for entry in results:
                if entry.get("config_group") == group_name and entry.get("association_id") in device_ids:
                    entry["stage"] = "associate"
                    entry["ok"] = True
        except SdwanApiError as exc:
            log.error("Associate failed for %s: %s", group_name, exc)
            for entry in results:
                if entry.get("config_group") == group_name:
                    entry["ok"] = False
                    entry["stage"] = "associate"
                    entry["error"] = str(exc)
            continue

        var_payload = [
            {"device-id": m["association_id"], "variables": m["variables"]} for m in members
        ]
        try:
            set_group_device_variables(client, gid, sol, var_payload)
            for entry in results:
                if entry.get("config_group") == group_name and entry.get("association_id") in device_ids:
                    entry["stage"] = "variables"
        except SdwanApiError as exc:
            log.error("Variables PUT failed for %s: %s", group_name, exc)
            for entry in results:
                if entry.get("config_group") == group_name:
                    entry["ok"] = False
                    entry["stage"] = "variables"
                    entry["error"] = str(exc)
            continue

        if not deploy:
            for entry in results:
                if entry.get("config_group") == group_name and entry.get("ok"):
                    entry["stage"] = "variables-only"
            continue

        try:
            deploy_resp = deploy_config_group(client, gid, device_ids)
            parent_task = deploy_resp.get("parentTaskId")
            task_info: dict[str, Any] = {
                "config_group": group_name,
                "config_group_id": gid,
                "parentTaskId": parent_task,
                "device_ids": device_ids,
            }
            if parent_task:
                poll = poll_action_status(
                    client,
                    str(parent_task),
                    timeout_sec=poll_timeout,
                    interval_sec=poll_interval,
                )
                task_info["poll"] = poll
            deploy_tasks.append(task_info)
            for entry in results:
                if entry.get("config_group") == group_name and entry.get("association_id") in device_ids:
                    entry["stage"] = "deploy"
                    entry["parentTaskId"] = parent_task
                    if parent_task and task_info.get("poll", {}).get("success") is False:
                        entry["ok"] = False
                        entry["error"] = task_info["poll"].get("summary", "deploy task failed")
            for did in device_ids:
                v = verify_association_deployed(client, gid, did)
                for entry in results:
                    if entry.get("association_id") == did:
                        entry["verification"] = v
                        if deploy and not v.get("deployed_ok"):
                            entry["ok"] = False
                            entry["error"] = v.get("configStatusMessage") or v.get("error", "deploy verification failed")
        except SdwanApiError as exc:
            log.error("Deploy failed for %s: %s", group_name, exc)
            for entry in results:
                if entry.get("config_group") == group_name:
                    entry["ok"] = False
                    entry["stage"] = "deploy"
                    entry["error"] = str(exc)

    return {
        "mode": "csv-apply",
        "csv": str(csv_path),
        "groups": group_meta,
        "deploy_tasks": deploy_tasks,
        "results": results,
    }


def main() -> int:
    """
    CLI entry point: parse args, authenticate, run discover or CSV workflow, emit JSON report.

    Confirmation guardrails (exit 2 if violated):
    - ``--apply`` requires ``--confirm-apply``
    - ``--deploy`` requires ``--confirm-deploy`` and ``--apply``

    Returns:
        Exit code 0, 1, or 2 (see module docstring).
    """
    p = argparse.ArgumentParser(
        description="UX 2.0 config group CSV onboard: discover, associate, variables, deploy, verify"
    )
    p.add_argument("--discover-unassigned", action="store_true", help="List reachable devices not in any config group")
    p.add_argument(
        "--output-csv",
        type=Path,
        help="With --discover-unassigned, write a CSV template to this path",
    )
    p.add_argument(
        "--template-group",
        help="With --output-csv, pre-fill config_group name and variable columns from this group",
    )
    p.add_argument("--csv", type=Path, help="Input CSV (serial_number, config_group, variable columns)")
    p.add_argument("--dry-run", action="store_true", help="Validate CSV and inventory matches only")
    p.add_argument("--apply", action="store_true", help="Associate devices and set variables from CSV")
    p.add_argument("--confirm-apply", action="store_true", help="Required with --apply")
    p.add_argument("--deploy", action="store_true", help="After apply, deploy config groups to CSV devices")
    p.add_argument("--confirm-deploy", action="store_true", help="Required with --deploy")
    p.add_argument(
        "--solution",
        choices=["sdwan", "sd-routing", "all"],
        default="all",
        help="Filter configuration groups by solution",
    )
    p.add_argument("--output", type=Path, help="Write JSON report to file")
    p.add_argument("--tenant", help="Provider-as-tenant: activate VSessionId for this tenant")
    p.add_argument("--poll-timeout", type=float, default=900.0, help="Deploy task poll timeout (seconds)")
    p.add_argument("--poll-interval", type=float, default=15.0, help="Deploy task poll interval (seconds)")
    p.add_argument("--skip-locked", action="store_true", help="Skip devices with device-lock Yes")
    args = p.parse_args()

    if args.apply and not args.confirm_apply:
        log.error("Refusing --apply without --confirm-apply")
        return 2
    if args.confirm_apply and not args.apply:
        log.error("--confirm-apply requires --apply")
        return 2
    if args.deploy and not args.confirm_deploy:
        log.error("Refusing --deploy without --confirm-deploy")
        return 2
    if args.confirm_deploy and not args.deploy:
        log.error("--confirm-deploy requires --deploy")
        return 2
    if args.deploy and not args.apply:
        log.error("--deploy requires --apply (associate and variables first)")
        return 2

    if not args.discover_unassigned and not args.csv:
        log.error("Specify --discover-unassigned or --csv")
        return 2

    settings = Settings.load()
    report: dict[str, Any]

    with ManagerClient(settings) as client:
        client.login()
        tenant_key = args.tenant or settings.tenant_name or settings.tenant_subdomain
        if tenant_key:
            client.activate_tenant_context(tenant_key)

        if args.discover_unassigned:
            report = run_discover(
                client,
                solution=args.solution,
                output_csv=args.output_csv,
                template_group=args.template_group,
            )
        else:
            assert args.csv is not None
            report = run_csv(
                client,
                csv_path=args.csv,
                solution=args.solution,
                dry_run=args.dry_run or not args.apply,
                apply=args.apply,
                deploy=args.deploy,
                skip_locked=args.skip_locked,
                poll_timeout=args.poll_timeout,
                poll_interval=args.poll_interval,
            )

    failures = 0
    if report.get("results"):
        failures = sum(1 for r in report["results"] if not r.get("ok"))

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)

    if failures:
        log.error("%d row(s) failed", failures)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
