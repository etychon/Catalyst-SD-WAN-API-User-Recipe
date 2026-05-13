---
title: Cellular signal and custom thresholds
release: "20.18"
tags: [cellular, lte, 5g, thresholds, rsrp, rssi, statistics, eiolte]
apis:
  - /dataservice/device
  - /dataservice/device/cellular
  - /dataservice/cellular/devices
  - /dataservice/device/interface
  - POST /dataservice/statistics/eiolte/uniqueAggregation
  - GET /dataservice/statistics/eiolte/query/fields
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
- **EIOLTE statistics aggregation** — `POST /dataservice/statistics/eiolte/uniqueAggregation` for **cellular RF and modem context over time** (materialized in the Manager statistics store). Prefer this when you need **trend charts, SLAs, or historical bands** instead of hammering per-device real-time radio APIs on a short interval.

## Time series: `POST /dataservice/statistics/eiolte/uniqueAggregation`

### When to use it

| Goal | Prefer |
| --- | --- |
| Current modem state / “what is true right now” on one edge | `GET /dataservice/device/cellular/status`, `GET /dataservice/device/cellularEiolte/radio` (per device; more expensive at fleet scale). |
| **RSRP/RSRQ/RSSI (and band, RAT, carrier) over hours or days** for charts, rollups, or anomaly detection | **`POST /dataservice/statistics/eiolte/uniqueAggregation`** — one bounded query returns **many time buckets** without a live device pull for every interval. |

The Manager persists EIOLTE samples on a platform-defined cadence; `uniqueAggregation` returns **pre-aggregated buckets** (bucket width and retention are platform-defined). Treat this as the **statistics-plane** source of truth for history, not a substitute for instant break-glass diagnostics.

### Authoritative references (20.18)

Use these DevNet pages as the contract for your Manager patch; field names and required body keys can change between releases.

