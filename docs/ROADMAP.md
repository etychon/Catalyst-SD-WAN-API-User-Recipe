# Roadmap — future enhancements

Community backlog for this repository. **Not a commitment** or release schedule. Items should be validated against [Cisco DevNet SD-WAN API 20.18](https://developer.cisco.com/docs/sdwan/) and your lab Manager before implementation.

When you complete an item, open a PR that updates this file (move to **Done** or remove) and add the recipe/script to [AGENTS.md](../AGENTS.md) and [recipes/README.md](recipes/README.md) as applicable.

## Priority legend

| Priority | Meaning |
|----------|---------|
| **P1** | High value for operators; clear gap in current recipes |
| **P2** | Improves usability, docs, or safety |
| **P3** | Nice-to-have or depends on other work |

---

## P1 — Configuration & compliance (UX 2.0)

| Item | Description |
|------|-------------|
| Deploy job status | After `POST /v1/config-group/{id}/device/deploy`, document and sample polling using `parentTaskId`; report per-device success/failure in CLI output. |
| Safer deploy filters | Flags such as `--skip-unreachable`, `--skip-locked`, `--require-reachable` so deploy does not target edges that cannot apply configuration. |
| Drift signal guide | Document when `configStatusMessage` is “In Sync” but `configGroupUpToDate` is `False`; optional golden-sample table per Manager patch. |

## P1 — Transport, links & QoS

| Item | Description |
|------|-------------|
| **Data cap for specific links** | New recipe (+ sample or extension of [transport-underlay-monitoring.md](recipes/transport-underlay-monitoring.md)): how to implement **data caps on specific WAN/transport links** via Manager 20.18 APIs. Map UI concepts (interfaces, TLOCs, SLA classes, shaping/QoS policy or UX 2.0 feature-profile parcels) to DevNet paths; clarify read vs configure APIs, identifiers (per-link vs per-TLOC vs per-interface), and lab validation. **Not covered in the repo today.** |
| Link utilization vs bandwidth | Tie [field-dictionary-device-health.md](field-dictionary-device-health.md) (`bw-*-util`, `auto-*-bandwidth`, `speed-mbps`) to threshold recipes and statistics queries. |
| Transport SLA drill-down | Expand tunnel/underlay recipe with app-route aggregation examples and BFD + statistics correlation. |

---

## P2 — Multi-tenant, auth & docs

| Item | Description |
|------|-------------|
| Tenant auth in foundation docs | Expand [01-auth-and-sessions.md](01-auth-and-sessions.md) and README: provider JWT + `SDWAN_TENANT_NAME` + `VSessionId` + XSRF-on-GET for UX 2.0 APIs. |
| CHANGELOG | Restore or add root [CHANGELOG.md](../CHANGELOG.md) for recipe/script additions per merge. |
| RBAC matrix | Machine-readable YAML: recipe → minimum DevNet roles (read vs deploy-write). |
| Agent skill | Optional Cursor project skill: recipe + script + smoke + AGENTS map; scope guardrails (SD-WAN 20.18 only). |

## P2 — UX 2.0 scope expansion

| Item | Description |
|------|-------------|
| Policy / topology groups | Separate recipes for UX 2.0 policy groups and topology groups (keep config-group recipe focused). |
| Classic template note | Short migration pointer: when templates still apply; link to Cisco config-group docs; no template-push automation here. |
| OT pack linkage | Connect [ot-minimal-pack.md](recipes/ot-minimal-pack.md) to config-group drift where UX 2.0 is enabled. |

---

## P2 — Operations & scale

| Item | Description |
|------|-------------|
| Federation + tenant | Document `SDWAN_FEDERATION` with `SDWAN_TENANT_NAME` (provider per cluster, tenant per customer). |
| Shared rate limiting | Backoff/concurrency helpers in `sdwan_recipes` for large inventory or config-group sweeps ([02-rate-limits-scale.md](02-rate-limits-scale.md)). |
| Structured exit codes | Scripts return distinct exit codes for RBAC 403, SessionTokenFilter, empty tenant match (CI/smoke diagnostics). |

---

## P3 — Cellular, testing & governance

| Item | Description |
|------|-------------|
| Cellular data usage | Clarify cellular byte counters vs link-level data caps; EIOLTE history + alerting patterns ([cellular-signal-thresholds.md](recipes/cellular-signal-thresholds.md)). |
| Lab validation checklist | CONTRIBUTING appendix: redacted golden JSON for config-group associate + deploy. |
| Offline fixture mode | Optional `--fixture` for `config_group_ux2.py` when no Manager is available. |
| API selection row | Add [api-selection-guide.md](api-selection-guide.md) row for link QoS / data cap once DevNet paths are lab-confirmed. |

---

## Done (recent)

| Item | Notes |
|------|--------|
| Governance recipe (alarms, events, audit, RBAC) | [syslog-alarms-audit-rbac.md](recipes/syslog-alarms-audit-rbac.md) — API catalog, query DSL, filters; `alarms_events.py` + `governance_query.py`. |
| UX 2.0 config groups recipe + script | [config-group-ux2-sync-deploy.md](recipes/config-group-ux2-sync-deploy.md), `config_group_ux2.py` (commit `bae8d45`). |
| Multi-tenant provider JWT + `SDWAN_TENANT_NAME` | `activate_tenant_context()`, XSRF on GET with `VSessionId`. |
| Legacy vs UX 2.0 inventory-status split | Banner on [inventory-status-config-groups.md](recipes/inventory-status-config-groups.md). |

---

## How to propose work

1. Check this list and [open issues](https://github.com/) (if your fork uses GitHub Issues).
2. For new recipes: follow [CONTRIBUTING.md](../CONTRIBUTING.md) — DevNet-first, lab-validated, no secrets in samples.
3. Prefer **one logical PR per roadmap item** when possible.
