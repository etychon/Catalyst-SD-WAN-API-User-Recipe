---
title: Multi-tenant Manager — provider vs tenant connectivity
release: "20.18"
tags: [multitenant, provider, tenant, rbac, jwt, session]
apis:
  - /dataservice/client/server
  - /dataservice/tenant
  - /dataservice/tenant/{tenantId}/vsessionid
  - POST /jwt/login
related_script: samples/scripts/multitenant_context.py
---

# Multi-tenant Manager — provider vs tenant connectivity

## Outcome

You can **classify** your Manager session (single-tenant vs provider vs tenant-only), **list tenants** when RBAC allows, and **attach a VSessionId** for provider-as-tenant automation using the shared Python client.

## When to use which path

| Situation | Auth | Env hints |
|-----------|------|-----------|
| Single-tenant or no tenant list | `jwt` / `auto` / `session` | Leave `SDWAN_TENANT_SUBDOMAIN` unset. |
| Provider; need to list all tenants | `session` | After login, `GET /dataservice/tenant` (see script output). |
| Provider; API calls as one tenant | `session` + `SDWAN_TENANT_SUBDOMAIN=<subDomain>` | Client obtains `VSessionId` and sets `VSessionId` header. |
| Tenant user; cannot see others | `jwt` (typical) | Use normal credentials; optional `SDWAN_TENANT` if SP requires it on `/jwt/login`. |

Full narrative: [../multitenant-clusters.md](../multitenant-clusters.md).

## Data sources

- **Server / tenancy hints:** `GET /dataservice/client/server` — response shape varies; look for tenancy or mode fields in your lab.
- **Tenant inventory:** `GET /dataservice/tenant` — provider (or equivalent) role required for full list.
- **VSessionId:** `POST /dataservice/tenant/{tenantId}/vsessionid` — [DevNet — V Session Id](https://developer.cisco.com/docs/sdwan/v-session-id/) documents provider-only context.

## Orchestration

1. Load [samples/.env.example](../../samples/.env.example) into `.env`; set `SDWAN_BASE_URL` and credentials.
2. Run `python samples/scripts/multitenant_context.py` to capture JSON (server + tenant list + device count probe).
3. If you are provider automating one tenant, set `SDWAN_AUTH_MODE=session`, `SDWAN_TENANT_SUBDOMAIN`, re-run a read-only script (for example [inventory_devices.py](../../samples/scripts/inventory_devices.py)) to confirm dataservice calls succeed with `VSessionId`.

## Edge cases

- **403 on `/dataservice/tenant`:** likely tenant-only user (case 3) or RBAC — expected.
- **JWT login with `SDWAN_TENANT`:** only when your SP documents it; remove if login fails.
- **Trust DevNet** over this recipe for exact JSON field names and new headers.

---

## In plain language

Answers: **How do I connect when my Manager hosts multiple customers?** Explains provider vs tenant users and when you must select a tenant before API calls return the right data.

## Where to go next

- [Multi-tenant clusters guide](../multitenant-clusters.md)
- [UX 2.0 config groups](config-group-ux2-sync-deploy.md)
- [START-HERE — MSP path](../START-HERE.md#msp--multi-tenant-operator)
- [Device inventory](inventory-devices.md)

## Technical details

- [Authentication](../01-auth-and-sessions.md)
- [multitenant_context.py](../../samples/scripts/multitenant_context.py)
- [DevNet — V Session Id](https://developer.cisco.com/docs/sdwan/v-session-id/)
