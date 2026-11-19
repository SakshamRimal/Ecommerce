---
name: Shopping Cart
description: Use when changing cart retrieval, adding/updating/removing cart items, stock validation against the cart, or cart response totals.
---

# Shopping Cart

## When to use

- `/api/v1/cart` endpoints.
- Cart item quantities, stock checks, totals.
- Cart persistence and the one-cart-per-user invariant.

## Files

| Concern | File |
|---|---|
| Routes | `src/app/api/v1/cart/controller.py` |
| Logic | `src/app/api/v1/cart/service.py` |
| SQL | `src/app/api/v1/cart/repository.py` |
| Schemas | `src/app/api/v1/cart/schema.py` |
| Model | `src/app/models/cart.py` |

## Endpoints (all require a bearer token)

| Method | Path | Result |
|---|---|---|
| GET | `/cart` | `CartResponse` |
| POST | `/cart/items` | 201 `CartResponse` |
| PATCH | `/cart/items/{product_id}` | `CartResponse` |
| DELETE | `/cart/items/{product_id}` | `CartResponse` |
| DELETE | `/cart` | `CartResponse` |

`CartResponse` = `{id, items: [{id, product_id, product_name, unit_price, quantity, subtotal}], total}`.

## Behaviour

- One cart per user. `get_or_create_cart` creates it lazily if missing.
- Items are eagerly loaded with `selectinload(Cart.items).selectinload(CartItem.product)`.
- Adding an existing product merges quantities.
- Stock is checked against `Product.stock_quantity` before add/update.
- `PATCH` with `quantity <= 0` removes the item (service branch).
- Totals are computed in the service from current product prices, not stored.
- Cart rows are **not** cached in Redis; the comment about "cached cart" is
  misleading — `session.expire(cart)` simply forces a DB re-read.

## Rules

1. Never trust a client-supplied price or subtotal; compute from `Product.price`.
2. Keep the unique constraint `uq_cart_product(cart_id, product_id)`.
3. Enforce `quantity >= 1` at the schema boundary.
4. Re-check stock at checkout — cart stock checks are advisory only.
5. Return the full cart after every mutation so the frontend can replace state.

## Gotchas

- `CartItemRequest` requires `product_id` even on `PATCH`, where the ID is also
  in the path. The body value is ignored.
- Because the schema enforces `quantity >= 1`, the "quantity <= 0 removes item"
  branch is unreachable through the API.
- `get_or_create_cart` flushes but does not commit; the request-scoped session
  commits at the end. An error later in the request rolls back the cart creation.
- No endpoint to merge a guest cart into a user cart.

## Verify

```bash
uv run pytest tests/integration/test_routes.py -q
# add focused tests if behaviour changes
```

## Related

- `docs/09-cart.md`
- `docs/10-orders.md`
