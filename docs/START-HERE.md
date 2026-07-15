# Start here — welcome

**Release focus:** Cisco Catalyst SD-WAN Manager **20.18**. This repository is community reference material, not an official Cisco product. See [DISCLAIMER.md](../DISCLAIMER.md).

You do **not** need API or programming experience to benefit from most of this content. If you can read a short guide and follow a checklist, you are in the right place.

## What you will get from this repo

This repository helps teams answer everyday SD-WAN operations questions **without starting from raw API documentation**:

- **Inventory** — What devices exist? Which sites? Which WAN or cellular links?
- **Health** — What is reachable, degraded, or using too much CPU or memory?
- **Transport and tunnels** — Are underlay links and overlay tunnels healthy?
- **Alarms and audit** — What needs attention right now? Who changed what?
- **Configuration drift** — Which devices are out of sync with their configuration group?
- **Maps and location** — Where are sites on a map? How do you keep history beyond Manager retention?

Each answer is packaged as a **recipe** (a short workflow document). Optional **Python samples** let you try the same workflow in a lab.

## What you do not need

| You do **not** need… | Because… |
|----------------------|----------|
| Deep API knowledge | Recipes explain outcomes first; technical endpoints come later. |
| Python | Reading recipes alone is valid. Scripts are optional for labs. |
| To mirror the Manager UI | We focus on opinionated monitoring views, not a copy of every screen. |
| Cisco support from this repo | See [DISCLAIMER.md](../DISCLAIMER.md); use TAC and DevNet for product support. |

## Three ways to use this repository

1. **Read only** — Open [concepts](concepts.md), pick a [recipe](recipes/README.md), and use it as design input for your dashboard or runbook.
2. **Try in a lab** — Follow the [5-minute lab try](#5-minute-lab-try) below with read-only credentials on a test Manager.
3. **Build an integration** — Read foundation guides (auth, scale, security), then wire recipes into your collector or automation stack.

![Choose your reading path by role](assets/choose-your-path.svg)

## Choose your path

Pick the row that sounds like you, then read the links **in order**.

### Plant / OT operator

Minimal visibility: inventory, cellular, alarms — not full IT depth.

1. [OT minimal pack](recipes/ot-minimal-pack.md)
2. [Device inventory](recipes/inventory-devices.md)
3. [Cellular signal thresholds](recipes/cellular-signal-thresholds.md)
4. [Syslog, alarms, audit](recipes/syslog-alarms-audit-rbac.md)
5. Optional: [Transport / underlay](recipes/transport-underlay-monitoring.md)

### NOC / IT operator

Day-to-day monitoring and troubleshooting views.

1. [Concepts — ideas before APIs](concepts.md)
2. [Device inventory](recipes/inventory-devices.md)
3. [Health, CPU, memory, tunnels](recipes/health-cpu-mem-tunnels.md)
4. [Transport / underlay](recipes/transport-underlay-monitoring.md)
5. [Syslog, alarms, audit](recipes/syslog-alarms-audit-rbac.md)
6. [UX 2.0 config groups — drift and deploy](recipes/config-group-ux2-sync-deploy.md)

### Dashboard or integration architect

Design collectors, data stores, and widgets.

1. [Concepts — ideas before APIs](concepts.md)
2. [Dashboard architecture](dashboard-architecture.md)
3. [API selection guide](api-selection-guide.md)
4. [Data retention](data-retention.md)
5. [Recipes index — by goal](recipes/README.md)

### Automation developer

Run samples and build production collectors.

1. This page — [5-minute lab try](#5-minute-lab-try)
2. [Authentication](01-auth-and-sessions.md)
3. [Security, RBAC, secrets](security-rbac-secrets.md)
4. [Scale and pagination](02-rate-limits-scale.md)
5. [Recipes index](recipes/README.md) and [Python scripts](../README.md#python-scripts-samplesscripts)

### MSP / multi-tenant operator

Provider cluster with multiple customer tenants.

1. [Concepts — multi-tenant summary](concepts.md#multi-tenant-deployments)
2. [Multi-tenant clusters](multitenant-clusters.md)
3. [Multi-tenant connectivity recipe](recipes/multitenant-connectivity.md)
4. [UX 2.0 config groups](recipes/config-group-ux2-sync-deploy.md)

## How this repo is organized

![Repository map](assets/repo-map.svg)

| Part | Location | Who it is for |
|------|----------|---------------|
| **This guide** | `docs/START-HERE.md` | Everyone, first visit |
| **Concepts** | [concepts.md](concepts.md) | Non-API readers |
| **Foundation guides** | `docs/00-overview.md` … `02`, multitenant | Architects and developers |
| **Recipes** | [docs/recipes/](recipes/) | Operators and builders |
| **Extended guides** | Architecture, security, fields, API selection | Design and implementation |
| **Reference** | [Glossary](reference/glossary.md), [API index](reference/api-index.md) | Lookup while building |
| **Samples** | [samples/scripts/](../samples/scripts/) | Lab and CI validation |

## 5-minute lab try

Use a **lab Manager** and a **read-only** service account when possible.

```bash
cd samples
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
```

Edit `.env`:

- Set `SDWAN_BASE_URL` (or `SDWAN_MANAGER`) to your Manager URL.
- Set credentials **or** `SDWAN_JWT_TOKEN` (see [authentication guide](01-auth-and-sessions.md)).
- For multi-tenant provider access, set `SDWAN_TENANT_NAME` if needed.

Run a small inventory pull:

```bash
python scripts/inventory_devices.py --limit 5
```

If that works, try the full recipe smoke test (optional):

```bash
python scripts/smoke_recipes.py
```

**Security:** TLS verification is on by default. Disabling SSL verification is for lab only. Never commit `.env` or live output files.

## Where to go next

- [Concepts — ideas before APIs](concepts.md)
- [Recipes — what do you want to know?](recipes/README.md)
- [Glossary](reference/glossary.md)
- [Roadmap — planned enhancements](ROADMAP.md)
- [Contributing](../CONTRIBUTING.md)

## Technical index

For the full documentation and script tables, see the [README](../README.md#full-reference-index).
