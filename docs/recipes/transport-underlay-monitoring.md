---
title: Transport and underlay monitoring
release: "20.18"
tags: [underlay, wan, interfaces, transport]
apis:
  - /dataservice/device
  - /dataservice/device/interface
related_script: samples/scripts/transport_underlay.py
---

# Transport and underlay monitoring

## Outcome

Understand **physical/logical WAN interfaces** (fiber, copper, cellular modem) distinct from **overlay** tunnels, and relate them to carriers and availability.

## Data sources

- **Device list** for context.
- **Interface inventory** via `GET /dataservice/device/interface?deviceId=...` — filter client-side for WAN-facing interface naming patterns (illustrative filter in the sample; tune per platform).

Overlay performance (application routes, VPN) uses different **statistics** families; consult OpenAPI for `approute`, `fec`, `tunnel`, as needed.

## Orchestration

1. Inventory devices.
2. Pull interfaces per device (bounded concurrency with backoff at scale).
3. Classify interfaces using allow-listed patterns from your engineering team (avoid naive string contains in security-sensitive contexts).

## Edge cases

- **Virtual interfaces** and **subinterfaces** may not map 1:1 to physical links.
- **Carrier** names may appear only in certain statistics feeds, not interface inventory.

## Sample

```bash
python scripts/transport_underlay.py --limit 10
```

Source: [samples/scripts/transport_underlay.py](../../samples/scripts/transport_underlay.py)
