---
title: OT minimal monitoring pack
release: "20.18"
tags: [ot, minimal, starter, alarms, inventory, cellular]
apis:
  - /dataservice/device
  - /dataservice/alarms
related_script: samples/scripts/inventory_devices.py
---

# OT minimal pack (simple custom workflows)

## Audience

OT teams that want **only** inventory, connectivity, cellular health, and alarms — not full IT feature depth.

## Recommended recipe order

1. [inventory-devices.md](inventory-devices.md) — know what exists and whether WAN interfaces are present.
2. [cellular-signal-thresholds.md](cellular-signal-thresholds.md) — numeric RF and custom bands.
3. [syslog-alarms-audit-rbac.md](syslog-alarms-audit-rbac.md) — operational signals with least-privilege service accounts.
4. Optional: [transport-underlay-monitoring.md](transport-underlay-monitoring.md) — when physical WAN diversity matters.

## Implementation tips

- Poll **less frequently** than IT NOC defaults unless troubleshooting.
- Prefer **large, readable tiles** and explicit “data as of” timestamps.
- Keep credentials in plant-approved vaults; see [../01-auth-and-sessions.md](../01-auth-and-sessions.md).

## Starter scripts

- [samples/scripts/inventory_devices.py](../../samples/scripts/inventory_devices.py)
- [samples/scripts/cellular_thresholds.py](../../samples/scripts/cellular_thresholds.py)
- [samples/scripts/alarms_events.py](../../samples/scripts/alarms_events.py)