- **[Unique Aggregation](https://developer.cisco.com/docs/sdwan/unique-aggregation/)** — OpenAPI for `POST /dataservice/statistics/eiolte/uniqueAggregation`: request schema (`query`, **`aggregation`** (required in practice), `size`, …) and a **worked example** request/response.
- **[Get Stat Query Fields — Monitoring Cellular Eiolte](https://developer.cisco.com/docs/sdwan/get-stat-query-fields-monitoring-cellular-eiolte-3103/)** — lists the **query rule properties** this family expects (for 20.18: **`entry_time`** and **`vdevice_name`**, both required in the query-field metadata).

### Request body — what actually works

Observed on **Catalyst SD-WAN Manager 20.18** (validated against live `200 OK` responses and DevNet examples):

1. **`query.condition`**: `"AND"`.
2. **`query.rules`** — order and operators matter for validation and ClickHouse compilation. A **known-good pattern** is:
   - **`entry_time`**: `type` `"date"`, `operator` `"last_n_hours"`, `value` `["<hours>"]` (string hours, e.g. `"48"`).
   - **`vdevice_name`**: `type` `"string"`, `operator` `"in"`, `value` `["<system-ip>"]` — the statistics store keys “device name” as the **system IP string** in many deployments (confirm with your payload; do **not** use `vdevice-id` unless your OpenAPI lists it for this family — it is **not** in the EIOLTE query-fields list for 20.18).
   - **`rssi`**: `type` `"string"`, `operator` `"not_equal"`, `value` `["0"]` — matches DevNet / UI-style filters to drop empty RSSI markers.
   - **`ps_domain`** (optional but common on IR8xx-class LTE): `type` `"string"`, `operator` `"in"`, `value` `["Attached"]` — narrows to attached packet-switched domain; omit or widen if your modems never report `Attached` (see script `--omit-ps-domain-filter` / `--ps-domain`).
3. **`aggregation`** — **required** for a successful query on current managers. Omitting it yields **HTTP 400** with `CLICKHOUSE0001` / *“Missing tag : aggregation”* (not the older `STATS_VALIDATION0001`-only message).
   - **`aggregation.field`**: array of `{ "property": "<name>", "sequence": <n> }` objects. Include the **dimension properties** you need in the result set. A field list that matches working Manager traffic includes (sequences 1–15): `rsrp`, `rsrq`, `mcc`, `mnc`, `carrier`, `rat`, `ps_domain`, `emm_state`, `lteband`, `ltebw`, `lteca`, `active_sim`, `bandclass`, `slot`, **`pci`** (PCI was present in live responses; omit only if your OpenAPI omits it).
   - **`aggregation.metrics`**: array of `{ "property": "<metric>", "type": "avg" }`. Live captures use **`rssi`** with **`avg`** even when the chart also surfaces **`rsrp`** in each bucket row — the backend still returns **`rsrp`** / **`rsrq`** / **`rssi`** per `data[]` object.
   - **`aggregation.histogram`**: `{ "property": "entry_time", "type": "minute", "interval": <int>, "order": "asc" }` — bucket width in minutes (e.g. `30`); tune for resolution vs. load.
4. **`size`**: integer cap on returned buckets (e.g. `10000`); keep aligned with [rate limits](../02-rate-limits-scale.md).

**Environment override** (script `cellular_signal_history.py`): `SDWAN_STATS_DEVICE_FIELD` defaults to **`vdevice_name`** for the device rule’s `field` key. Only change it when your OpenAPI or a capture proves a different property name for this statistics family.

### Common HTTP 400 signatures

| Symptom | Typical cause |
| --- | --- |
| `STATS_VALIDATION0001` / *Invalid query* | Rule uses a **property not allowed** for EIOLTE statistics (e.g. `vdevice-id` instead of `vdevice_name`), or malformed rule types/operators. Cross-check **`GET /dataservice/statistics/eiolte/query/fields`**. |
| `CLICKHOUSE0001` / *Missing tag : aggregation* | Request body is missing the **`aggregation`** object (or it is empty / malformed). Copy the structure from [Unique Aggregation](https://developer.cisco.com/docs/sdwan/unique-aggregation/) examples. |

### Response body — structure for parsers

Successful JSON is suitable for **time-series ingestion** and for **CLI visualization** (see `cellular_signal_history.py`).

Top-level keys commonly include:

| Key | Role |
| --- | --- |
| **`header`** | `generatedOn` (epoch ms), `columns[]` / `fields[]` with `property`, `title`, `dataType` — use as the allow-list for parsing `data[]`. |
| **`entryTimeList`** | Ordered list of **bucket start times** (epoch ms). Useful for alignment; each `data[]` row also carries **`entry_time`**. |
| **`data[]`** | One object per **histogram bucket** (per dimension combination when `slot` / `active_sim` / … vary). Numeric RF and modem context fields match `header` metadata. |

Typical **`data[]`** fields (names from live 20.18 payloads; always reconcile with `header.fields`):

- **Time / volume**: `entry_time` (ms), `count` (samples in the bucket — use for confidence / sparse-bucket handling).
- **RF**: `rsrp`, `rsrq`, `rssi` (dBm-style numbers in captures; treat units per your device docs).
- **RAN context**: `rat`, `lteband`, `ltebw`, `lteca`, `bandclass`, `pci`.
- **Operator**: `carrier`, `mcc`, `mnc` (sensitivity: policy / minimization).
- **Device slice**: `active_sim`, `slot` — **use to split multi-radio / multi-SIM** series in your collector or in the sample sparkline script (one Braille line per `(slot, active_sim)` group).
- **Attach context**: `ps_domain`, `emm_state`.

### How to use the series in a collector

1. Authenticate once; reuse the session or JWT for all statistics POSTs in that run. Statistics POSTs may need **`X-XSRF-TOKEN`** even with Bearer JWT — see [Authentication and sessions](../01-auth-and-sessions.md) and the `ManagerClient` behavior in `samples/src/sdwan_recipes/client.py`.
2. For each **cellular-capable** device (from inventory or interface heuristics), issue **one** `uniqueAggregation` POST per lookback window (or batch if your OpenAPI supports multi-device rules — prefer fewer POSTs).
3. Normalize each `data[]` row into your TSDB: keys = device id + **`slot`** + **`active_sim`** + `entry_time` (plus `pci` / `lteband` if you partition by cell); metrics = `rsrp`, `rsrq`, `rssi`, optional context fields.
4. Apply **partner thresholds** in your analytics layer; store raw numbers, not only colors.
5. Respect [rate limits and backoff](../02-rate-limits-scale.md); wide `last_n_hours` windows and large `size` values are heavier on the statistics service.

### Caveats

- **RBAC**: Statistics POSTs may require different read roles than `GET /device/interface`; capture HTTP status per device.
- **Gaps**: Missing buckets can mean the device was down, not reporting EIOLTE, or retention expired.
- **5G / NR-only fields**: `header.columns` may add NR-specific properties on newer platforms; extend parsers from live payloads, not only from LTE-shaped examples.
- **Trust live OpenAPI + responses** over this recipe when they disagree — this file captures patterns observed in **20.18** field work.

### For AI agents (quick facts)

- Path: `POST /dataservice/statistics/eiolte/uniqueAggregation` (under `/dataservice` base).
- Device scoping rule property for 20.18 EIOLTE query fields: **`vdevice_name`** (not `vdevice-id`); value is often the **system IP** string.
- Body **must** include **`aggregation`** with `field`, `metrics`, and `histogram` (minute histogram on `entry_time` in working examples).
- **`aggregation.metrics`** often uses **`{"property": "rssi", "type": "avg"}`** while response rows still include **`rsrp`**.
- Response: `header`, `entryTimeList`, `data[]`; group time series by **`slot`** + **`active_sim`** when present.
- Sample implementation: `samples/scripts/cellular_signal_history.py` (Braille RSSI sparkline per interface); auth/CSRF patterns in `samples/src/sdwan_recipes/client.py`.

## Orchestration

1. Authenticate.
2. For **spot checks** or drill-down: resolve inventory/interface first; only call cellular device APIs when a cellular-like interface exists (see [samples/scripts/cellular_thresholds.py](../../samples/scripts/cellular_thresholds.py)).
3. For **history / trends**: build the `uniqueAggregation` JSON body per **Request body — what actually works** above (including **`aggregation`**); persist `data[]` as a time series keyed by device + `slot` + `active_sim` + `entry_time`.
4. Parse numeric RSRP/RSRQ/RSSI when present; apply **partner bands** in your code (the sample script uses illustrative RSRP cutoffs for point-in-time interface rows).
5. Always capture HTTP status in your ETL for observability.

## Field mapping

Map actual keys from your hardware — examples include `rsrp`, `RSRP`, or nested modem structures. The sample includes a small heuristic extractor; replace with schema-validated parsing for production. For statistics responses, prefer **`header.fields`** / **`header.columns`** as the allow-list of properties your parser accepts.

## Edge cases

- Dual-SIM and modem firmware upgrades can change available fields.
- Polling too frequently can load the Manager and devices; default to multi-minute intervals unless troubleshooting.
- Do not conflate **live** cellular GETs with **statistics** POSTs: different staleness, different RBAC, different load profile.

## Sample

**Inventory + live-style cellular probes** (per device, gated on cellular interface):

```bash
python scripts/cellular_thresholds.py --limit 15
```

**EIOLTE statistics history** (Braille **RSSI** sparkline from `uniqueAggregation`, **one line per `(slot, active_sim)`**; only devices with a cellular-like interface unless `--assume-cellular`):

```bash
# Example: one edge with cellular (system IP and hostname from your inventory)
python scripts/cellular_signal_history.py --device-id 10.100.5.111 --hours 48

# Or match by hostname substring when scanning up to --limit devices
python scripts/cellular_signal_history.py --hostname-contains IR8140 --hours 24

# If interface names do not match the cellular heuristic but EIOLTE statistics exist:
python scripts/cellular_signal_history.py --device-id 10.100.5.111 --assume-cellular --hours 48

# If statistics POST returns SessionTokenFilter 403 (Bearer vs XSRF mismatch), either:
python scripts/cellular_signal_history.py --device-id 10.100.5.111 --fresh-jwt-login --hours 48
# or set SDWAN_JWT_CSRF from the same /jwt/login JSON as SDWAN_JWT_TOKEN (see docs/01-auth-and-sessions.md).

# Widen or omit ps_domain when modems do not report "Attached":
python scripts/cellular_signal_history.py --device-id 10.100.5.111 --omit-ps-domain-filter --hours 48
python scripts/cellular_signal_history.py --device-id 10.100.5.111 --ps-domain Attached,Idle --hours 48
```

Inventory note: `--device-id` and `--hostname-contains` scan the **full** device list (hostname scan capped by `--scan-limit`, default 5000). Unfiltered mode still uses `--limit` as the inventory prefix cap.

If the statistics POST returns HTTP 400, use the **Common HTTP 400 signatures** table above, then confirm rule field names against **`GET /dataservice/statistics/eiolte/query/fields`** and [Unique Aggregation](https://developer.cisco.com/docs/sdwan/unique-aggregation/) for your patch. Optional override:

```bash
export SDWAN_STATS_DEVICE_FIELD=vdevice_name   # default; change only if OpenAPI names a different device key for EIOLTE
```

Sources:

- [samples/scripts/cellular_thresholds.py](../../samples/scripts/cellular_thresholds.py) — live-style cellular probes.
- [samples/scripts/cellular_signal_history.py](../../samples/scripts/cellular_signal_history.py) — `uniqueAggregation` request builder + per-interface RSSI Braille output.
- [Cisco DevNet — Unique Aggregation](https://developer.cisco.com/docs/sdwan/unique-aggregation/) — canonical request/response shapes.
