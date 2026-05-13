---
title: Cellular signal and custom thresholds
release: "20.18"
tags: [cellular, lte, 5g, thresholds, rsrp]
apis:
  - /dataservice/device
  - /dataservice/device/cellular
  - /dataservice/device/interface
related_script: samples/scripts/cellular_thresholds.py
---

# Cellular dashlets and partner-defined thresholds

## Outcome

Reliable **cellular health** widgets using **numeric RF metrics** (for example RSRP) with **your own** excellent/good/fair/poor bands, instead of copying UI bucket semantics that may not match your RF policy or the raw API fields.

## Why UI buckets can disagree with dashboards

The Manager UI may combine multiple metrics, vendor defaults, and presentation thresholds. REST payloads expose **underlying counters** with their own cadence. Always design thresholds on **documented engineering limits** for your deployment and validate against field measurements.

## Data sources

- **Device list** to enumerate candidates.
- **Cellular-specific endpoints** when present (sample tries `/dataservice/device/cellular` and `/dataservice/cellular/devices` — confirm in OpenAPI; 404 is normal if unused).
- **Interface inventory** filtered to `Cellular*` style names as a fallback for coarse status.

## Orchestration

1. Authenticate.
2. For each device, attempt cellular endpoints; always capture HTTP status in your ETL for observability.
3. Parse numeric RSRP/RSRQ/SINR when present; apply **partner bands** in your code (example in script uses illustrative RSRP cutoffs).

## Field mapping

Map actual keys from your hardware — examples include `rsrp`, `RSRP`, or nested modem structures. The sample includes a small heuristic extractor; replace with schema-validated parsing for production.

## Edge cases

- Dual-SIM and modem firmware upgrades can change available fields.
- Polling too frequently can load the Manager and devices; default to multi-minute intervals unless troubleshooting.

## Sample

```bash
python scripts/cellular_thresholds.py --limit 15
```

Source: [samples/scripts/cellular_thresholds.py](../../samples/scripts/cellular_thresholds.py)
