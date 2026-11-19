# 11 — Build Plan

The frontend is not built yet. This is the phased plan, including the backend
work that blocks some features.

## Phase 0 — Decisions (½ day)

- [ ] Choose framework: Next.js App Router (recommended) or Vite SPA.
- [ ] Choose auth storage: httpOnly cookie (needs backend work) vs in-memory.
- [ ] Choose hosting.
- [ ] Confirm design direction (tokens, brand).
- [ ] Record decisions in `02-architecture.md`.

## Phase 1 — Foundation (2–3 days)

- [ ] Scaffold app + TypeScript strict.
- [ ] Tailwind + shadcn/ui + tokens.
- [ ] Providers: TanStack Query, auth, toasts.
- [ ] `lib/api` client + error class + generated types.
- [ ] `Price`, `Button`, `Input`, `Card`, `Skeleton`, `EmptyState`,
      `ErrorState`, `Toast`.
- [ ] Header/footer/layout + responsive nav.
- [ ] MSW + first tests + CI.

**Done when:** a static home page renders with the design system and CI passes.

## Phase 2 — Catalog (3–4 days)

- [ ] `ProductCard`, `ProductGrid`, `CategoryChips`, `StockBadge`.
- [ ] Home: featured products + categories.
- [ ] PLP: pagination ("load more"), category filter, URL state.
- [ ] PDP: detail, add-to-cart placeholder, 404.
- [ ] Loading/empty/error states + tests.

**Done when:** browse and detail flows work against the backend.

## Phase 3 — Auth (2–3 days)

- [ ] Login/register forms.
- [ ] Token store + single-flight refresh.
- [ ] `/auth/me` bootstrap.
- [ ] Route guards + 403 page.
- [ ] Auth tests + E2E login.

**Done when:** session survives refresh and protected routes redirect correctly.

## Phase 4 — Cart (3 days)

- [ ] Cart drawer + cart page.
- [ ] Add/update/remove/clear mutations.
- [ ] Header badge.
- [ ] Stock conflict UX.
- [ ] Auth prompt for guests.
- [ ] Tests.

**Done when:** cart mutations round-trip and totals match the server.

## Phase 5 — Checkout (2–3 days)

- [ ] Checkout review page.
- [ ] Idempotency key lifecycle.
- [ ] Place order + confirmation.
- [ ] Empty/conflict/error states.
- [ ] Tests + E2E purchase.

**Done when:** an order can be placed end-to-end and retried safely.

## Phase 6 — Search (2 days)

- [ ] Header search + `/search`.
- [ ] Debounce, URL state, cancel.
- [ ] Results/empty/error.
- [ ] Tests.

## Phase 7 — AI assistant (2–3 days)

- [ ] Assistant drawer/page.
- [ ] Local transcript, pending state.
- [ ] 429 cooldown, error retry.
- [ ] Sanitized rendering, char limit.
- [ ] Tests.

## Phase 8 — Admin (4–5 days)

- [ ] Admin shell + guard.
- [ ] Product table + form (create/edit/delete).
- [ ] Category table + form (create/rename/delete).
- [ ] Conflict/error UX.
- [ ] Tests.

## Phase 9 — Polish & launch (3–5 days)

- [ ] Accessibility audit (axe, keyboard, screen reader).
- [ ] Performance (Lighthouse, bundle, prefetch).
- [ ] SEO metadata + structured data.
- [ ] E2E suite green.
- [ ] Error monitoring.
- [ ] Analytics (privacy-conscious).
- [ ] Docs + runbook.

## Backend work needed (parallel track)

These block or limit frontend features. Add them in the backend first.

| Priority | Backend task | Unblocks |
|---|---|---|
| P0 | `GET /orders`, `GET /orders/{id}` | Order history/detail |
| P0 | `POST /auth/logout` + refresh revocation | Real logout |
| P0 | Fix product update re-index/embedding | Accurate search/AI |
| P0 | Fix semantic-search chat wiring | AI semantic tool |
| P1 | Make `GET /categories/{id}` public | Category pages |
| P1 | Add product images (`image_url`) | Real product cards |
| P1 | Add list totals/pagination metadata | Accurate pagination |
| P1 | Add price/category filters + sort to search/list | Filters UI |
| P2 | Guest cart + merge endpoint | Pre-login cart |
| P2 | Order cancel/restock | Cancel UI |
| P2 | Password reset/email verification | Account recovery |
| P2 | Address/payment fields | Real checkout |
| P3 | Chat history endpoint | Persistent transcript |
| P3 | Semantic search HTTP endpoint | Semantic search UI |

## Risks

| Risk | Mitigation |
|---|---|
| Backend contract changes mid-build | generated types + contract doc |
| Auth storage decision delayed | build against an auth interface |
| No images | placeholder component, add field early |
| Order history missing | design account page without it |
| Search index lag | expectations copy + refetch |
| Rate limits during QA | test accounts + cooldowns |
