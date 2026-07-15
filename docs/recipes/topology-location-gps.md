---
title: Topology and location (GPS vs manual)
release: "20.18"
tags: [topology, gps, site, map]
apis:
  - /dataservice/site
  - /dataservice/sites
  - /dataservice/device
related_script: samples/scripts/topology_location.py
---

# Site and device topology (GPS or manual coordinates)

## Outcome

Map-centric views: **where devices are**, grouped by **site**, using **GPS** when available or **manual coordinates** maintained by operations.

## Data sources

- **Sites:** try `GET /dataservice/site` or `GET /dataservice/sites` (deployment differences are common).
- **Devices:** `GET /dataservice/device` — may include `site-id` and sometimes location fields; many deployments enrich location via external GIS.

## Orchestration

1. Discover which site endpoint exists (sample tries both).
2. Merge site list with devices on `site-id` (or equivalent).
3. Prefer **device-reported GPS** for moving assets (cellular vehicles) and **site fixed coordinates** for branches when that matches your operational model.

## Field mapping (illustrative)

| Concept | Where it may appear |
|---------|---------------------|
| Site name | Site object or device-derived |
| Latitude / longitude | Device row, site row, or not present (then use CMDB/GIS) |

## Edge cases

- Missing coordinates: do not fabricate; show “unknown” and drive workflow to update CMDB.
- Privacy: coordinate exposure may be sensitive; apply RBAC and data minimization.

## Sample

```bash
python scripts/topology_location.py
```

Source: [samples/scripts/topology_location.py](../../samples/scripts/topology_location.py)

---

## In plain language

Answers: **Where are my sites on a map?** Uses coordinates from the Manager when available; you can override missing locations in your own database.

## Where to go next

- [Location history retention](location-history-retention.md)
- [Device inventory](inventory-devices.md)
- [OT minimal pack](ot-minimal-pack.md)

## Technical details

- [Data retention](../data-retention.md)
- [API selection — topology row](../api-selection-guide.md)
