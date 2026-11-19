---
name: State and Data Fetching
description: Use when defining query keys, caching, mutations, optimistic updates, or the cart/auth client state model.
---

# State & Data Fetching

## When to use

- Adding a query or mutation.
- Defining cache keys or invalidation.
- Deciding server vs client state.
- Handling auth-aware queries.

## Split

| State | Where |
|---|---|
| Products, categories, cart, orders, user, search | TanStack Query (server state) |
| Cart drawer open, filters, recent searches, chat transcript | Zustand / local state |
| Form fields | React Hook Form or local state |
| Tokens | auth store (memory) + refresh storage |

## Query keys

Centralise in `lib/query-keys.ts`:

```ts
export const qk = {
  products: (p: { limit: number; offset: number; categoryId?: string }) =>
    ["products", p] as const,
  product: (id: string) => ["product", id] as const,
  categories: () => ["categories"] as const,
  cart: () => ["cart"] as const,
  me: () => ["me"] as const,
  search: (q: string) => ["search", q] as const,
};
```

## Defaults

```ts
new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, err) => (err as ApiError).status >= 500 && count < 2,
      refetchOnWindowFocus: false,
    },
  },
});
```

- Product lists: `staleTime` 60 s (backend caches 300 s).
- Product detail: 30 s.
- Categories: 5 min.
- Cart: `staleTime: 0`; always refetch on mount after mutations.
- `me`: long-lived until auth changes.

## Mutations

| Mutation | Invalidate |
|---|---|
| Add/update/remove/clear cart | `qk.cart()` |
| Create order | `qk.cart()`, order confirmation from response |
| Admin product create/update/delete | `products`, `product` |
| Admin category create/update/delete | `categories`, `products` |
| Login/register/refresh | `me`, `cart` |
| Logout | clear all |

## Rules

1. Do not duplicate server state in Zustand.
2. Do not recompute cart totals; use the server response.
3. Use `placeholderData: keepPreviousData` for pagination to avoid flicker.
4. Cancel in-flight search queries when the term changes.
5. On 401, refresh once then retry; on failure, clear the query cache.
6. Use `enabled` for auth-gated queries (`enabled: !!user`).
7. Serialize query params deterministically so cache keys match.

## Optimistic updates

Use only for cart quantity changes where rollback is trivial:

```ts
onMutate: async (next) => {
  await qc.cancelQueries({ queryKey: qk.cart() });
  const prev = qc.getQueryData(qk.cart());
  qc.setQueryData(qk.cart(), patchCart(prev, next));
  return { prev };
},
onError: (_e, _v, ctx) => qc.setQueryData(qk.cart(), ctx?.prev),
onSettled: () => qc.invalidateQueries({ queryKey: qk.cart() }),
```

Checkout and admin writes should **not** be optimistic.

## Related

- `../../../docs/06-state-and-data-fetching.md`
- `../api-client/SKILL.md`
