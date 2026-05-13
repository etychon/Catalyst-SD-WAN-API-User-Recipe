# Cellular Monitoring

## Dashboard Question

Which cellular links are available, usable, weak, or failing, and how should signal thresholds be customized?

## API Sequence

1. `GET /device/cellular/status?deviceId={system-ip}`
2. `GET /device/cellularEiolte/radio?deviceId={system-ip}`
3. Optional interface trend: `GET /statistics/interface/type?query={query}` filtered to cellular interfaces.

## Recommended Fields

- `if-name` or `cellular-interface-name`
- `modem-status`
- `sim-status`
- `network-status`
- `Radio-Status`
- `RAT-Selected`
- `RSRP`
- `RSRQ`
- `RSSI`
- `SNR` or `Measured-ENDC-SINR`
- Band and bandwidth where useful

## Custom Thresholds

Do not blindly reuse generic excellent/good/fair/poor labels. They are often too coarse for OT and transport failover decisions.

Suggested LTE starting points:

| Metric | Excellent | Good | Fair | Poor |
| --- | --- | --- | --- | --- |
| RSRP | `>= -80 dBm` | `-90 to -81 dBm` | `-100 to -91 dBm` | `< -100 dBm` |
| RSRQ | `>= -10 dB` | `-15 to -10 dB` | `-20 to -15 dB` | `< -20 dB` |
| SINR/SNR | `>= 20 dB` | `13 to 19 dB` | `0 to 12 dB` | `< 0 dB` |

Tune by carrier, antenna, device model, geography, and business impact.

## Best Practices

- Display both status and radio quality. A modem can be online with weak radio quality.
- Track cellular quality over time; one weak sample should not cause a critical alarm.
- Show customer-specific thresholds in dashboard configuration, not hard-coded source.
- Keep SIM identifiers and carrier-sensitive data protected.

## Example

See [samples/scripts/collect_dashboard_snapshot.py](../../samples/scripts/collect_dashboard_snapshot.py).

