# 02 — Architecture

## Recommended stack

| Layer | Recommendation | Why |
|---|---|---|
| Framework | Next.js (App Router) + TypeScript | SSR/SEO for catalog, file-based routing, server components |
| Data fetching | TanStack Query | caching, retries, mutations, devtools |
| Client state | Zustand | small, ergonomic for cart drawer/filters |
| Forms | React Hook Form + Zod | validation mirrors backend bounds |
| Styling | Tailwind CSS + shadcn/ui | consistent tokens, accessible primitives |
| API types | `openapi-typescript` | types generated from `/openapi.json` |
| Tests | Vitest + Testing Library + MSW; Playwright | unit → E2E |
| Lint/format | ESLint + Prettier | consistent code |

If the team prefers a pure SPA, Vite + React Router is a valid alternative; the
module boundaries and data rules stay the same. Record the decision before
scaffolding.

## Proposed structure

```
ecommerce-frontend/
├── .agents/                 # AI agent skills (this workspace)
├── docs/                    # planning docs
├── public/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # providers, header/footer
│   │   ├── (shop)/
│   │   │   ├── page.tsx
│   │   │   ├── products/page.tsx
│   │   │   ├── products/[id]/page.tsx
│   │   │   ├── search/page.tsx
│   │   │   ├── cart/page.tsx
│   │   │   └── checkout/page.tsx
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (account)/account/page.tsx
│   │   └── admin/
│   │       ├── layout.tsx
│   │       ├── products/page.tsx
│   │       └── categories/page.tsx
│   ├── components/
│   │   ├── ui/              # Button, Input, Card, Dialog, ...
│   │   ├── layout/          # Header, Footer, Container
│   │   ├── catalog/         # ProductCard, ProductGrid, Filters
│   │   ├── cart/            # CartDrawer, CartLine, QuantityStepper
│   │   ├── checkout/        # OrderSummary, PlaceOrderButton
│   │   ├── search/          # SearchInput, SearchResults
│   │   └── chat/            # AssistantPanel, MessageList, Composer
│   ├── lib/
│   │   ├── api/             # client + endpoint modules + generated types
│   │   ├── auth/            # token store, refresh, guards
│   │   ├── money.ts
│   │   ├── query-keys.ts
│   │   └── env.ts
│   └── stores/              # Zustand
├── tests/
│   ├── unit/
│   ├── component/
│   └── e2e/
└── package.json
```

## Rendering strategy

| Route | Strategy | Reason |
|---|---|---|
| Home | SSR/ISR | SEO, fast first paint |
| PLP | SSR/ISR + client refetch | SEO + freshness |
| PDP | SSR/ISR | SEO, structured data |
| Search | CSR | query-driven |
| Cart | CSR | auth-only |
| Checkout | CSR | auth-only |
| Account | CSR | auth-only |
| Admin | CSR | auth-only |
| Chat | CSR | interactive |

## Boundaries

1. **`lib/api` is the only network layer.** Components call hooks, hooks call
   API functions.
2. **Server state lives in TanStack Query.** No copying products/cart into
   Zustand.
3. **Auth is a store + interceptor.** Access token in memory; refresh is
   single-flight.
4. **Money is a string.** Format through one helper.
5. **Pages own layout; components own presentation.** No data fetching in
   primitives.
6. **Feature folders** keep related components/hooks together as the app grows.

## Environment

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

No secrets in the browser. The backend URL must be allowed by
`CORS_ALLOWED_ORIGINS`.

## Performance

- Route-level code splitting.
- `next/image` (when images exist) or placeholders.
- Prefetch PDP on card hover/focus.
- Keep the catalog payload small (`ProductListItem` is already lean).
- Cache categories for 5 min, product lists for 60 s client-side.
- Avoid client-side waterfalls: fetch list + categories in parallel.

## Security

- Never store refresh tokens in `localStorage` if avoidable; prefer an
  `httpOnly` cookie (requires backend support).
- Sanitize assistant/HTML content.
- Use CSP, `X-Content-Type-Options`, and a strict `connect-src` for the API.
- Never expose `OPENAI_API_KEY` or server secrets to the client.

## Decision log

| Date | Decision | Notes |
|---|---|---|
| — | Framework | pending |
| — | Auth cookie vs memory | pending |
| — | Hosting | pending |
