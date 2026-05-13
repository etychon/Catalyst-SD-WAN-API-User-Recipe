# API index — DevNet entry points (20.18)

Use this table as a **curated map** into Cisco DevNet. Endpoint paths and schemas are defined in the official OpenAPI for your exact patch release; validate in your lab.

| Topic | DevNet URL | Typical use in this repo |
|-------|------------|--------------------------|
| Introduction | https://developer.cisco.com/docs/sdwan/ | Orientation |
| Authentication (JWT + session) | https://developer.cisco.com/docs/sdwan/authentication/ | `ManagerClient` login |
| Device model / monitoring | https://developer.cisco.com/docs/sdwan/device/ | Inventory, reachability |
| Full catalog | https://developer.cisco.com/docs/sdwan/ | Search OpenAPI for `dataservice` paths |

## Common `/dataservice` families (illustrative)

Exact paths differ by feature and release patch — confirm in OpenAPI:

- **Devices:** `/dataservice/device`
- **Device interfaces:** paths matching `device/interface` in OpenAPI (used in inventory recipe)
- **Alarms / events:** alarm and event resources under monitoring and troubleshooting sections
- **Configuration attachment / sync:** configuration or template attachment resources for “in sync” semantics

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
