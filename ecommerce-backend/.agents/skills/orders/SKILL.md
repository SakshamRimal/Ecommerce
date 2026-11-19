---
name: Orders and Checkout
description: Use when changing order creation from the cart, stock locking, idempotency keys, order totals/status, or the order confirmation email job.
---

# Orders & Checkout

## When to use

- `POST /api/v1/orders`.
- Stock deduction or transaction/locking logic.
- Idempotency behaviour.
- Order confirmation email.
- Adding order read endpoints (currently missing).

## Files

| Concern | File |
|---|---|
| Route | `src/app/api/v1/orders/controller.py` |
| Logic | `src/app/api/v1/orders/service.py` |
| SQL | `src/app/api/v1/orders/repository.py` |
| Schemas | `src/app/api/v1/orders/schema.py` |
| Model | `src/app/models/order.py` |

## Endpoint

`POST /orders` (authenticated) body `{idempotency_key}` → 201 `OrderResponse`
`{id, status, total_amount, items: [{product_id, product_name, unit_price, quantity}]}`.

There is **no** list/get/cancel/status endpoint. `OrderRepository.get_by_id`
exists but is unused.

## Flow

1. Look up an existing order by `idempotency_key`; if found, return it.
2. Load the user's cart with items and products.
3. Reject an empty cart with `409 Conflict`.
4. For each cart item:
   - `SELECT ... FOR UPDATE` the product row.
   - Reject missing product (`404`) or insufficient stock (`409`).
   - Decrement `stock_quantity`.
   - Build `OrderItem` with a **snapshot** of name and price.
5. Create `Order` with `status=CONFIRMED`, total, and idempotency key.
6. Delete cart items.
7. Commit, emit metrics, enqueue `send_order_confirmation_task`.
8. Return the order.

## Rules

1. Keep stock decrements inside one transaction with row locks.
2. Always snapshot `product_name` and `unit_price` into `order_items`.
3. Idempotency key is client-generated and unique in the DB.
4. Do not send email inline; enqueue the arq job after commit.
5. Keep monetary values as `Decimal`/`Numeric(10, 2)`.

## Gotchas

- Idempotency check is not race-safe: two concurrent requests with the same key
  can both pass the check; one then hits the unique constraint and returns 500.
  Catch `IntegrityError` and return the existing order.
- Total is accumulated with `float(product.price)`, which can introduce binary
  floating-point drift before storing in `Numeric`. Accumulate with `Decimal`.
- The email job is enqueued after commit. If Redis is down, the order exists but
  the request raises.
- `OrderResponse.status` is typed `str`, not the `OrderStatus` enum.
- No cancel/refund/restock path.

## Verify

```bash
uv run pytest tests/unit -q
# add focused order tests; none exist today
```

## Related

- `docs/10-orders.md`
- `docs/13-background-jobs.md`
- `docs/18-known-issues.md`
