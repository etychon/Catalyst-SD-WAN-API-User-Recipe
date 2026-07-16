# Security, RBAC, and Secrets

Incorporated from a partner starter pack; pairs with [01-auth-and-sessions.md](01-auth-and-sessions.md) for JWT vs session details in **this** repository. This is **operational guidance only**; it is not Cisco support policy — see [DISCLAIMER.md](../DISCLAIMER.md).

**Who this is for:** Everyone running samples or production automation. Read this before granting API accounts or enabling deploy scripts.

## Plaintext Password Controls

Never put SD-WAN Manager passwords in:

- Python source files.
- Markdown examples.
- Git-tracked `.env` files.
- Frontend JavaScript.
- Dashboard database fields.
- CI logs.

Use one of:

- Interactive prompt via `getpass`.
- Environment variable injected by a secrets manager.
- Vault, CyberArk, AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault.
- SSO-derived session tokens for approved break-glass or development workflows.

## API User Model

Create dedicated API users per integration (examples only — use your naming standard):

- `api-reader-prod`
- `api-reader-lab`
- `audit-exporter-prod`

Do not use personal admin accounts for scheduled collectors.

## RBAC

Start with read-only permissions:

- Device inventory read.
- Device monitoring read.
- Interface read.
- Routing read for BFD state.
- **Alarms read** — `POST /alarms`, `POST /alarms/count` (DevNet role e.g. `Alarms-read` on count APIs).
- **Events read** — `POST /events` with query DSL.
- **Audit read** — `POST /auditlog`; use a dedicated `audit-exporter-*` service account where possible.
- Config group read if showing assignment and drift (`Config Group-read`, `Config Group > Device-read` on UX 2.0 APIs).
- Config group deploy only for dedicated automation accounts (`Config Group > Device > Deploy-write` per DevNet).

Governance recipe with filter examples: [syslog-alarms-audit-rbac.md](recipes/syslog-alarms-audit-rbac.md). Field discovery: `GET /alarms/query/fields`, `/events/fields`, `/auditlog/fields`.

Only grant write permissions for automation workflows that intentionally change SD-WAN Manager state.

## Logging

Sanitize logs:

- Redact `Authorization`, `Cookie`, `JSESSIONID`, `X-XSRF-TOKEN`, usernames, and passwords.
- Avoid logging full request bodies for auth calls.
- Cap raw response logging in production.

## Transport Security

Use TLS verification in production. In this repository, TLS is controlled with `SDWAN_VERIFY_SSL` (default `true`) for the shared `httpx` client. The `samples/scripts/collect_dashboard_snapshot.py` script additionally accepts `--insecure` for **lab-only** runs. Production collectors should trust the SD-WAN Manager certificate chain.

See also: [01-auth-and-sessions.md](01-auth-and-sessions.md).

## Agent Guardrails

AI agents using these recipes should default to read-only endpoints.

**UX 2.0 configuration groups:** Documentation and samples in this repository may describe **deploy** and other write APIs for configuration groups ([config-group-ux2-sync-deploy.md](recipes/config-group-ux2-sync-deploy.md)). That is intentional for operators automating compliance workflows. **Runtime best practice:** do not call deploy or provision POST APIs until the operator explicitly confirms (sample scripts require `--deploy` and `--confirm-deploy` together; agents should obtain human approval per change).

Require explicit approval before:

- Deploying **classic device templates** or pushing template changes (out of scope for the UX 2.0 config group recipe).
- Changing policies.
- Clearing alarms.
- Changing RBAC.
- Running troubleshooting commands that could expose secrets.

---

## In plain language

Use dedicated read-only API accounts for dashboards. Never put passwords in Git or logs. Treat deploy and policy changes as high-risk — require human approval and stronger RBAC.

## Where to go next

- [Authentication](01-auth-and-sessions.md)
- [UX 2.0 config groups — deploy gates](recipes/config-group-ux2-sync-deploy.md)
- [Syslog, alarms, audit recipe](recipes/syslog-alarms-audit-rbac.md)
- [START-HERE — lab try](START-HERE.md#5-minute-lab-try)

## Technical details

- [samples/.env.example](../samples/.env.example)
- [AGENTS.md](../AGENTS.md) — agent guardrails
