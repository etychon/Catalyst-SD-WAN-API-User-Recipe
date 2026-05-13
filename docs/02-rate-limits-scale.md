# Rate limits, pagination, and multi-cluster scale

This guide complements [00-overview.md](00-overview.md) and [01-auth-and-sessions.md](01-auth-and-sessions.md) for designs that must grow toward **tens of thousands of devices** or **multiple Manager clusters**.

## Per-Manager constraints

- **Authentication:** session concurrency and lifetime limits (see DevNet authentication page). Prefer **JWT** for automation to reduce session churn where supported.
- **API volume:** treat the Manager as a shared control plane — use **bounded concurrency**, **exponential backoff** on `429`/`503`, and **idempotent** reads.
- **Pagination:** list endpoints may return large arrays or support paging query parameters. Always read the **20.18 OpenAPI** for the exact parameter names; scripts in this repo use conservative `limit`/`offset` style only where applicable and otherwise document “fetch all with client-side batching”.

## Caching strategy

| Data type | Suggested TTL | Rationale |
|-----------|----------------|-----------|
| Device inventory | 5–30 minutes | Changes on add/remove/RMA |
| Site and topology metadata | 5–30 minutes | Moderate change rate |
| Tunnel or interface counters | 1–5 minutes | Higher rate; align to dashboard refresh |
| Alarms | 30 seconds–2 minutes | Operational sensitivity |

## Multi-cluster “single pane of glass”

1. **Normalize:** define a stable `cluster_id` (Manager FQDN or tenant id) on every row ingested into your data platform.
2. **Authenticate per cluster:** separate credentials or tokens; never reuse tokens across Managers unless your security model explicitly allows it.
3. **Stagger polling:** avoid aligning all clusters to the same clock tick — spread schedules to reduce aggregate CPU spikes.
4. **Centralize retention:** push metrics and inventory snapshots into your TSDB or data lake; the Manager remains the **operational** source, not the long-term analytics warehouse.

## OT deployments

OT users often need **fewer endpoints** and longer cache TTLs. Start with the [OT minimal pack](recipes/ot-minimal-pack.md) and expand only when required.

## Related

- [Recipes index](recipes/) — each recipe calls out orchestration order and edge cases
- [samples/scripts/federation_demo.py](../samples/scripts/federation_demo.py) — optional multi-URL merge pattern
