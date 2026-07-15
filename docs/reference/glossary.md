# Glossary

Plain-language definitions for readers new to APIs. Technical detail is in the **Meaning** column.

| Term | Simple definition | Meaning |
|------|-------------------|---------|
| **API** | A structured way for software to ask the Manager questions and get answers. | Application Programming Interface — REST JSON under `/dataservice/...` in this repo. See [concepts](../concepts.md). |
| **Recipe** | A short workflow doc: what to collect, in what order, and why. | Markdown under `docs/recipes/` with YAML frontmatter. See [recipe anatomy](../assets/recipe-anatomy.svg). |
| **Cisco Catalyst SD-WAN Manager** | The central control center for your SD-WAN network. | Controller UI and APIs for the overlay (often *vManage* in older docs). |
| **Edge / WAN edge** | The router or appliance at a site. | Premises equipment running SD-WAN software. |
| **Overlay** | The encrypted SD-WAN network built on top of WAN links. | VPN fabric over one or more WAN transports. |
| **Underlay** | The physical or provider link (internet, MPLS, LTE). | Transports beneath IPsec/GRE overlay. |
| **Reachability** | Whether the Manager can currently talk to the device. | Reported status on inventory/health APIs; not a substitute for end-to-end app tests. |
| **BFD** | A fast check of whether tunnels/paths are up. | Bidirectional Forwarding Detection — tunnel session health. |
| **dataservice** | The web address prefix for Manager automation APIs. | URL prefix for northbound JSON REST, e.g. `/dataservice/device`. |
| **Configuration group (CG)** | A named bundle of UX 2.0 settings applied to a set of devices. | Group-based config (`/dataservice/v1/config-group*`) for `sdwan` or `sd-routing`. See [config-group-ux2](../recipes/config-group-ux2-sync-deploy.md). |
| **Classic device template** | Older UX 1.0 way to push config to devices. | Template attach/push model; see [legacy inventory status](../recipes/inventory-status-config-groups.md). |
| **system-ip** | A stable ID for a device in many Manager screens. | Overlay identifier used in API filters (format varies by deployment). |
| **deviceId / uuid** | Alternate IDs for the same device in JSON responses. | Validate which field your deployment uses as the join key. |
| **Multi-tenant** | One provider platform, many customer organizations. | Provider users may list tenants; `VSessionId` scopes calls to one tenant. See [multitenant-clusters](../multitenant-clusters.md). |
| **JWT** | A time-limited access token instead of a browser session cookie. | JSON Web Token from `POST /jwt/login`; sent as `Authorization: Bearer`. |
| **JWT claims** | Fields inside the login response (token, refresh, csrf). | `token`, `refresh`, `csrf`, `tenantId`, etc., per DevNet. |
| **XSRF / CSRF token** | A safety token required for changes (POST/PUT/DELETE). | Sent as `X-XSRF-TOKEN` header with mutating requests. |
| **RBAC** | Role-based access — who may read or change what. | Manager permissions for API users; start read-only for collectors. |

---

## In plain language

Use this table when a recipe or guide uses unfamiliar terms. For a full tour, read [START-HERE](../START-HERE.md) and [concepts](../concepts.md).

## Where to go next

- [API index — DevNet links](api-index.md)
- [Recipes by goal](../recipes/README.md)
- [Overview](../00-overview.md)

## Technical details

- [Field dictionary](../field-dictionary-device-health.md)
- [Cisco DevNet — SD-WAN 20.18](https://developer.cisco.com/docs/sdwan/)
