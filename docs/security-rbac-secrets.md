# Security, RBAC, and Secrets

Incorporated from a partner starter pack; pairs with [01-auth-and-sessions.md](01-auth-and-sessions.md) for JWT vs session details in **this** repository. This is **operational guidance only**; it is not Cisco support policy — see [DISCLAIMER.md](../DISCLAIMER.md).

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
- Alarm/event/audit read.
- Config group read if showing assignment and drift.

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

AI agents using these recipes should default to read-only endpoints. Require explicit approval before:

- Deploying templates or configuration groups.
- Changing policies.
- Clearing alarms.
- Changing RBAC.
- Running troubleshooting commands that could expose secrets.

