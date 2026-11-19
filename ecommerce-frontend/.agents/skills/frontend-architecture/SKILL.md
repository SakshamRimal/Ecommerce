---
name: Frontend Architecture
description: Use when choosing the app structure, rendering strategy, routing, folders, or when scaffolding the storefront for the first time.
---

# Frontend Architecture

## When to use

- First scaffold of the app.
- Deciding SSR/SSG/CSR per route.
- Adding a new top-level area (storefront, account, admin).
- Reviewing folder or import conventions.

## Recommended stack (proposal)

| Concern | Choice |
|---|---|
| Framework | Next.js App Router + TypeScript |
| Data | TanStack Query |
| UI state | Zustand (cart drawer, filters) |
| Validation | Zod |
| Styling | Tailwind CSS + shadcn/ui |
| API types | `openapi-typescript` from `/openapi.json` |
| Tests | Vitest + Testing Library + MSW, Playwright |

If a pure SPA is preferred, use Vite + React Router; the same module boundaries
apply.

## Folder structure

```
src/
├── app/                    # routes (Next.js App Router)
│   ├── (shop)/
│   │   ├── page.tsx        # home
│   │   ├── products/
│   │   │   ├── page.tsx    # PLP
│   │   │   └── [id]/page.tsx
│   │   ├── search/page.tsx
│   │   ├── cart/page.tsx
│   │   └── checkout/page.tsx
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (account)/account/page.tsx
│   └── admin/
│       ├── products/page.tsx
│       └── categories/page.tsx
├── components/
│   ├── ui/                 # primitives
│   └── <feature>/          # feature components
├── lib/
│   ├── api/                # client + endpoints + generated types
│   ├── auth/               # token store, refresh
│   ├── money.ts
│   └── query-keys.ts
├── stores/                 # Zustand
└── styles/
```

## Rendering rules

- **Product list/detail:** server-render when possible for SEO; revalidate on
  the client via TanStack Query for cart/stock changes.
- **Cart, checkout, account, admin:** client-only (auth required).
- **Search:** client-driven (query param), debounced.
- **Chat:** client-only; no streaming endpoint exists.

## Rules

1. Keep `lib/api` the only place that calls `fetch`.
2. Route groups separate shop / auth / account / admin layouts.
3. Server components must not read tokens from `localStorage`.
4. Every route has `loading`, `error`, and `not-found` boundaries.
5. No business logic duplicated from the backend (e.g. stock rules).

## Verify

```bash
pnpm typecheck
pnpm lint
pnpm build
```

## Related

- `../../../docs/02-architecture.md`
- `../../../docs/05-pages-and-routes.md`
- `../../../../ecommerce-backend/docs/02-architecture.md`
