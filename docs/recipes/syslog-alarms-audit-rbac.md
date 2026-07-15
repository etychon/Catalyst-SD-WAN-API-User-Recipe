---
title: Syslog, alarms, alerts, audit, and RBAC
release: "20.18"
tags: [alarms, events, syslog, audit, rbac, security]
apis:
  - /dataservice/alarms
  - /dataservice/alarms/count
  - /dataservice/event
related_script: samples/scripts/alarms_events.py
---

# Syslog, alarms, alerts, audit, and RBAC

## Outcome

Integrate **reactive monitoring** (alarms and events) and **governance** (audit, least-privilege API users) with partner SIEM and ticketing.

## Data sources

### Pull model (REST)

The sample probes common alarm and event paths (exact paths vary — OpenAPI is canonical):

- `/dataservice/alarms`
- `/dataservice/alarms/count`
- `/dataservice/event`
- `/dataservice/message/events`

Record HTTP status for each candidate so operators know what your deployment exposes.

### Push model (syslog and forwarding)

For high-volume syslog, many enterprises **forward device or Manager syslog** to a collector (UDP/TCP/TLS) rather than polling REST. Align retention and parsing with your security team.

### Audit

Audit logs may be exposed under dedicated **audit** or **admin** API sections depending on RBAC. Create a **read-only monitoring** role with the minimum `/dataservice` scopes required for your dashboards.

## RBAC guidance

- Separate **break-glass admin** from **automation accounts**.
- Never share personal user passwords with integrations; use **service accounts** with JWT where available.
- Log **authorization denials** in your collector without including secrets.

## Orchestration

1. Authenticate with the automation user.
2. Pull alarms/events on an interval aligned to incident response needs.
3. Normalize severities to your SIEM taxonomy.

## Sample

```bash
python scripts/alarms_events.py
```

Source: [samples/scripts/alarms_events.py](../../samples/scripts/alarms_events.py)

---

## In plain language

Answers: **What is actively wrong?** **Who changed configuration or permissions?** Pulls alarms, events, and audit logs into security and NOC views with least-privilege service accounts.

## Where to go next

- [Health and tunnels](health-cpu-mem-tunnels.md)
- [Security, RBAC, secrets](../security-rbac-secrets.md)
- [OT minimal pack](ot-minimal-pack.md)

## Technical details

- [API selection — alarms and audit](../api-selection-guide.md)
- [Authentication](../01-auth-and-sessions.md)
