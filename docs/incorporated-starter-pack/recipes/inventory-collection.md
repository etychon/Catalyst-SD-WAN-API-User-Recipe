# Inventory Collection

## Dashboard Question

Which devices exist, where are they, what interfaces/transports do they have, and which devices have cellular details worth showing?

## API Sequence

1. `GET /device`
2. For each reachable edge device:
   - `GET /device/interface?deviceId={system-ip}`
   - `GET /device/cellular/status?deviceId={system-ip}` when cellular is expected
   - `GET /device/cellularEiolte/radio?deviceId={system-ip}` for richer LTE/5G radio metrics

## Recommended Fields

Device:

- `uuid`
- `system-ip` or `system_ip`
- `host-name` or `name`
- `site-id` or `site_id`
- `device-model`
- `version`
- `reachability`
- `status` or `health`
- `latitude`, `longitude`
- `isDeviceGeoData` or `has_geo_data`

Interface:

- Interface name
- VPN ID
- Admin status
- Operational status
- IP address
- Interface type
- Color/TLOC where available

Cellular:

- Modem status
- SIM status
- Network status
- Signal strength
- RSRP, RSRQ, RSSI, SINR/SNR when available

## Best Practices

- Treat `/device` or `/health/devices` as the top-level inventory seed.
- Normalize field names because some APIs use hyphenated names and others use snake case.
- Store interface inventory separately from device inventory because interface cardinality is higher.
- Do not block the whole inventory run on one device-level API failure.

## Example

See [samples/scripts/collect_dashboard_snapshot.py](../../samples/scripts/collect_dashboard_snapshot.py) in this repository (multi-endpoint snapshot).

