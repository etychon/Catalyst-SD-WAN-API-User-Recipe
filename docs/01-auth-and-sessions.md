# Authentication — JWT and session (Release 20.18)

Official reference: [Authentication — Cisco Catalyst SD-WAN Manager API, Release 20.18](https://developer.cisco.com/docs/sdwan/authentication/).

**Do I need this to read recipes?** No — only if you run [samples](../samples/scripts/) or build your own collector. For a plain-language intro, see [START-HERE](START-HERE.md) and [concepts](concepts.md).

## Principles (no plaintext passwords in artifacts)

- Store credentials in **environment variables**, a **secrets manager**, or **vault** — never in Git, never in screenshots attached to tickets.
- Treat **JWT access tokens**, **refresh tokens**, **JSESSIONID**, and **XSRF tokens** as secrets at rest and in transit.
- Application logs must **not** print `Authorization`, cookie values, or token JSON. Use the shared sample client which redacts common sensitive keys.

## JWT-based authentication (recommended from 20.18.1)

Documented flow:

1. `POST /jwt/login` with `Content-Type: application/json` and body `username`, `password`, optional `duration` (seconds, 1–604800).
2. On success, parse JSON: use `token` as **Bearer** access token and `csrf` as `X-XSRF-TOKEN` for state-changing requests.
3. Call APIs under `/dataservice/...` with header `Authorization: Bearer <token>` and, for `POST`/`PUT`/`DELETE`, `X-XSRF-TOKEN: <csrf>`.

Refresh:

- `POST /jwt/refresh` with JSON body containing `refresh` and optional `duration`.
- DevNet notes that refresh token rotation behavior has limits — plan to **re-login** when refresh is no longer accepted.

## Session-based authentication (backward compatible)

1. `POST /j_security_check` with `Content-Type: application/x-www-form-urlencoded` and body `j_username` / `j_password`.
2. On success, capture `Set-Cookie: JSESSIONID=...`. DevNet: failure often returns HTML containing `<html` — clients should detect that.
3. `GET /dataservice/client/token` with the `Cookie` header carrying `JSESSIONID` to retrieve the XSRF token string.
4. **GET** requests to `/dataservice/...` typically need the session cookie; **POST**/`PUT`/`DELETE` need cookie **and** `X-XSRF-TOKEN`.

Logout (session mode):

- `POST /logout` with the session cookie when finished to release server-side session resources.

Session limits (from DevNet): default **30 minutes** inactivity, **24 hours** max session life, **100** concurrent sessions per user class behavior — design automations to avoid login storms.

## SSO

If the Manager uses SSO, browser-derived `JSESSIONID` and `X-XSRF-TOKEN` may be used for ad hoc automation; for production integrations, prefer **service accounts** and flows approved by your security team, aligned with DevNet and IT policy.

## mTLS and custom trust stores

Production deployments should use **TLS 1.2+** with server certificates your client trusts. If your lab uses private CAs, install the CA in the client trust store rather than disabling verification globally.

## Sample configuration

See [samples/.env.example](../samples/.env.example): `SDWAN_AUTH_MODE=jwt`, `session`, or **`auto`** (try JWT, then session); `SDWAN_BASE_URL` (**preferred**) or legacy `SDWAN_MANAGER`; `SDWAN_USERNAME`, `SDWAN_PASSWORD`, `SDWAN_VERIFY_SSL`. Multi-tenant options: `SDWAN_TENANT`, `SDWAN_TENANT_SUBDOMAIN`, `SDWAN_VSESSION_ID` (see [multitenant-clusters.md](../multitenant-clusters.md)).

**Bearer token from environment (skip `/jwt/login`):** set `SDWAN_JWT_TOKEN` to the access string from a prior `POST /jwt/login` response (`token` field). Use `SDWAN_AUTH_MODE=jwt` or `auto` (not `session`). For state-changing calls, set `SDWAN_JWT_CSRF` from the same response (`csrf`) when your Manager returns it. If `csrf` is absent from that JSON, the sample `ManagerClient` attempts **`GET /dataservice/client/token` with `Authorization: Bearer …`** after login to obtain an XSRF string paired to the JWT (some statistics POSTs require it). Optional `SDWAN_JWT_REFRESH` enables the client’s existing `POST /jwt/refresh` path on HTTP 401. Prefer username/password or a secrets manager for renewals when possible; pasted tokens expire and must be rotated like passwords.

## Multi-tenant Manager (provider vs tenant)

See **[multitenant-clusters.md](multitenant-clusters.md)** for when to use `SDWAN_TENANT`, `SDWAN_TENANT_SUBDOMAIN`, and `SDWAN_VSESSION_ID`, and how they map to session vs JWT flows. Runnable probe: `samples/scripts/multitenant_context.py`.

---

## In plain language

Authentication proves your automation is allowed to ask the Manager for data. Use a dedicated service account, store passwords in a vault, and log in once per job — not on every API call.

## Where to go next

- [Security, RBAC, secrets](security-rbac-secrets.md)
- [Multi-tenant clusters](multitenant-clusters.md)
- [5-minute lab try](START-HERE.md#5-minute-lab-try)
- [Scale — session limits](02-rate-limits-scale.md)

## Technical details

- [Python client implementation](../samples/src/sdwan_recipes/client.py)
- [samples/.env.example](../samples/.env.example)
- [Cisco DevNet — Authentication](https://developer.cisco.com/docs/sdwan/authentication/)
