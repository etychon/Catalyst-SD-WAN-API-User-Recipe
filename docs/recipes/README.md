# Recipes index

Version: **20.18** ([DevNet](https://developer.cisco.com/docs/sdwan/)).

**New to this repo?** Read [START-HERE](../START-HERE.md) and [concepts](../concepts.md) first — no API knowledge required.

![Anatomy of a recipe](../assets/recipe-anatomy.svg)

## I want to…

| I want to… | Start here |
|------------|------------|
| Get a minimal OT monitoring set | [ot-minimal-pack.md](ot-minimal-pack.md) |
| See what devices and interfaces exist | [inventory-devices.md](inventory-devices.md) |
| Know if devices are reachable | [inventory-devices.md](inventory-devices.md) (reachability fields) |
| Check config sync (legacy / templates) | [inventory-status-config-groups.md](inventory-status-config-groups.md) |
| List UX 2.0 config groups, find drift, deploy | [config-group-ux2-sync-deploy.md](config-group-ux2-sync-deploy.md) |
| Monitor CPU, memory, and tunnels | [health-cpu-mem-tunnels.md](health-cpu-mem-tunnels.md) |
| Put sites on a map (GPS / coordinates) | [topology-location-gps.md](topology-location-gps.md) |
| Monitor WAN / underlay links | [transport-underlay-monitoring.md](transport-underlay-monitoring.md) |
| Track cellular signal quality | [cellular-signal-thresholds.md](cellular-signal-thresholds.md) |
| Keep location or signal history beyond Manager retention | [location-history-retention.md](location-history-retention.md) |
| Surface alarms, events, and audit logs | [syslog-alarms-audit-rbac.md](syslog-alarms-audit-rbac.md) |
| Operate a multi-tenant (MSP) Manager | [multitenant-connectivity.md](multitenant-connectivity.md) |
| Run CLI-style checks at scale (read-only) | [cli-equivalents-scale.md](cli-equivalents-scale.md) |

## All recipes (summary)

| Recipe | Summary |
|--------|---------|
| [ot-minimal-pack.md](ot-minimal-pack.md) | OT-focused starter path |
| [inventory-devices.md](inventory-devices.md) | Devices, interfaces, IPs |
| [inventory-status-config-groups.md](inventory-status-config-groups.md) | Legacy sync probe (templates / mixed) |
| [config-group-ux2-sync-deploy.md](config-group-ux2-sync-deploy.md) | UX 2.0 config groups: list, drift, deploy |
| [health-cpu-mem-tunnels.md](health-cpu-mem-tunnels.md) | Health and tunnel stats |
| [topology-location-gps.md](topology-location-gps.md) | Sites and coordinates |
| [transport-underlay-monitoring.md](transport-underlay-monitoring.md) | WAN / underlay |
| [cellular-signal-thresholds.md](cellular-signal-thresholds.md) | Cellular + custom bands |
| [location-history-retention.md](location-history-retention.md) | 30-day retention architecture |
| [syslog-alarms-audit-rbac.md](syslog-alarms-audit-rbac.md) | Events and governance |
| [cli-equivalents-scale.md](cli-equivalents-scale.md) | Operational views at scale |
| [multitenant-connectivity.md](multitenant-connectivity.md) | Provider vs tenant, `VSessionId`, tenant list probe |

## Foundation and extended guides

Foundation: [../00-overview.md](../00-overview.md), [../01-auth-and-sessions.md](../01-auth-and-sessions.md), [../02-rate-limits-scale.md](../02-rate-limits-scale.md), [../multitenant-clusters.md](../multitenant-clusters.md).

Extended: [../api-selection-guide.md](../api-selection-guide.md), [../dashboard-architecture.md](../dashboard-architecture.md), [../data-retention.md](../data-retention.md), [../security-rbac-secrets.md](../security-rbac-secrets.md), [../field-dictionary-device-health.md](../field-dictionary-device-health.md).

Original starter-pack text: [../incorporated-starter-pack/README.md](../incorporated-starter-pack/README.md).

---

## In plain language

Pick a row under **I want to…** above when you know your goal. Each recipe explains what question it answers before any API detail.

## Where to go next

- [START-HERE](../START-HERE.md)
- [Concepts](../concepts.md)
- [Glossary](../reference/glossary.md)
