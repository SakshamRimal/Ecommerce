# Ecommerce Frontend — Documentation

Planning documentation for the storefront. The app is **not built yet**.

Everything here is derived from the backend contract in
[`../../ecommerce-backend/docs/`](../../ecommerce-backend/docs/).

## Index

| # | Document | What it covers |
|---|---|---|
| 01 | [Overview](01-overview.md) | Goals, users, scope, non-goals |
| 02 | [Architecture](02-architecture.md) | Stack, folders, rendering, boundaries |
| 03 | [API Contract](03-api-contract.md) | Types, endpoints, money, errors |
| 04 | [Auth & Session](04-auth-and-session.md) | Login, tokens, refresh, guards |
| 05 | [Pages & Routes](05-pages-and-routes.md) | Route table and page specs |
| 06 | [State & Data](06-state-and-data-fetching.md) | Query keys, caching, mutations |
| 07 | [Components](07-components.md) | Design system and inventory |
| 08 | [Error Handling](08-error-handling.md) | Error taxonomy and UX |
| 09 | [UX & Accessibility](09-ux-accessibility.md) | States, a11y, responsive |
| 10 | [Testing](10-testing.md) | Unit, component, E2E |
| 11 | [Build Plan](11-build-plan.md) | Phases, milestones, backend gaps |
| 12 | [Admin](12-admin.md) | Admin product/category management |

## Status of key decisions

| Decision | Status |
|---|---|
| Framework | Recommended: Next.js App Router + TS |
| Styling | Recommended: Tailwind + shadcn/ui |
| Server state | Recommended: TanStack Query |
| Client state | Recommended: Zustand |
| Auth storage | Pending backend cookie support |
| Payments | Out of scope for v1 (no backend support) |
| Images | Blocked (no image field in backend) |

## Ground truth

- **Backend API reference:** [`06-api-reference.md`](../../ecommerce-backend/docs/06-api-reference.md)
- **Backend → frontend handoff:** [`19-frontend-handoff.md`](../../ecommerce-backend/docs/19-frontend-handoff.md)
- **Backend known issues:** [`18-known-issues.md`](../../ecommerce-backend/docs/18-known-issues.md)

When the backend changes, update the contract doc and the backend handoff in the
same change.
