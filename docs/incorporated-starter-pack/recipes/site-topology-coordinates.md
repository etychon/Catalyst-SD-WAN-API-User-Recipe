# Site Topology and Coordinates

## Dashboard Question

Where are sites and devices, and how should a topology map be built?

## API Sequence

1. `GET /device`
2. `GET /health/devices`
3. Optional external sources:
   - CMDB
   - GIS platform
   - OT asset inventory
   - Manual dashboard override table

## Coordinate Priority

1. Manual approved override in dashboard database.
2. External CMDB/GIS source.
3. SD-WAN Manager-provided coordinates when `isDeviceGeoData` or `has_geo_data` is true.
4. Site-level default coordinate.
5. Unknown location bucket.

## Best Practices

- Keep site coordinates separate from device coordinates.
- Store a coordinate `source` field.
- Do not infer precise physical location from IP geolocation for OT sites.
- For multiple devices at one site, render one site node and drill into device details.

## Topology Model

Minimum fields:

- `cluster_id`
- `site_id`
- `site_name`
- `latitude`
- `longitude`
- `device_count`
- `site_health`
- `transport_summary`

