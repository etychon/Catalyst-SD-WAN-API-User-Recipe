---
title: Device health (CPU, memory, tunnel status)
release: "20.18"
tags: [health, cpu, memory, tunnels, statistics]
apis:
  - /dataservice/device
  - /dataservice/device/tunnel
  - /dataservice/device/tunnel/statistics
related_script: samples/scripts/health_tunnels.py
---

# Device health (CPU, memory, tunnel status)

## Outcome

Operational health: **control/data plane indicators**, **resource usage**, and **tunnel statistics** suitable for NOC-style tiles.

## Data sources

- **Device list:** `GET /dataservice/device` — often includes coarse health or reachability; good first signal.
- **Tunnel statistics:** family under `/dataservice/device/tunnel` or `/dataservice/device/tunnel/statistics` (names differ by release patch — the sample tries multiple paths and records HTTP status).

CPU and memory may appear on **system status** or **statistics** families; search the 20.18 OpenAPI for `system` and `statistics` resources and extend the sample once you confirm the paths in your lab.

## Orchestration

1. Authenticate.
2. Fetch devices; choose a bounded subset for deep statistics during pilots.
3. For each device key, attempt tunnel endpoints; store the first successful response or capture errors for operator review.

## Field mapping

Tunnel JSON is highly model-dependent. Build your dashboard against **validated** keys from production-like hardware.

## Edge cases

- **Staleness:** statistics are sampled; show “as of” timestamps from the payload when available.
- **Scale:** avoid querying all devices every minute at full depth; tier devices by criticality.

## Sample

```bash
python scripts/health_tunnels.py --limit 10
```

Source: [samples/scripts/health_tunnels.py](../../samples/scripts/health_tunnels.py)

---

## In plain language

Answers: **Are devices healthy?** **How much CPU and memory are they using?** **Are tunnels up?** Suitable for NOC tiles and escalation workflows.

## Where to go next

- [Device inventory](inventory-devices.md)
- [Transport / underlay](transport-underlay-monitoring.md)
- [Syslog, alarms, audit](syslog-alarms-audit-rbac.md)
- [Field dictionary](../field-dictionary-device-health.md)

## Technical details

- [Dashboard architecture](../dashboard-architecture.md)
- [API selection — health row](../api-selection-guide.md)
- [Scale guide](../02-rate-limits-scale.md)
