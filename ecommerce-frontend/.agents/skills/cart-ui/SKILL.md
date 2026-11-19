---
name: Cart UI
description: Use when building the cart drawer/page, add-to-cart, quantity updates, removals, or cart totals.
---

# Cart UI

## When to use

- Add-to-cart buttons.
- Cart drawer / cart page.
- Quantity steppers.
- Cart totals and empty state.

## Endpoints (all require auth)

| Action | Call | Success |
|---|---|---|
| Read | `GET /cart` | 200 `Cart` |
| Add | `POST /cart/items` `{product_id, quantity}` | 201 `Cart` |
| Update | `PATCH /cart/items/{product_id}` `{product_id, quantity}` | 200 `Cart` |
| Remove | `DELETE /cart/items/{product_id}` | 200 `Cart` |
| Clear | `DELETE /cart` | 200 `Cart` |

Every mutation returns the **full cart** — replace the cache with it.

## Cart shape

```ts
{
  id: string;
  items: {
    id: string;
    product_id: string;
    product_name: string;
    unit_price: string;
    quantity: number;
    subtotal: string;
  }[];
  total: string;
}
```

`subtotal` and `total` are server-computed strings.

## Behaviour

- Adding an existing product merges quantities.
- Adding requires stock ≥ current + requested; otherwise 409.
- Updating requires stock ≥ new quantity; otherwise 409.
- Cart is created lazily on first read/add.
- **No guest cart.** Unauthenticated users must log in before adding.

## Rules

1. Disable quantity controls while a mutation is in flight.
2. On 409, refetch the cart/product and show the available stock.
3. Optimistically update only if you can roll back on error; otherwise await the
   server response.
4. Use the returned cart as the source of truth (do not recompute totals).
5. Show a badge with the total item count.
6. Persist the drawer open state in UI state, not the server.
7. `PATCH` requires `product_id` in the body even though it is in the path — send
   both to match the schema.
8. For `quantity`, never send 0: the schema requires ≥ 1. Use `DELETE` to remove.

## Empty / error states

| State | UI |
|---|---|
| Empty | "Your cart is empty" + link to catalog |
| Unauthenticated | prompt to log in |
| 409 | inline "Only N available" |
| 404 item | refetch cart |
| Network/500 | retry action |

## Guest cart (future)

The backend has no anonymous cart or merge endpoint. If product wants a guest
cart, add a backend endpoint (`POST /cart/merge`) or add items one-by-one after
login.

## Related

- `../../../docs/06-state-and-data-fetching.md`
- `../../../../ecommerce-backend/docs/09-cart.md`
