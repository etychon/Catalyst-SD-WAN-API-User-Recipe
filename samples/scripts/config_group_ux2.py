#!/usr/bin/env python3
"""
UX 2.0 configuration groups: list groups, members, drift, optional deploy.

See docs/recipes/config-group-ux2-sync-deploy.md

Default: read-only JSON report. Deploy requires --deploy and --confirm-deploy together.
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
from sdwan_recipes.config_group import (
    build_reachability_index,
    deploy_config_group,
    device_reachability,
    get_group_associations,
    is_out_of_sync,
    list_config_groups,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("config_group_ux2")


def _enrich_device(
    assoc: dict[str, Any],
    reach_index: dict[str, dict[str, Any]],
    *,
    reachable_only: bool,
    out_of_sync_only: bool,
) -> dict[str, Any] | None:
    reach = device_reachability(assoc, reach_index)
    row = {
        "id": assoc.get("id"),
        "host-name": assoc.get("host-name") or assoc.get("hostName"),
        "deviceIP": assoc.get("deviceIP"),
        "configStatusMessage": assoc.get("configStatusMessage"),
        "configGroupUpToDate": assoc.get("configGroupUpToDate"),
        "device-lock": assoc.get("device-lock"),
        "addedByRule": assoc.get("addedByRule"),
        "reachability": reach,
        "out_of_sync": is_out_of_sync(assoc),
    }
    if reachable_only and reach != "reachable":
        return None
    if out_of_sync_only and not row["out_of_sync"]:
        return None
    return row


def _build_report(
    client: ManagerClient,
    *,
    solution: str,
    group_id: str | None,
    reachable_only: bool,
    out_of_sync_only: bool,
) -> dict[str, Any]:
    groups = list_config_groups(client, solution=solution)
    if group_id:
        groups = [g for g in groups if str(g.get("id")) == group_id]
        if not groups:
            raise SdwanApiError(f"No config group found with id {group_id!r}")

    inventory = client.dataservice_json("/dataservice/device")
    reach_index = build_reachability_index(inventory)

    report_groups: list[dict[str, Any]] = []
    deploy_candidates: list[tuple[str, str]] = []

    for group in groups:
        gid = str(group.get("id") or "")
        if not gid:
            continue
        try:
            associations = get_group_associations(client, gid)
        except SdwanApiError as exc:
            log.warning("Association fetch failed for %s: %s", gid, exc)
            associations = []

        devices: list[dict[str, Any]] = []
        for assoc in associations:
            enriched = _enrich_device(
                assoc,
                reach_index,
                reachable_only=reachable_only,
                out_of_sync_only=out_of_sync_only,
            )
            if enriched is None:
                continue
            devices.append(enriched)
            if enriched.get("out_of_sync"):
                did = enriched.get("id")
                if did:
                    deploy_candidates.append((gid, str(did)))

        report_groups.append(
            {
                "id": gid,
                "name": group.get("name"),
                "solution": group.get("solution"),
                "state": group.get("state"),
                "numberOfDevices": group.get("numberOfDevices"),
                "numberOfDevicesUpToDate": group.get("numberOfDevicesUpToDate"),
                "devices": devices,
            }
        )

    return {
        "solution_filter": solution,
        "group_count": len(report_groups),
        "groups": report_groups,
        "deploy_candidate_ids_by_group": _candidates_by_group(deploy_candidates),
    }


def _candidates_by_group(pairs: list[tuple[str, str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for gid, did in pairs:
        out.setdefault(gid, []).append(did)
    return out


def main() -> int:
    p = argparse.ArgumentParser(
        description="UX 2.0 config groups: list, drift filter, optional deploy"
    )
    p.add_argument(
        "--solution",
        choices=["sdwan", "sd-routing", "all"],
        default="all",
        help="Filter configuration groups by solution (default: all)",
    )
    p.add_argument("--group-id", help="Limit to one configuration group UUID")
    p.add_argument(
        "--reachable-only",
        action="store_true",
        help="Include only devices with reachability=reachable from GET /device",
    )
    p.add_argument(
        "--out-of-sync-only",
        action="store_true",
        help="Include only devices where configGroupUpToDate indicates drift",
    )
    p.add_argument("--output", type=Path, help="Write JSON report to file")
    p.add_argument(
        "--deploy",
        action="store_true",
        help="After report, POST deploy for filtered out-of-sync devices",
    )
    p.add_argument(
        "--confirm-deploy",
        action="store_true",
        help="Required with --deploy; acknowledges destructive write",
    )
    p.add_argument(
        "--device-ids",
        nargs="*",
        help="Deploy only these device ids (must belong to --group-id when set)",
    )
    p.add_argument(
        "--tenant",
        metavar="NAME_OR_SUBDOMAIN",
        help="Multi-tenant provider: act as this tenant (e.g. emmanuel) via VSessionId",
    )
    args = p.parse_args()

    if args.deploy and not args.confirm_deploy:
        log.error("Refusing deploy without --confirm-deploy")
        return 2
    if args.confirm_deploy and not args.deploy:
        log.error("--confirm-deploy requires --deploy")
        return 2

    settings = Settings.load()
    with ManagerClient(settings) as client:
        client.login()
        tenant_key = args.tenant or settings.tenant_name or settings.tenant_subdomain
        if tenant_key:
            client.activate_tenant_context(tenant_key)
        report = _build_report(
            client,
            solution=args.solution,
            group_id=args.group_id,
            reachable_only=args.reachable_only,
            out_of_sync_only=args.out_of_sync_only,
        )

        if args.deploy:
            _run_deploy(client, report, args.group_id, args.device_ids)

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        log.info("Wrote %s", args.output)
    else:
        print(text)
    return 0


def _run_deploy(
    client: ManagerClient,
    report: dict[str, Any],
    group_id: str | None,
    device_ids: list[str] | None,
) -> None:
    by_group = report.get("deploy_candidate_ids_by_group") or {}
    if group_id:
        if group_id not in by_group and not device_ids:
            log.warning("No deploy candidates for group %s", group_id)
            return
        targets = {group_id: device_ids or by_group.get(group_id, [])}
    else:
        if device_ids:
            raise SystemExit("--device-ids requires --group-id when deploying")
        targets = by_group

    for gid, ids in targets.items():
        if not ids:
            continue
        log.info("Deploying config group %s to %d device(s)", gid, len(ids))
        result = deploy_config_group(client, gid, ids)
        log.info("Deploy response: %s", json.dumps(result))


if __name__ == "__main__":
    raise SystemExit(main())
