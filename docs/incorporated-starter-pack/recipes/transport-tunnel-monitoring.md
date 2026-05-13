# Transport and Tunnel Monitoring

## Dashboard Question

Which underlay transports and overlay tunnels are down, degraded, or violating SLA?

## API Sequence

Current state:

1. `GET /device/bfd/summary?deviceId={system-ip}`
2. `GET /device/bfd/sessions?deviceId={system-ip}`
3. For scale: `GET /data/device/state/BFDSessions?count={count}` with pagination.

Historical metrics:

1. `POST /statistics/approute/fec/aggregation`
2. `GET /statistics/interface/type?query={query}`

## Recommended Metrics

- Tunnel state.
- Local color and remote color.
- Local and remote system IP.
- Loss.
- Latency.
- Jitter.
- vQoE where available.
- Interface RX/TX kbps and capacity percentage.

## Best Practices

- Use BFD sessions for current tunnel state.
- Use app-route aggregation for historical SLA charts.
- Use interface statistics for underlay throughput and drops.
- Normalize tunnel keys so a tunnel can be tracked across polling intervals.
- Alert on business impact: one transport down may be warning; all transports down for a site is critical.

## Scale Notes

For large deployments, avoid per-device tunnel polling as the only method. Use bulk state APIs where possible, paginate until `moreEntries` is false, and reserve per-device APIs for drill-down.

