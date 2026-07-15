# Concepts — ideas before APIs

Read this page if you are new to SD-WAN Manager integrations or want plain language before opening endpoint tables.

**Release focus:** 20.18. Not official Cisco documentation — see [DISCLAIMER.md](../DISCLAIMER.md).

## SD-WAN Manager — the control center

**Cisco Catalyst SD-WAN Manager** (often called *vManage* in older docs) is the central system that manages your SD-WAN network. Think of it as the **control center**:

- It knows which **edge devices** (routers at sites) exist.
- It stores **configuration** and **policy** you apply to those devices.
- It collects **health, alarms, and statistics** reported from the field.
- It offers a **web UI** and **programmatic access** (APIs) for automation.

Your custom dashboard or NOC screen is **separate**. It typically **asks the Manager for data** on a schedule, then presents only what your team cares about.

## Edge devices — what is at each site

An **edge** (WAN edge router) runs SD-WAN software at a branch, plant, or hub. It connects site traffic over one or more **WAN transports** (internet, MPLS, LTE/5G, etc.).

The Manager does not replace the edge; it **orchestrates and monitors** it. Status you see in a dashboard is **as reported to the Manager**, which may lag a few minutes behind real time depending on polling and device reachability.

## Monitoring vs configuration

| Activity | Plain meaning | In this repo |
|----------|---------------|--------------|
| **Monitoring** | Read current state: up/down, CPU, tunnels, alarms | Most recipes are read-only |
| **Configuration** | Push or deploy settings to devices | Only where explicitly documented (e.g. UX 2.0 config group **deploy**) |

Deploy-style operations require **stronger permissions**, change control, and confirmation. See [security, RBAC, secrets](security-rbac-secrets.md) before automating writes.

## Recipe, script, and guide — three kinds of content

![Anatomy of a recipe](assets/recipe-anatomy.svg)

| Kind | What it is | Example |
|------|------------|---------|
| **Recipe** | Short workflow: outcome, steps, field hints, edge cases | [inventory-devices.md](recipes/inventory-devices.md) |
| **Script** | Runnable lab example that follows a recipe | `samples/scripts/inventory_devices.py` |
| **Guide** | Cross-cutting design topic (auth, scale, architecture) | [dashboard-architecture.md](dashboard-architecture.md) |

You can use a recipe **without ever running the script**. The script proves the workflow and helps developers copy patterns.

## Overlay, underlay, tunnels, and cellular

Everyday operator questions map to these ideas:

- **Underlay** — The physical or provider link (fiber, DSL, LTE). “Is my internet link up?”
- **Overlay** — The encrypted SD-WAN fabric built on top of underlays. “Are my sites connected via SD-WAN?”
- **Tunnel** — A secured path between edges or to the controller. “Is the tunnel up and within SLA?”
- **Cellular** — A WAN transport via modem; signal strength (RSRP, RSSI, etc.) matters for failover.

Recipes: [transport-underlay-monitoring.md](recipes/transport-underlay-monitoring.md), [health-cpu-mem-tunnels.md](recipes/health-cpu-mem-tunnels.md), [cellular-signal-thresholds.md](recipes/cellular-signal-thresholds.md).

## UX 1.0 templates vs UX 2.0 configuration groups

Manager supports more than one configuration model. This matters for “is my device in sync?” workflows.

| Model | Plain description | Recipe in this repo |
|-------|-------------------|---------------------|
| **Classic device templates (UX 1.0)** | Older template attach/push model | [inventory-status-config-groups.md](recipes/inventory-status-config-groups.md) — legacy probe |
| **Configuration groups (UX 2.0)** | Group-based config for `sdwan` and `sd-routing` solutions | [config-group-ux2-sync-deploy.md](recipes/config-group-ux2-sync-deploy.md) |

If your organization uses UX 2.0 groups, start with the UX 2.0 recipe. The legacy recipe remains for mixed or template-heavy environments.

## What is an API?

An **API** (Application Programming Interface) is a structured way for software to **ask the Manager questions** and get **machine-readable answers** (usually JSON).

Examples in plain terms:

- “List all devices.”
- “For device X, what is CPU usage?”
- “Which alarms are active in the last hour?”

You do not need to memorize URLs to read recipes. When you build a collector, use [API selection guide](api-selection-guide.md) and [Cisco DevNet](https://developer.cisco.com/docs/sdwan/) for exact paths.

Term lookup: [glossary](reference/glossary.md).

## Your data pipeline

Manager is excellent for **operations visibility**, not as a long-term metrics warehouse for every chart you might want.

![Monitoring data flow](assets/monitoring-data-flow.svg)

Typical pattern:

1. **Edges** report state to the Manager.
2. A **collector** (script, scheduler, or ETL job) queries the Manager on a interval.
3. You **store normalized records** in your database or time-series system.
4. Your **dashboard** reads from your store (and optionally calls the Manager for live drill-down).

Long history (for example 30 days of GPS or cellular signal) usually requires **your own retention design**. See [data-retention.md](data-retention.md) and [location-history-retention.md](recipes/location-history-retention.md).

## Multi-tenant deployments

In a **multi-tenant** Manager, one provider platform hosts **multiple customer tenants**. Provider automation often must **select a tenant context** before config-group and some inventory calls behave as expected.

Start with [multitenant-clusters.md](multitenant-clusters.md) and [multitenant-connectivity.md](recipes/multitenant-connectivity.md).

---

## In plain language

This page explains the building blocks — Manager, edges, recipes, and data flow — so you can read workflow docs without API jargon.

## Where to go next

- [Start here — guided tour](START-HERE.md)
- [Recipes — by goal](recipes/README.md)
- [Overview — technical polling patterns](00-overview.md)
- [Dashboard architecture](dashboard-architecture.md)

## Technical details

- [Authentication](01-auth-and-sessions.md)
- [API selection guide](api-selection-guide.md)
- [Glossary](reference/glossary.md)
