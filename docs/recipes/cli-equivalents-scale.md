---
title: CLI-style operational views at scale
release: "20.18"
tags: [cli, livedata, troubleshooting, scale]
apis:
  - /dataservice/device
  - /dataservice/device/system/properties
  - /dataservice/device/system/status
related_script: samples/scripts/cli_bulk_demo.py
---

# “Show command” style views and customization at scale

## Outcome

Provide operators **focused operational snapshots** (similar to selective `show` output) without clicking through the full Manager UI, while controlling **load** and **RBAC**.

## Approach

1. **Prefer read-only statistics and inventory APIs** documented in OpenAPI for your release.
2. Use **device-scoped GET** endpoints where available (the sample tries `device/system/properties` and `device/system/status` with `deviceId`).
3. For true **interactive CLI**, Cisco exposes device action workflows in some releases — these may be **sensitive** and **non-idempotent**; require architecture review, strict allow-lists, and human approval before automation.

## Scale controls

- Default **dry-run** mode lists targets without calling downstream APIs.
- With `--execute`, the sample performs **sequential** GETs to avoid client threading hazards and Manager overload.
- Cap devices (`--limit`) during design; later use tiered schedules and caching.

## Sample

```bash
python scripts/cli_bulk_demo.py
python scripts/cli_bulk_demo.py --execute --limit 10
```

Source: [samples/scripts/cli_bulk_demo.py](../../samples/scripts/cli_bulk_demo.py)

---

## In plain language

Answers: **How do we run operational checks across many devices safely?** Read-only bulk diagnostics at scale, with dry-run defaults so you do not accidentally change devices.

## Where to go next

- [Device inventory](inventory-devices.md)
- [Health and tunnels](health-cpu-mem-tunnels.md)
- [Scale guide](../02-rate-limits-scale.md)

## Technical details

- [Security — agent guardrails](../security-rbac-secrets.md)
- [Authentication](../01-auth-and-sessions.md)
