# Glossary

| Term | Meaning |
|------|---------|
| **Cisco Catalyst SD-WAN Manager** | Central controller UI and APIs for the SD-WAN overlay (often referred to as *vManage* in older literature). |
| **Edge / WAN edge** | Premises equipment running SD-WAN software (router or compute). |
| **Overlay** | VPN fabric built over one or more WAN transports. |
| **Underlay** | Physical or provider transports (MPLS, internet, LTE/5G) beneath IPsec/GRE overlay. |
| **dataservice** | URL prefix for northbound JSON REST APIs on the Manager, for example `/dataservice/device`. |
| **Configuration group (CG)** | UX 2.0 group-based configuration (`/dataservice/v1/config-group*`) for `sdwan` or `sd-routing` solutions. Distinct from **classic device templates** (`/dataservice/template/*`). See [config-group-ux2-sync-deploy.md](../recipes/config-group-ux2-sync-deploy.md). |
| **Classic device template** | UX 1.0 template attach/push model; not covered by the UX 2.0 config group recipe. |
| **system-ip** | Stable overlay identifier used in many API filters (format is deployment-specific). |
| **deviceId / uuid** | Device identifiers in API payloads — always validate which field your deployment uses as the join key. |
| **Multi-tenant** | Provider-operated cluster with multiple tenants; RBAC may expose `GET /dataservice/tenant` only to provider users; `VSessionId` header scopes some session calls to one tenant. |
| **JWT claims** | `token`, `refresh`, `csrf`, `tenantId`, etc., from `POST /jwt/login` per DevNet. |
| **XSRF** | Cross-site request forgery token required for most state-changing calls (`X-XSRF-TOKEN` header). |

## Related

- [API index](api-index.md)
- [Overview](../00-overview.md)
