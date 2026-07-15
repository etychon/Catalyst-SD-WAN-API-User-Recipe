---
title: Inventory status (sync, configuration groups)
release: "20.18"
tags: [inventory, config-sync, configuration-groups, compliance]
apis:
  - /dataservice/device
  - /dataservice/device/config/status
  - /dataservice/template/device/config/attached
  - /dataservice/device/config/group
related_script: samples/scripts/inventory_status.py
---

# Inventory status (in sync, out of sync, configuration group)

> **UX 2.0 vs classic:** This recipe probes **legacy / mixed** dataservice endpoints (templates, `/dataservice/device/config/group`). It does **not** implement the UX 2.0 configuration group workflow. For listing groups by solution, per-group device association, drift, and deploy, use **[config-group-ux2-sync-deploy.md](config-group-ux2-sync-deploy.md)** and [samples/scripts/config_group_ux2.py](../../samples/scripts/config_group_ux2.py).

## Outcome

Widgets that show **configuration compliance**, **attachment to templates or configuration groups**, and **high-level sync state** alongside inventory.

## Data sources

The exact combination depends on whether the deployment uses **classic templates**, **configuration groups**, or hybrid models. Candidate read APIs (names vary — confirm in OpenAPI):

- `GET /dataservice/device` — baseline status fields such as `templateStatus` when present.
- `GET /dataservice/device/config/status` — config sync style health (may 404 if unused).
- `GET /dataservice/template/device/config/attached` — template attachment views.
- `GET /dataservice/device/config/group` — configuration group association where enabled.

## Orchestration

1. Load devices.
2. Call each **optional** status endpoint once (not per device) when the API is global; otherwise follow OpenAPI for per-device filters.
3. Join in your ETL using stable device keys.

## Field mapping

Document your deployment’s truth: UI labels like “Out of sync” map to specific enum values in JSON. Capture a **golden sample** from a lab Manager and store it with your integration tests (redacted).

## Edge cases

- Mixed modes during migration from templates to configuration groups.
- Partial permissions: users see a subset of devices; compliance views must not leak hidden devices via creative joins.

## Sample

```bash
python scripts/inventory_status.py
```

Source: [samples/scripts/inventory_status.py](../../samples/scripts/inventory_status.py)

---

## In plain language

Answers: **Is device configuration in sync?** (Legacy / template environments.) Use when you still rely on **classic device templates** or a mixed migration state — not for UX 2.0-only config groups.

## Where to go next

- [UX 2.0 config groups](config-group-ux2-sync-deploy.md)
- [Concepts — UX 1.0 vs 2.0](../concepts.md#ux-10-templates-vs-ux-20-configuration-groups)
- [Device inventory](inventory-devices.md)

## Technical details

- [API selection — legacy status row](../api-selection-guide.md)
- [Security — read-only RBAC](../security-rbac-secrets.md)
