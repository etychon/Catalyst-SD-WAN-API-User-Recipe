# Cisco Catalyst SD-WAN Manager — Monitoring recipes (20.18)

<!--
  Machine-readable index: see repo-manifest.json (paths, flags, DevNet hub).
  Agent-oriented rules: see AGENTS.md
  Legal / support stance: see DISCLAIMER.md (not a Cisco initiative; as-is; no support)
-->

**Goal:** Help teams build SD-WAN monitoring views and automations **without starting from raw API documentation** — using plain-language recipes, design guides, and optional lab scripts.

## New here?

Start with **[docs/START-HERE.md](docs/START-HERE.md)** — a guided tour that does not assume API or programming knowledge.

- [Concepts — ideas before APIs](docs/concepts.md)
- [Recipes — find by goal](docs/recipes/README.md)

![How this repository is organized](docs/assets/repo-map.svg)

## Who this is for

| You are… | Start with |
|----------|------------|
| **Operator** (OT or NOC) | [START-HERE](docs/START-HERE.md) → [recipes](docs/recipes/README.md) |
| **Architect** designing dashboards | [concepts](docs/concepts.md) → [dashboard architecture](docs/dashboard-architecture.md) |
| **Developer** building collectors | [START-HERE lab try](docs/START-HERE.md#5-minute-lab-try) → [authentication](docs/01-auth-and-sessions.md) |
| **MSP** on multi-tenant Manager | [multitenant clusters](docs/multitenant-clusters.md) → [multitenant recipe](docs/recipes/multitenant-connectivity.md) |

This repo provides **recipes** (workflow docs), **runnable samples** (Python scripts for labs), and **architecture notes** (auth, scale, security). Official [DevNet API documentation](https://developer.cisco.com/docs/sdwan/) remains authoritative for each endpoint.

**What this is not:** an official Cisco deliverable, a substitute for TAC, or a guarantee of API compatibility across every Manager patch level. Always validate in your lab.

## Disclaimer (required reading)

This content is provided **“as is”**, **without Cisco support**, and is **not a Cisco initiative**. See **[DISCLAIMER.md](DISCLAIMER.md)** and **[LICENSE](LICENSE)** before use or redistribution.

## Repository layout

| Path | Purpose |
|------|---------|
| [docs/START-HERE.md](docs/START-HERE.md) | Human onboarding and persona paths |
| [docs/concepts.md](docs/concepts.md) | Plain-language concepts |
| [docs/assets/](docs/assets/) | SVG diagrams for navigation |
| [docs/recipes/](docs/recipes/) | Use-case workflows |
| [docs/](docs/) | Foundation and extended guides, [roadmap](docs/ROADMAP.md) |
| [samples/](samples/) | Python scripts and library |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [AGENTS.md](AGENTS.md) | Conventions for LLM agents |

## For developers — quick start (samples)

Prerequisites: Manager **20.18.x**, Python **3.10+**, credentials via `.env` only (never committed).

```bash
cd samples
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
# Edit .env: set SDWAN_BASE_URL (or SDWAN_MANAGER), credentials or SDWAN_JWT_TOKEN
python scripts/inventory_devices.py --limit 5
```

Step-by-step for non-developers: [docs/START-HERE.md#5-minute-lab-try](docs/START-HERE.md#5-minute-lab-try).

Full snapshot (health + inventory + drilldowns + alarms/audit):

```bash
python scripts/collect_dashboard_snapshot.py --hours 24 --output output/dashboard_snapshot.json
```

**Security defaults:** TLS verification on. Lab-only: `SDWAN_VERIFY_SSL=false`. See [security guide](docs/security-rbac-secrets.md).

---

## Full reference index

- [Start here](docs/START-HERE.md) · [Concepts](docs/concepts.md) · [Roadmap](docs/ROADMAP.md)
- [Overview — Manager vs devices, polling patterns](docs/00-overview.md)
- [Authentication — JWT and session](docs/01-auth-and-sessions.md)
- [Scale — pagination, multi-cluster](docs/02-rate-limits-scale.md)
- [Multi-tenant Manager — provider vs tenant](docs/multitenant-clusters.md)
- [API index (DevNet links)](docs/reference/api-index.md)
- [Glossary](docs/reference/glossary.md)
- [Recipes (use cases)](docs/recipes/) — [table of contents](docs/recipes/README.md)

### Extended guides

- [Dashboard architecture](docs/dashboard-architecture.md)
- [API selection guide](docs/api-selection-guide.md)
- [Data retention (30-day history)](docs/data-retention.md)
- [Security, RBAC, secrets](docs/security-rbac-secrets.md)
- [Field dictionary — device health, interfaces, cellular](docs/field-dictionary-device-health.md)
- [DevNet source links](docs/source-links.md)
- [Incorporated starter-pack copies + crosswalk](docs/incorporated-starter-pack/README.md)

### Recipes (human TOC)

| Topic | Doc |
|-------|-----|
| OT starter pack | [docs/recipes/ot-minimal-pack.md](docs/recipes/ot-minimal-pack.md) |
| Device + interface inventory | [docs/recipes/inventory-devices.md](docs/recipes/inventory-devices.md) |
| Config sync (legacy probe) | [docs/recipes/inventory-status-config-groups.md](docs/recipes/inventory-status-config-groups.md) |
| UX 2.0 config groups (list, drift, deploy) | [docs/recipes/config-group-ux2-sync-deploy.md](docs/recipes/config-group-ux2-sync-deploy.md) |
| Health and tunnels | [docs/recipes/health-cpu-mem-tunnels.md](docs/recipes/health-cpu-mem-tunnels.md) |
| Topology and GPS | [docs/recipes/topology-location-gps.md](docs/recipes/topology-location-gps.md) |
| Transport / underlay | [docs/recipes/transport-underlay-monitoring.md](docs/recipes/transport-underlay-monitoring.md) |
| Cellular thresholds | [docs/recipes/cellular-signal-thresholds.md](docs/recipes/cellular-signal-thresholds.md) |
| Location history retention | [docs/recipes/location-history-retention.md](docs/recipes/location-history-retention.md) |
| Syslog, alarms, audit, RBAC | [docs/recipes/syslog-alarms-audit-rbac.md](docs/recipes/syslog-alarms-audit-rbac.md) |
| Multi-tenant connectivity | [docs/recipes/multitenant-connectivity.md](docs/recipes/multitenant-connectivity.md) |
| CLI-style views at scale | [docs/recipes/cli-equivalents-scale.md](docs/recipes/cli-equivalents-scale.md) |

### Python scripts (`samples/scripts/`)

| Script | Purpose |
|--------|---------|
| `inventory_devices.py` | Devices + per-device interfaces |
| `inventory_status.py` | Devices + config status / template / CG hints |
| `config_group_ux2.py` | UX 2.0 config groups: list, drift filter, optional deploy |
| `health_tunnels.py` | Devices + tunnel endpoint attempts |
| `alarms_events.py` | Alarms and events probe |
| `topology_location.py` | Sites + devices for maps |
| `transport_underlay.py` | WAN-ish interfaces from inventory |
| `cellular_thresholds.py` | Cellular metrics + custom bands |
| `cellular_signal_history.py` | EIOLTE `uniqueAggregation` RSSI history (Braille sparkline per slot/SIM) |
| `location_history_demo.py` | SQLite snapshot demo (ETL pattern) |
| `cli_bulk_demo.py` | Bulk read-only diagnostics with dry-run |
| `federation_demo.py` | Multi-Manager merge via `SDWAN_FEDERATION` |
| `multitenant_context.py` | Multi-tenant probe (server, tenant list, device sample) |
| `smoke_recipes.py` | Run all recipe scripts against `samples/.env` (lab/CI gate) |
| `collect_dashboard_snapshot.py` | Health + inventory merge, drilldowns, alarms/audit POST queries |

## Roadmap

Planned enhancements (including **data caps on specific links**, deploy job polling, and safer deploy filters) are tracked in **[docs/ROADMAP.md](docs/ROADMAP.md)**. Contributions welcome per [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing and publishing hygiene

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for workflow, PR expectations, and local checks. All participants must follow **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**.

- Do **not** commit `.env`, live outputs with real device data, or identifying hostnames or sites.
- Prefer generic placeholders (`example.com`, `api-readonly-service` as a **role name** only, not a real account).
- Open issues and PRs in your fork or community tracker as you define for the project.

## License

Sample code is under the [MIT License](LICENSE). Documentation in this repository is intended to be used under the same permissive terms unless a file states otherwise. **This does not grant any rights to Cisco trademarks**; see [DISCLAIMER.md](DISCLAIMER.md).
