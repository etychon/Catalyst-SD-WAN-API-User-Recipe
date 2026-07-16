# Agent instructions (LLM context)

**Legal / support:** This repo is **not** an official Cisco initiative and has **no Cisco support**. Read [DISCLAIMER.md](DISCLAIMER.md) before advising production changes. For authoritative API behavior, use [Cisco DevNet SD-WAN docs](https://developer.cisco.com/docs/sdwan/). Human contributions: [CONTRIBUTING.md](CONTRIBUTING.md); conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

**Machine index:** [repo-manifest.json](repo-manifest.json) lists key paths and flags (`official_cisco_project: false`).

Use this repository as **human-readable documentation** plus **executable examples** for Cisco Catalyst SD-WAN Manager **20.18** REST APIs.

## Start here

0. **Human onboarding:** [docs/START-HERE.md](docs/START-HERE.md) and [docs/concepts.md](docs/concepts.md) — plain language, persona paths, no API prerequisite.
1. Security: [docs/01-auth-and-sessions.md](docs/01-auth-and-sessions.md) and [docs/security-rbac-secrets.md](docs/security-rbac-secrets.md) — credentials and RBAC.
2. Patterns: [docs/00-overview.md](docs/00-overview.md) and [docs/dashboard-architecture.md](docs/dashboard-architecture.md) — where data lives and collector architecture.
3. Endpoints: [docs/api-selection-guide.md](docs/api-selection-guide.md) — map APIs to dashboard widgets.
4. Scale: [docs/02-rate-limits-scale.md](docs/02-rate-limits-scale.md) — pagination, backoff, multi-cluster.
5. Multi-tenant: [docs/multitenant-clusters.md](docs/multitenant-clusters.md) — provider vs tenant, `VSessionId`, env vars.

## Conventions

- **Recipes** live under `docs/recipes/` with YAML **frontmatter** (`title`, `tags`, `release`, `related_script`, `apis`).
- **Python** shared library: `samples/src/sdwan_recipes/` — import `ManagerClient`, `SdwanApiError` from `sdwan_recipes.client`.
- **Scripts** live in `samples/scripts/` — thin CLIs; configuration via `.env` (see `samples/.env.example`). Use `collect_dashboard_snapshot.py` for a multi-endpoint export aligned with [docs/dashboard-architecture.md](docs/dashboard-architecture.md). Run `smoke_recipes.py` to exercise all recipe scripts against a local `samples/.env` (never commit `.env`).
- **Do not** log `Authorization` headers, JWT bodies, or passwords. The client uses structured logging and redacts sensitive keys.
- **TLS**: default verify on; `SDWAN_VERIFY_SSL=false` is lab-only and must be called out in any generated deployment advice.
- **UX 2.0 configuration groups:** [docs/recipes/config-group-ux2-sync-deploy.md](docs/recipes/config-group-ux2-sync-deploy.md) covers list/associate/drift/deploy for `sdwan` and `sd-routing` only (not classic templates). Samples may call deploy POST APIs when the operator passes `--deploy` and `--confirm-deploy`; do not deploy without explicit confirmation.

## Recipe → script map

| Recipe | Script |
|--------|--------|
| `docs/recipes/inventory-devices.md` | `samples/scripts/inventory_devices.py` |
| `docs/recipes/inventory-status-config-groups.md` | `samples/scripts/inventory_status.py` |
| `docs/recipes/health-cpu-mem-tunnels.md` | `samples/scripts/health_tunnels.py` |
| `docs/recipes/topology-location-gps.md` | `samples/scripts/topology_location.py` |
| `docs/recipes/transport-underlay-monitoring.md` | `samples/scripts/transport_underlay.py` |
| `docs/recipes/cellular-signal-thresholds.md` | `samples/scripts/cellular_thresholds.py`, `samples/scripts/cellular_signal_history.py` |
| `docs/recipes/location-history-retention.md` | `samples/scripts/location_history_demo.py` |
| `docs/recipes/syslog-alarms-audit-rbac.md` | `samples/scripts/alarms_events.py` (POST queries, `--discover-fields`, filters; shared `governance_query.py`) |
| `docs/recipes/cli-equivalents-scale.md` | `samples/scripts/cli_bulk_demo.py` |
| `docs/recipes/multitenant-connectivity.md` | `samples/scripts/multitenant_context.py` |
| `docs/recipes/config-group-ux2-sync-deploy.md` | `samples/scripts/config_group_ux2.py` |
| `docs/02-rate-limits-scale.md` (multi-cluster) | `samples/scripts/federation_demo.py` |
| (smoke — all recipe scripts) | `samples/scripts/smoke_recipes.py` |
| [docs/dashboard-architecture.md](docs/dashboard-architecture.md) (snapshot) | `samples/scripts/collect_dashboard_snapshot.py` |

## Authoritative API reference

[Cisco DevNet — SD-WAN Manager API 20.18](https://developer.cisco.com/docs/sdwan/). When endpoint paths or JSON fields differ in the field, **trust DevNet and live Manager responses** over this repo; recipes label illustrative shapes where needed.

## Planned work

Future recipes and enhancements (e.g. **data caps on specific links**, deploy job polling): [docs/ROADMAP.md](docs/ROADMAP.md).
