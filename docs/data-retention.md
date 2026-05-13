# Data Retention and 30-Day History

This guide was incorporated from a partner starter pack. It complements (and sometimes overlaps) [docs/recipes/location-history-retention.md](recipes/location-history-retention.md) and [docs/02-rate-limits-scale.md](02-rate-limits-scale.md); use all three when designing retention and scale.

## Recommendation

Store dashboard history outside SD-WAN Manager for a 30-day stretch. SD-WAN Manager is the source of truth for network state, but a dashboard should own its monitoring history, normalization, and cross-cluster correlation.

## Storage Pattern

Use three logical stores:

| Store | Data | Retention |
| --- | --- | --- |
| Inventory/config store | Device, site, coordinates, config status, config group, serial, model | Current state plus change history for 90-365 days |
| Time-series store | CPU, memory, interface rates, tunnel SLA, cellular radio metrics | 30-90 days at native resolution, then downsample |
| Event/audit store | Alarms, syslog-derived events, SD-WAN audit logs, RBAC changes | 90-400 days depending on compliance |

## Time-Series Choices

Good fits:

- Prometheus with remote storage for metrics-heavy environments.
- InfluxDB or TimescaleDB for rich time-series queries.
- OpenSearch or Elasticsearch for event and audit search.
- PostgreSQL for smaller deployments where simplicity matters.

## Cardinality Controls

For large deployments:

- Do not store every raw JSON field as a metric label.
- Keep labels bounded: `cluster_id`, `site_id`, `device_id`, `interface`, `color`, `vpn_id`.
- Store verbose raw payloads in object storage only for short-term debugging.
- Downsample old metrics to 5-minute or 1-hour aggregates.

## Location History

For mobile or cellular-heavy sites, persist location samples in a dedicated table:

| Field | Description |
| --- | --- |
| `cluster_id` | SD-WAN Manager source. |
| `device_id` | UUID or stable device ID. |
| `system_ip` | Device system IP. |
| `site_id` | SD-WAN site ID. |
| `latitude` / `longitude` | Manager-provided or manually overridden coordinates. |
| `source` | `manager_geo`, `manual_override`, `external_cmdb`, `gps_feed`. |
| `timestamp` | Collection time. |

Only store movement history when there is a business reason and an approved privacy policy.

