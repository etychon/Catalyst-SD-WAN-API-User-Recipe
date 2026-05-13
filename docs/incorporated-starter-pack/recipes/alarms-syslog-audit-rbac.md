# Alarms, Syslog, Audit, and RBAC

## Dashboard Question

Which events require action, and which administrative changes must be reviewed?

## API Sequence

Alarms:

1. `POST /alarms`
2. `GET /events/fields`

Audit logs:

1. `POST /auditlog`
2. `GET /auditlog/fields`

## Query Pattern

Use POST for dashboard queries because query strings can exceed practical URL limits.

Example query shape:

```json
{
  "query": {
    "condition": "AND",
    "rules": [
      {
        "value": ["6"],
        "field": "entry_time",
        "type": "date",
        "operator": "last_n_hours"
      }
    ]
  },
  "size": 10000
}
```

## Syslog

Use SD-WAN Manager APIs for alarms, events, and audit logs. For raw syslog:

- Forward syslog from SD-WAN components and devices into the customer logging platform.
- Normalize syslog with the same `cluster_id`, `site_id`, `device_id`, and `system_ip` keys.
- Correlate syslog with SD-WAN alarms by time, host, and event type.

## RBAC

Dashboard should show:

- API user identity.
- Last successful collection time.
- RBAC-related audit events.
- Failed login attempts where available.
- Changes to roles, groups, users, templates, policies, or config groups.

## Best Practices

- Separate operational alarms from administrative audit events.
- Keep security/audit views access-controlled.
- Redact sensitive values before sending events to AI agents.

