# Ecommerce Frontend — Planning Workspace

This folder is the **planning and agent-context workspace** for the storefront.
The application itself has not been built yet.

It is derived entirely from the backend contract in
`../ecommerce-backend/docs/`, especially:

- [`06-api-reference.md`](../ecommerce-backend/docs/06-api-reference.md)
- [`19-frontend-handoff.md`](../ecommerce-backend/docs/19-frontend-handoff.md)
- [`18-known-issues.md`](../ecommerce-backend/docs/18-known-issues.md)

## Status

| Item | State |
|---|---|
| App scaffold | ⏳ not started |
| Framework decision | ⏳ pending (recommendation in [docs/02-architecture.md](docs/02-architecture.md)) |
| API contract | ✅ documented |
| Auth design | ✅ documented |
| Page/route plan | ✅ documented |
| Component inventory | ✅ documented |
| Build plan | ✅ documented |

## Start here

- [`AGENTS.md`](AGENTS.md) — rules for agents working here
- [`.agents/README.md`](.agents/README.md) — feature skills
- [`docs/README.md`](docs/README.md) — full documentation index

## Ground rules

1. The backend is the source of truth for shapes and status codes.
2. Money is a JSON **string**; never do float math on it.
3. Do not invent endpoints. If a feature needs one, add it to the backend first
   and update the contract docs.
4. Read the backend's known issues before designing around a flow.
