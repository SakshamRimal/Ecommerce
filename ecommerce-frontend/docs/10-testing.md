# 10 — Testing

## Strategy

| Layer | Tool | What |
|---|---|---|
| Unit | Vitest | money, query keys, validators, reducers |
| Component | Vitest + Testing Library | UI states, interactions |
| Integration | Vitest + MSW | page data flows, auth, cart |
| E2E | Playwright | critical journeys against a real backend |
| A11y | axe-core | key pages/components |
| Visual (optional) | Playwright screenshots | design regressions |

## MSW

Mock at the network boundary using the backend contract. Example handlers:

```ts
const API = "http://localhost:8000/api/v1";

export const handlers = [
  http.post(`${API}/auth/login`, async ({ request }) => {
    const text = await request.text();
    if (!text.includes("username=")) {
      return HttpResponse.json({ detail: "Expected form data" }, { status: 422 });
    }
    return HttpResponse.json({
      access_token: "access",
      refresh_token: "refresh",
      token_type: "bearer",
    });
  }),
  http.get(`${API}/products`, ({ request }) => {
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get("limit") ?? 20);
    return HttpResponse.json(
      Array.from({ length: Math.min(limit, 3) }, (_, i) => ({
        id: `p${i}`,
        name: `Product ${i}`,
        price: "19.99",
        stock_quantity: 5,
      })),
    );
  }),
  http.get(`${API}/cart`, () =>
    HttpResponse.json({ id: "c1", items: [], total: "0" }),
  ),
];
```

Keep one fixture module typed from `docs/03-api-contract.md`.

## Critical test cases

### Auth
- Login uses form encoding.
- Tokens stored; `/auth/me` called.
- 401 → refresh → retry once.
- Refresh failure → logout.
- Customer cannot access admin.

### Catalog
- Skeleton → grid.
- Empty category.
- Product 404.
- Price shows formatted currency.
- Out-of-stock disables add.

### Cart
- Add merges quantity.
- 409 stock shows message.
- Stepper min 1.
- Remove/clear.
- Unauthenticated prompts login.

### Checkout
- Empty cart cannot submit.
- Same idempotency key on retry.
- Confirmation renders response snapshot.
- 409 handled.

### Search
- Debounce.
- Empty results.
- Error state.

### Chat
- Pending disables composer.
- 429 cooldown.
- Reply appended.
- Draft preserved on error.

### Admin
- Guard.
- Create/edit/delete.
- Category delete 409.
- Product delete 500 handled.

## E2E journeys

1. Register → login → browse → add to cart → checkout → confirmation.
2. Search → PDP → add to cart.
3. Admin login → create category → create product → visible in storefront.
4. Session expiry → refresh → continue.

Use a seeded backend; reset the DB between runs. Never run E2E against
production.

## Quality gates

```bash
pnpm typecheck
pnpm lint
pnpm test -- --coverage
pnpm e2e
```

Coverage targets:
- `lib/` ≥ 90%
- `components/` ≥ 80%
- Critical pages ≥ 70%

## Flake prevention

- No fixed sleeps.
- Await network via MSW or Playwright auto-wait.
- Deterministic fixtures.
- Isolate query cache per test.
- Reset MSW handlers and auth state after each test.
