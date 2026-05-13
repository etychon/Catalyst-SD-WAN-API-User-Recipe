# Device Health

## Dashboard Question

Which devices are unhealthy, and why?

## API Sequence

1. `GET /health/devices`
2. For selected devices:
   - `GET /device/system/status?deviceId={system-ip}`
   - `GET /device/counters?deviceId={system-ip}`
   - `GET /device/bfd/summary?deviceId={system-ip}`

## Recommended Health Signals

- Reachability
- Health color
- CPU load
- Memory utilization
- Control connections up versus total
- BFD sessions up versus total
- OMP peers up versus total
- Active alarms

## Dashboard Rules

Use customer-tunable thresholds:

| Signal | Warning | Critical |
| --- | --- | --- |
| CPU | `>= 75%` for 10 minutes | `>= 90%` for 5 minutes |
| Memory | `>= 75%` | `>= 90%` |
| Control connections | Below expected count | Zero up |
| BFD sessions | Any down for primary transports | All tunnels down for site |
| Reachability | Intermittent | Unreachable |

## Best Practices

- Prefer trend-based alerts over one-sample spikes.
- Join health with alarms so operators see cause and effect in one view.
- Keep OT views simple: site normal/degraded/offline plus the top reason.

## Example

See [samples/scripts/collect_dashboard_snapshot.py](../../samples/scripts/collect_dashboard_snapshot.py).

