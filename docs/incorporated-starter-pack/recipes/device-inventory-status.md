# Device Inventory Status

## Dashboard Question

Which devices are in sync, out of sync, unmanaged, locked, or assigned to configuration groups?

## API Sequence

1. `GET /system/device/vedges`
2. `GET /system/device/controllers`
3. Optional for UX 2.0 environments: `GET /v1/config-group/{configGroupId}` when a device record exposes a config group ID or name.

## Recommended Status Model

| Dashboard state | Source fields |
| --- | --- |
| In sync | `configStatusMessage = In Sync`, `templateStatus = Success` |
| Out of sync | `configStatusMessage` contains sync drift or failure wording |
| Config group managed | `managed-by` starts with `Config-Group` or config group fields are populated |
| Template managed | `template` is populated |
| CLI/unmanaged | `configOperationMode = cli` and no template/config group assignment |
| Locked | `device-lock = Yes` |

## Best Practices

- Show both operational reachability and configuration status. A device can be reachable and out of sync.
- Preserve the raw `configStatusMessageDetails` for drill-down views.
- In multi-cluster dashboards, include `cluster_id` in every status record.

## Example

The dashboard snapshot script collects device inventory and can be extended to call `/system/device/vedges` for detailed configuration state.

