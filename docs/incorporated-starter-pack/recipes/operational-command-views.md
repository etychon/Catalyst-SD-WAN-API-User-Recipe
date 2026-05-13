# Operational Command Views

## Dashboard Question

How can partners provide useful "show command" style status views at scale without exposing every CLI command or scraping text output?

## Recommendation

Build curated operational views from real-time SD-WAN Manager APIs. Use raw device CLI commands only for break-glass troubleshooting, because text output is harder to normalize, harder to secure, and less reliable at scale.

## API Sequence

Common views:

| View | Endpoints |
| --- | --- |
| Interface status | `GET /device/interface?deviceId={system-ip}` |
| System status | `GET /device/system/status?deviceId={system-ip}` |
| Control connections | `GET /device/control/connections?deviceId={system-ip}` |
| BFD tunnel sessions | `GET /device/bfd/sessions?deviceId={system-ip}` |
| BFD summary | `GET /device/bfd/summary?deviceId={system-ip}` |
| OMP peers | `GET /device/omp/peers?deviceId={system-ip}` |
| Cellular modem/SIM | `GET /device/cellular/status?deviceId={system-ip}` |
| Cellular radio | `GET /device/cellularEiolte/radio?deviceId={system-ip}` |

## Best Practices

- Design one dashboard view per operational question, not one tab per CLI command.
- Normalize fields and labels so the same view works across device models.
- Rate-limit drill-down calls and avoid collecting every real-time view for every device every minute.
- Cache drill-down results briefly, for example 30-120 seconds, to avoid repeated calls when multiple users inspect the same device.
- Redact secrets and identifiers that are not needed by the target audience.

## Scale Pattern

1. Use bulk inventory and health APIs to identify candidate devices.
2. Use bulk state/statistics APIs where available for fleet-wide status.
3. Use real-time device APIs only when a user opens a site or device drill-down.
4. Store the normalized response for short-lived dashboard cache, not as a long-term system of record unless required.

