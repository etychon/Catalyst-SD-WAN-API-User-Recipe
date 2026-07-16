# API index — DevNet entry points (20.18)

Use this table as a **curated map** into Cisco DevNet. Endpoint paths and schemas are defined in the official OpenAPI for your exact patch release; validate in your lab.

| Topic | DevNet URL | Typical use in this repo |
|-------|------------|--------------------------|
| Introduction | https://developer.cisco.com/docs/sdwan/ | Orientation |
| Authentication (JWT + session) | https://developer.cisco.com/docs/sdwan/authentication/ | `ManagerClient` login |
| V Session Id (multitenant) | https://developer.cisco.com/docs/sdwan/v-session-id/ | Provider-as-tenant `VSessionId` header |
| Device model / monitoring | https://developer.cisco.com/docs/sdwan/device/ | Inventory, reachability |
| Full catalog | https://developer.cisco.com/docs/sdwan/ | Search OpenAPI for `dataservice` paths |
| Alarms, events, audit (hub) | https://developer.cisco.com/docs/sdwan/alarm-and-event/ | POST query DSL for alarms, events, auditlog |
| Alarm query fields | https://developer.cisco.com/docs/sdwan/get-alarm-query-fields/ | Discover filterable alarm properties |
| Alarm count (POST) | https://developer.cisco.com/docs/sdwan/post-count/ | Count with same query rules |
| Audit severity summary | https://developer.cisco.com/docs/sdwan/get-vmanage-audit-log-histogram/ | Histogram with query parameter |
| User and group (RBAC) | https://developer.cisco.com/docs/sdwan/user-and-group/ | Admin user/group read (governance) |

## Common `/dataservice` families (illustrative)

Exact paths differ by feature and release patch — confirm in OpenAPI:

- **Devices:** `/dataservice/device`
- **Device interfaces:** paths matching `device/interface` in OpenAPI (used in inventory recipe)
- **Alarms / events / audit:** [Alarm and Event](https://developer.cisco.com/docs/sdwan/alarm-and-event/) — recipe [syslog-alarms-audit-rbac.md](../recipes/syslog-alarms-audit-rbac.md)
- **Configuration attachment / sync (legacy):** template attachment resources for classic “in sync” semantics
- **UX 2.0 configuration groups:** [Get Config Group By Solution](https://developer.cisco.com/docs/sdwan/get-config-group-by-solution/), [Get Config Group Association](https://developer.cisco.com/docs/sdwan/get-config-group-association/), [Deploy Config Group](https://developer.cisco.com/docs/sdwan/deploy-config-group/) — recipe [config-group-ux2-sync-deploy.md](../recipes/config-group-ux2-sync-deploy.md)

When a sample script receives `404` or empty data, first verify **RBAC** for the API user, then verify the **feature** is enabled on the platform.

## Extended guides and incorporated starter pack

- [API selection guide](../api-selection-guide.md) — endpoint map by dashboard use case
- [Dashboard architecture](../dashboard-architecture.md)
- [Field dictionary](../field-dictionary-device-health.md)
- [Original starter-pack recipe copies + crosswalk](../incorporated-starter-pack/README.md)

## Related

- [Glossary](glossary.md)
- [Recipes](../recipes/)
- **Multi-cluster merge sketch:** [samples/scripts/federation_demo.py](../../samples/scripts/federation_demo.py) (requires `SDWAN_FEDERATION` JSON in environment).
- **Multi-tenant probe:** [samples/scripts/multitenant_context.py](../../samples/scripts/multitenant_context.py); guide [multitenant-clusters.md](../multitenant-clusters.md).
