# Cisco Catalyst SD-WAN Manager — Monitoring recipes (20.18)

<!--
  Machine-readable index: see repo-manifest.json (paths, flags, DevNet hub).
  Agent-oriented rules: see AGENTS.md
  Legal / support stance: see DISCLAIMER.md (not a Cisco initiative; as-is; no support)
-->

## Why this repository exists

Operators, partners, and automation teams repeatedly build the **same kinds of dashboards** on Cisco Catalyst SD-WAN Manager: inventory, reachability, tunnel and transport health, cellular signal, alarms, audit context, and multi-cluster rollups. Official [DevNet API documentation](https://developer.cisco.com/docs/sdwan/) is authoritative for each endpoint, but it is organized for **API discovery**, not for **end-to-end dashboard workflows**.

This repo fills that gap by providing:

1. **Recipes** — short, use-case-driven Markdown with YAML frontmatter (easy for humans and for LLMs to filter) describing outcomes, data sources, orchestration order, field mapping, and edge cases.
2. **Runnable samples** — Python scripts under `samples/scripts/` that **chain multiple calls** per workflow (closer to real collectors than one-off Swagger tries).
3. **Architecture and operations notes** — retention, RBAC, scaling, and security patterns that belong in your design docs, not only in product UI help.

**What this is not:** an official Cisco deliverable, a substitute for TAC, or a guarantee of API compatibility across every Manager patch level. Always validate in your lab and against your release’s OpenAPI.

## Disclaimer (required reading)

This content is provided **“as is”**, **without Cisco support**, and is **not a Cisco initiative**. Cisco trademarks are used descriptively only. See **[DISCLAIMER.md](DISCLAIMER.md)** and **[LICENSE](LICENSE)** before use or redistribution.

## Audience

- **Partners** building repeatable customer integrations.
- **IT/OT architects** and operators who want opinionated monitoring views without exposing every Manager screen.
- **Automation and AI-assisted workflows** that need stable file paths and conventions (see [AGENTS.md](AGENTS.md) and [repo-manifest.json](repo-manifest.json)).

OT-focused entry: [docs/recipes/ot-minimal-pack.md](docs/recipes/ot-minimal-pack.md).

## Repository layout

| Path | Purpose |
|------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute safely and effectively |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards (Contributor Covenant 2.1) |
| [DISCLAIMER.md](DISCLAIMER.md) | Not Cisco-official; as-is; no support; trademarks |
| [repo-manifest.json](repo-manifest.json) | Machine-oriented path index and flags |
| [AGENTS.md](AGENTS.md) | Conventions for LLM agents |
| [docs/](docs/) | Foundation guides (`00`–`02`), extended guides, [recipes](docs/recipes/) |
| [docs/reference/](docs/reference/) | DevNet link index and glossary |
| [docs/incorporated-starter-pack/](docs/incorporated-starter-pack/) | Preserved starter-pack recipes + crosswalk |
| [samples/](samples/) | Installable Python package + `scripts/` |

## Prerequisites

- Cisco Catalyst SD-WAN Manager **20.18.x** (other releases may differ).
- Credentials and Manager URLs **only** via environment variables or a vault — never committed files.
- Python **3.10+** for samples.

## Quick start (samples)

```bash
cd samples
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
# Edit .env: set SDWAN_BASE_URL (or SDWAN_MANAGER), SDWAN_USERNAME, SDWAN_PASSWORD
python scripts/inventory_devices.py --limit 5
```

Full snapshot (health + inventory + drilldowns + alarms/audit), aligned with [docs/dashboard-architecture.md](docs/dashboard-architecture.md):

```bash
python scripts/collect_dashboard_snapshot.py --hours 24 --output output/dashboard_snapshot.json
```

Alternatively, from the repo root: `pip install -r requirements.txt` and set `PYTHONPATH=samples/src` when running scripts; **`pip install -e samples` is still recommended** for imports.

**Security defaults:** TLS verification on. Lab-only: `SDWAN_VERIFY_SSL=false` or `collect_dashboard_snapshot.py --insecure`.

**Password hygiene:** Prefer `SDWAN_PASSWORD_PROMPT=1` and omit `SDWAN_PASSWORD` where possible (see [samples/examples/config.example.env](samples/examples/config.example.env)).

## Documentation index

- [Overview — Manager vs devices, polling patterns](docs/00-overview.md)
- [Authentication — JWT and session](docs/01-auth-and-sessions.md)
- [Scale — pagination, multi-cluster](docs/02-rate-limits-scale.md)
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
| Config sync / configuration groups | [docs/recipes/inventory-status-config-groups.md](docs/recipes/inventory-status-config-groups.md) |
| Health and tunnels | [docs/recipes/health-cpu-mem-tunnels.md](docs/recipes/health-cpu-mem-tunnels.md) |
| Topology and GPS | [docs/recipes/topology-location-gps.md](docs/recipes/topology-location-gps.md) |
| Transport / underlay | [docs/recipes/transport-underlay-monitoring.md](docs/recipes/transport-underlay-monitoring.md) |
| Cellular thresholds | [docs/recipes/cellular-signal-thresholds.md](docs/recipes/cellular-signal-thresholds.md) |
| Location history retention | [docs/recipes/location-history-retention.md](docs/recipes/location-history-retention.md) |
| Syslog, alarms, audit, RBAC | [docs/recipes/syslog-alarms-audit-rbac.md](docs/recipes/syslog-alarms-audit-rbac.md) |
| CLI-style views at scale | [docs/recipes/cli-equivalents-scale.md](docs/recipes/cli-equivalents-scale.md) |

### Python scripts (`samples/scripts/`)

| Script | Purpose |
|--------|---------|
| `inventory_devices.py` | Devices + per-device interfaces |
| `inventory_status.py` | Devices + config status / template / CG hints |
| `health_tunnels.py` | Devices + tunnel endpoint attempts |
| `alarms_events.py` | Alarms and events probe |
| `topology_location.py` | Sites + devices for maps |
| `transport_underlay.py` | WAN-ish interfaces from inventory |
| `cellular_thresholds.py` | Cellular metrics + custom bands |
| `location_history_demo.py` | SQLite snapshot demo (ETL pattern) |
| `cli_bulk_demo.py` | Bulk read-only diagnostics with dry-run |
| `federation_demo.py` | Multi-Manager merge via `SDWAN_FEDERATION` |
| `collect_dashboard_snapshot.py` | Health + inventory merge, drilldowns, alarms/audit POST queries |

## Contributing and publishing hygiene

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for workflow, PR expectations, and local checks. All participants must follow **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**.

- Do **not** commit `.env`, live outputs with real device data, or identifying hostnames or sites.
- Prefer generic placeholders (`example.com`, `api-readonly-service` as a **role name** only, not a real account).
- Open issues and PRs in your fork or community tracker as you define for the project.

## License

Sample code is under the [MIT License](LICENSE). Documentation in this repository is intended to be used under the same permissive terms unless a file states otherwise. **This does not grant any rights to Cisco trademarks**; see [DISCLAIMER.md](DISCLAIMER.md).
