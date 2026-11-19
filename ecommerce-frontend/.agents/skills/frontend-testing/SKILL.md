---
name: Frontend Testing
description: Use when adding unit, component, integration, or end-to-end tests for the storefront, or when mocking the backend with MSW.
---

# Frontend Testing

## When to use

- New component or hook.
- New API call.
- Auth/cart/checkout/search flows.
- Fixing flaky tests.

## Pyramid

| Level | Tool | Scope |
|---|---|---|
| Unit | Vitest | pure functions (`money`, `query-keys`, validators) |
| Component | Vitest + Testing Library | components with MSW |
| Integration | Vitest + MSW | page-level data flows |
| E2E | Playwright | happy paths against the real backend |

## MSW setup

Create handlers from the backend contract:

```ts
http.get(`${API}/products`, () =>
  HttpResponse.json([
    { id: "p1", name: "Trail Runner", price: "89.90", stock_quantity: 4 },
  ]),
);

http.post(`${API}/auth/login`, async ({ request }) => {
  const body = await request.text();
  // assert form-encoded, not JSON
  return HttpResponse.json({
    access_token: "a",
    refresh_token: "r",
    token_type: "bearer",
  });
});
```

Add a handler for every endpoint used by a test. Keep fixtures typed from
`docs/03-api-contract.md`.

## Test cases that matter

### Auth
- Login sends form data, stores tokens, fetches `/auth/me`.
- 401 triggers one refresh then retry.
- Refresh failure logs out.
- Customer blocked from admin.

### Catalog
- Loading skeleton → list.
- Empty list.
- 404 product page.
- Price renders as currency.
- Out-of-stock disables add.

### Cart
- Add → cart updated from response.
- 409 stock → message + refetch.
- Quantity stepper boundaries (min 1).
- Remove/clear.

### Checkout
- Empty cart blocks submit.
- Same idempotency key reused on retry.
- Success shows snapshot from response.
- 409 handled.

### Search
- Debounce/cancel.
- No results.
- 500 error state.

### Chat
- Pending disables composer.
- 429 message.
- Reply appended.

## E2E (Playwright)

Use the Compose stack or a seeded test backend. Cover:

1. Register → login → browse → add to cart → checkout.
2. Search → product detail → add to cart.
3. Admin login → create product → see it in the list.

## Rules

1. Test behaviour, not implementation.
2. Use accessible queries (`getByRole`, `getByLabel`).
3. No arbitrary sleeps; use MSW/`waitFor`.
4. Keep one source of fixtures.
5. Run `typecheck`, `lint`, and tests in CI.
6. Don't assert on money formatting internals; assert the visible currency.

## Commands

```bash
pnpm test
pnpm test:watch
pnpm e2e
pnpm typecheck
```

## Related

- `../../../docs/10-testing.md`
- `../api-client/SKILL.md`
