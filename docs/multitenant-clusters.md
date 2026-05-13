# Multi-tenant Cisco Catalyst SD-WAN Manager (Release 20.18)

Official references: [Cisco DevNet — SD-WAN Manager API](https://developer.cisco.com/docs/sdwan/), multitenant flows such as [V Session Id](https://developer.cisco.com/docs/sdwan/v-session-id/) and tenant APIs under `/dataservice/tenant`. This document is **not** a substitute for DevNet or your SP runbook; field names and RBAC differ by patch and license.

## Concepts

| Idea | Meaning |
|------|--------|
| **Single-tenant Manager** | One customer / overlay on the cluster. There is no provider tenant list; `GET /dataservice/tenant` may be empty or not applicable. |
| **Multi-tenant Manager** | A **provider** operates multiple **tenants**. Provider users can list tenants and obtain a **VSessionId** to act *as* a tenant on dataservice calls. **Tenant** users are scoped to one tenant and cannot see others. |
| **VSessionId** | Token returned by `POST /dataservice/tenant/{tenantId}/vsessionid` (provider context). The sample client sends it on subsequent requests as header **`VSessionId`**, consistent with the [Catalyst WAN SDK](https://github.com/cisco-en-programmability/catalystwan-sdk) `vSessionAuth` pattern. |

## Case 1 — Non-multi-tenant cluster

**What you see:** One organization; your user is not a provider listing multiple SP customers.

**How to connect:** Use the same flow as any Manager: `SDWAN_BASE_URL`, `SDWAN_USERNAME`, `SDWAN_PASSWORD`, `SDWAN_AUTH_MODE=jwt` (or `session` / `auto`). Leave multitenant variables unset:

- Do **not** set `SDWAN_TENANT_SUBDOMAIN` (that path is session-only and provider-as-tenant).
- `GET /dataservice/tenant` may return an empty list or 403 depending on software mode; that is normal.

**Sample:** `python samples/scripts/multitenant_context.py` prints server/tenant context; tenant list may be empty.

## Case 2 — Multi-tenant cluster, **provider** user (see all tenants)

**What you see:** You can open the provider UI and switch tenants; APIs such as `GET /dataservice/tenant` succeed and return rows with fields like `subDomain` and `tenantId` (names vary by release — inspect JSON).

**How to list tenants (automation):**

1. Authenticate with **session** mode (`SDWAN_AUTH_MODE=session`) using a **provider** account (cookies + XSRF, as in [01-auth-and-sessions.md](01-auth-and-sessions.md)).
2. `GET /dataservice/tenant` with the session cookie and `X-XSRF-TOKEN` (the shared `ManagerClient` does this after login).
3. Parse the `data` array (see `unwrap_data` in `samples/src/sdwan_recipes/util.py`).

**How to act as a specific tenant (provider-as-tenant):**

1. Same session login as provider.
2. Set **`SDWAN_TENANT_SUBDOMAIN`** to the tenant’s **`subDomain`** value from the list (case-insensitive match in the sample client).
3. The client calls `POST /dataservice/tenant/{tenantId}/vsessionid` and stores **`VSessionId`**, then sends header **`VSessionId`** on later `/dataservice/...` calls.

Alternatively, if you already obtained **`VSessionId`** elsewhere (e.g. lab capture), set **`SDWAN_VSESSION_ID`** and omit `SDWAN_TENANT_SUBDOMAIN`; the client will attach the header without calling vsessionid again.

**JWT note:** Provider JWT flows vary by deployment. If your SP documents a `tenant` field on `POST /jwt/login`, set **`SDWAN_TENANT`** and the sample client includes it in the JSON body. Confirm with DevNet and live Manager responses.

## Case 3 — Multi-tenant cluster, **tenant** user (cannot see other tenants)

**What you see:** `GET /dataservice/tenant` returns **403 Forbidden** or only your tenant’s data — RBAC hides other tenants.

**How to connect:** Use normal credentials for that tenant user (`SDWAN_AUTH_MODE=jwt` recommended). Do **not** set `SDWAN_TENANT_SUBDOMAIN` (that is for provider-as-tenant after listing all tenants).

If your identity provider or Manager requires an extra tenant discriminator on login, set **`SDWAN_TENANT`** to the value your SP documents for `POST /jwt/login` (often a tenant name or UUID string). If login fails, remove it and follow SP guidance; this repo only forwards the field when set.

Optional **`SDWAN_VSESSION_ID`:** use only if your SP gives you a VSessionId for tenant-scoped session APIs; uncommon for pure tenant JWT flows.

## Environment variables (summary)

| Variable | Typical use |
|----------|-------------|
| `SDWAN_TENANT` | Optional `tenant` field on `POST /jwt/login` when required for tenant-scoped JWT. |
| `SDWAN_TENANT_SUBDOMAIN` | **Session + provider:** match `subDomain` in `GET /dataservice/tenant`, then call vsessionid. Requires `SDWAN_AUTH_MODE=session`. |
| `SDWAN_VSESSION_ID` | Send **`VSessionId`** header on every request (JWT or session) when you already have the token. |

## Runnable sample

- **Script:** [samples/scripts/multitenant_context.py](../samples/scripts/multitenant_context.py) — probes `client/server`, tenant list, and a small device sample.
- **Recipe:** [docs/recipes/multitenant-connectivity.md](recipes/multitenant-connectivity.md)

## Related

- [Authentication — JWT and session](01-auth-and-sessions.md)
- [Scale and multi-Manager](02-rate-limits-scale.md) (different topic: multiple Managers, not tenant RBAC on one Manager)
