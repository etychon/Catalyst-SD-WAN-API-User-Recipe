# Location History

## Dashboard Question

How can we track device/site location for 30 days?

## Recommendation

Store location samples in the dashboard platform, not only in SD-WAN Manager.

## API Sequence

1. `GET /device`
2. `GET /health/devices`
3. Persist coordinates and source in a location-history table.

## Data Model

```json
{
  "cluster_id": "prod-eu-1",
  "device_id": "uuid",
  "system_ip": "10.10.10.10",
  "site_id": "1001",
  "latitude": 37.666684,
  "longitude": -122.777023,
  "source": "manager_geo",
  "collected_at": "2026-05-13T12:00:00Z"
}
```

## Best Practices

- Keep 30 days at native collection resolution if movement matters.
- Downsample older samples.
- Record whether coordinates came from Manager, CMDB, manual override, or GPS feed.
- Review privacy and safety requirements before storing precise movement history.

