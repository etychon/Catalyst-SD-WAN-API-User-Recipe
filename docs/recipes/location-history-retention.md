---
title: Location history and 30-day retention
release: "20.18"
tags: [location, history, timeseries, retention, etl]
apis:
  - /dataservice/device
related_script: samples/scripts/location_history_demo.py
---

# Location history (30-day stretch) — where to store

## Outcome

Answer **“where was this device over the last 30 days?”** using a **durable history store** you operate, not the Manager alone.

## Architecture

| Layer | Role |
|-------|------|
| **Hot** (minutes) | Poll Manager/device APIs for current coordinates or site linkage for live maps. |
| **Warm** (30 days) | Append-only (or upsert) time series in **your** TSDB, lake, or SIEM — examples: Prometheus remote_write, InfluxDB, TimescaleDB, cloud metrics, or Parquet on object storage with a query engine. |

### Schema sketch (recommended)

| Column | Notes |
|--------|------|
| `ts` | UTC timestamp of observation |
| `cluster_id` | When using multiple Managers |
| `device_id` | Stable key (`uuid` / `system-ip` — pick one canonical) |
| `site_id` | Optional |
| `latitude`, `longitude` | Nullable |
| `accuracy_m` | Optional |
| `source` | `api`, `gps`, `manual`, etc. |

Use an **idempotent** upsert key such as `(cluster_id, device_id, ts_bucket)` if you poll on a schedule.

## Manager API role

`GET /dataservice/device` may include coordinates for some deployments; others rely on external GIS. The Manager is generally **not** a long-retention analytics database — export metrics on a schedule.

## Sample (demo only)

The bundled SQLite collector illustrates **append-only snapshots** for learning. For >20k devices, move to a managed TSDB with compaction, retention policies, and access control.

```bash
python scripts/location_history_demo.py --db ./demo.sqlite3
```

Source: [samples/scripts/location_history_demo.py](../../samples/scripts/location_history_demo.py)
