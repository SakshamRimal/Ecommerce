# 06 — State & Data Fetching

## Principles

1. Server data belongs to TanStack Query.
2. UI-only state belongs to Zustand/local state.
3. The server response is the source of truth for cart totals and stock.
4. One query key factory.
5. Mutations invalidate; they do not hand-patch unless rollback is trivial.

## Query keys

```ts
export const qk = {
  me: () => ["me"] as const,
  products: (p: { limit: number; offset: number; categoryId?: string }) =>
    ["products", p] as const,
  product: (id: string) => ["product", id] as const,
  categories: () => ["categories"] as const,
  cart: () => ["cart"] as const,
  search: (q: string) => ["search", q] as const,
};
```

Keep `categoryId` normalized (`undefined` vs `""`) so keys are stable.

## Defaults

```ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (count, err) =>
        err instanceof ApiError && err.status >= 500 && count < 2,
    },
  },
});
```

Per-query:

| Query | staleTime | Notes |
|---|---|---|
| products list | 60 s | backend caches 300 s |
| product detail | 30 s | stock changes |
| categories | 5 min | rarely changes |
| cart | 0 | always fresh |
| me | 5 min | until auth change |
| search | 30 s | keyed by exact query |

## Mutations

| Mutation | Invalidate | Optimistic |
|---|---|---|
| add/update/remove/clear cart | `cart` | optional |
| create order | `cart` | no |
| admin product write | `products`, `product(id)` | no |
| admin category write | `categories`, `products` | no |
| login/register | `me`, `cart` | no |
| logout | `queryClient.clear()` | — |

## Cart pattern

Every cart mutation returns the full cart. Use `setQueryData(qk.cart(), data)`
on success, then invalidate to be safe.

```ts
const add = useMutation({
  mutationFn: (input: { product_id: string; quantity: number }) =>
    api.cart.add(input),
  onSuccess: (cart) => {
    queryClient.setQueryData(qk.cart(), cart);
    queryClient.invalidateQueries({ queryKey: qk.cart() });
  },
});
```

## Pagination pattern

Offset-based "load more":

```ts
const query = useInfiniteQuery({
  queryKey: qk.products({ limit: 24, offset: 0, categoryId }),
  queryFn: ({ pageParam }) =>
    api.products.list({ limit: 24, offset: pageParam, categoryId }),
  initialPageParam: 0,
  getNextPageParam: (last, all) =>
    last.length === 24 ? all.length * 24 : undefined,
});
```

No total count exists, so stop when a page is short.

## Search pattern

- Debounce 300 ms.
- `enabled: q.length >= 2`.
- `placeholderData: keepPreviousData`.
- Abort stale requests.
- Keep `q` in the URL.

## Auth-aware queries

```ts
useQuery({ queryKey: qk.cart(), queryFn: api.cart.get, enabled: !!user });
```

On logout, `queryClient.clear()` and reset the cart store.

## Error handling

- Query errors render an `ErrorState` with retry.
- Mutation errors surface a toast + field errors.
- 401 is handled centrally by the fetch wrapper; components see a final error
  only after refresh fails.

## Anti-patterns

- `useEffect` + `fetch` for server data.
- Copying server data into Zustand.
- Computing cart totals client-side.
- Using array index as a list key.
- Recreating `QueryClient` on render.
- Fetching the same data in a parent and child separately.

## Related

- `../.agents/skills/state-and-data/SKILL.md`
- [`03-api-contract.md`](03-api-contract.md)
