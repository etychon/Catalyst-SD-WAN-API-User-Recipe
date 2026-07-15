# API Selection Guide

Use this guide to choose SD-WAN Manager APIs for monitoring dashboards.

> **Non-API readers:** start with [concepts.md](concepts.md) and [recipes/README.md](recipes/README.md). Return here when you are ready to pick exact endpoints for a collector.

**Path convention:** Unless a path already starts with `/dataservice`, the Manager serves REST APIs under the **`/dataservice`** prefix (for example `GET /dataservice/device`). The “Endpoint map” table below uses short paths (for example `GET /device`) meaning **`GET /dataservice/device`** in this repository’s samples.

## Authentication

Preferred patterns:

- Release 20.18.1 and later: JWT login using `POST /jwt/login`, then send `Authorization: Bearer <token>` and `X-XSRF-TOKEN` for mutating requests.
- Backward compatible: session login using `POST /j_security_check`, retrieve XSRF token with `GET /dataservice/client/token`, then reuse the same session for chained calls.
- For read-only dashboard collectors, use GET and POST query APIs with a least-privilege API user.

Avoid:

- Storing credentials in scripts, YAML, `.env` files committed to Git, or dashboard frontend code.
- Creating one login session per API call. Cisco documents session reuse and session limits; collectors should authenticate once per run and reuse the session.

## Endpoint Map

| Use case | Primary endpoints | Notes |
| --- | --- | --- |
| Overlay inventory | `GET /device`, `GET /system/device/{deviceCategory}` | `/device` is useful for connected overlay inventory, system IP, hostname, site ID, reachability, latitude, longitude, and status. `/system/device/vedges` and controller categories expose config status and management metadata. |
| Device inventory status (legacy / mixed) | `GET /device/status`, `GET /system/device/vedges`, `GET /template/device/config/attached` | Template and vedge sync fields; see [inventory-status-config-groups.md](recipes/inventory-status-config-groups.md). |
| UX 2.0 configuration groups | `GET /v1/config-group?solution=`, `GET /v1/config-group/{configGroupId}/device/associate`, `POST /v1/config-group/{configGroupId}/device/deploy` | List by `solution` (`sdwan`, `sd-routing`); drift via `configGroupUpToDate`; deploy requires write RBAC. See [config-group-ux2-sync-deploy.md](recipes/config-group-ux2-sync-deploy.md). **Classic templates not supported.** |
| Health summary | `GET /health/devices` | Good dashboard entry point for CPU, memory, health, reachability, control connections, BFD sessions, OMP peers, and coordinates. |
| Real-time device health | `GET /device/system/status?deviceId=...`, `GET /device/counters?deviceId=...`, `GET /device/bfd/summary?deviceId=...` | Use when an operator drills into one device. |
| Interfaces and IPs | `GET /device/interface?deviceId=...`, `GET /statistics/interface/type?query=...` | Use real-time interface state for current view and statistics for time-series traffic. |
| Tunnels and transport | `GET /device/bfd/sessions?deviceId=...`, `GET /device/bfd/summary?deviceId=...`, `GET /data/device/state/BFDSessions?count=...`, `POST /statistics/approute/fec/aggregation` | Use BFD state for current tunnel inventory and app-route statistics for latency, loss, jitter, and tunnel trend charts. |
| Cellular status (live drill-down) | `GET /device/cellular/status?deviceId=...`, `GET /device/cellularEiolte/radio?deviceId=...` | Build your own signal classification from RSRP, RSRQ, RSSI, SINR/SNR rather than relying only on generic excellent/good/fair/poor labels. |
| Cellular signal **over time** (statistics) | `POST /statistics/eiolte/uniqueAggregation` | Aggregated EIOLTE buckets (`header`, `entryTimeList`, `data[]` with `entry_time`, `rsrp`, `rsrq`, `rssi`, slot/SIM, `count`, …). Body must include **`aggregation`** (`field`, `metrics`, `histogram`) on current managers—see [cellular-signal-thresholds.md](recipes/cellular-signal-thresholds.md) for request/response notes and error codes. |
| Site topology and coordinates | `GET /device`, `GET /health/devices` | Prefer Manager-provided latitude/longitude when `isDeviceGeoData` or `has_geo_data` is true. Store manual overrides in your dashboard database. |
| Alarms and events | `POST /alarms`, `GET /events/fields` | Use POST for non-trivial queries and large query strings. |
| Audit logs | `POST /auditlog`, `GET /auditlog/fields` | Pull audit data into a security/audit view with actor, action, severity, object, and timestamp. |

## API Calling Pattern

1. Authenticate once.
2. Pull low-cardinality inventory first.
3. Normalize identifiers:
   - `system-ip`
   - `uuid`
   - `host-name`
   - `site-id`
   - `device-model`
4. For each reachable WAN edge, collect drill-down real-time details with concurrency limits.
5. Collect time-series statistics by query windows, not by one call per chart.
6. Persist raw responses for troubleshooting only when allowed by policy; otherwise persist normalized records.

## Dashboard Design Principle

Do not mirror the SD-WAN Manager UI. Build opinionated views:

- OT workflow view: site health, transport health, cellular signal, alarms, and last known location.
- IT operations view: inventory drift, config status, tunnel status, CPU/memory, and events.
- Multi-cluster executive view: site counts, degraded sites, offline devices, tunnel SLA, and top alarm categories.

## Multi-tenant Manager

If your deployment is **multi-tenant**, provider automation often needs `GET /tenant` and `POST /tenant/{tenantId}/vsessionid` before dataservice reads behave as a specific tenant. Single-tenant clusters ignore this. See [multitenant-clusters.md](multitenant-clusters.md) and [recipes/multitenant-connectivity.md](recipes/multitenant-connectivity.md).

---

## In plain language

This table maps **dashboard questions** (“show device inventory”, “list alarms”) to **Manager API families**. Use it as a lookup while implementing recipes — not as your first read.

## Where to go next

- [Recipes — I want to…](recipes/README.md)
- [Dashboard architecture](dashboard-architecture.md)
- [Authentication](01-auth-and-sessions.md)
- [Glossary](reference/glossary.md)

## Technical details

- [API index — DevNet links](reference/api-index.md)
- [Cisco DevNet — SD-WAN 20.18](https://developer.cisco.com/docs/sdwan/)
