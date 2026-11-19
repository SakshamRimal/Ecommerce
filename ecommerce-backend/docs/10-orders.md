# 10 — Orders

## Endpoint

`POST /api/v1/orders` (bearer required)

```json
{ "idempotency_key": "checkout-2026-11-04-abc123" }
```

```json
{
  "id": "uuid",
  "status": "confirmed",
  "total_amount": "179.80",
  "items": [
    {
      "product_id": "uuid",
      "product_name": "Trail Runner",
      "unit_price": "89.90",
      "quantity": 2
    }
  ]
}
```

There are no read/cancel endpoints. `OrderRepository.get_by_id` is unused.

## Checkout algorithm

```
create_order_from_cart(user_id, data):
  existing = repo.get_by_idempotency_key(data.idempotency_key)
  if existing: return existing

  cart = SELECT cart + items + products WHERE user_id
  if not cart or not cart.items: 409 "Cart is empty"

  try:
    for item in cart.items:
      product = SELECT product FOR UPDATE
      if not product: 404
      if product.stock < item.qty: 409
      product.stock -= item.qty
      order_items.append(OrderItem(snapshot name, price, qty))
      total += float(product.price) * qty

    order = Order(status=CONFIRMED, total, idempotency_key, items)
    session.add(order)
    delete all cart items
  except (Conflict, NotFound): raise
  except Exception: metric("internal_error"); raise

  commit
  refresh(order, ["items"])
  metrics: orders_created_total, order_value_dollars
  enqueue send_order_confirmation_task(order_id, email, name)
  return order
```

## Transaction semantics

- Products are locked with `SELECT ... FOR UPDATE`, preventing oversell between
  concurrent checkouts.
- Everything runs in the request session; `get_db_session` commits at the end.
  The service also commits explicitly before enqueueing the email.
- On `ConflictError`/`NotFoundError`, the service re-raises; the dependency rolls
  back, so stock changes and cart deletion are undone.
- Stock is decremented before the order row is added, all in the same
  transaction.

## Idempotency

- `orders.idempotency_key` is `UNIQUE`.
- A replay with the same key returns the original order.
- **Race:** two concurrent requests with the same key can both miss the initial
  lookup. One commits; the other raises `IntegrityError` on the unique index and
  currently returns `500`. Wrap the commit in a catch that re-reads the order and
  returns it.

## Money handling

- `unit_price` is copied from `Product.price` (`Numeric(10,2)`).
- `total_amount` accumulates with `float`, then is stored in `Numeric(10,2)`.
  Use `Decimal` end-to-end to avoid drift such as `0.30000000000000004`.
- The API serializes money as strings.

## Status

`OrderStatus`: `PENDING`, `CONFIRMED`, `CANCELED` (DB names). Checkout always
creates `CONFIRMED`; `PENDING` and `CANCELED` are never set by the backend.

## Email

After commit:

```python
queue.enqueue_job(
    "send_order_confirmation_task",
    str(order.id),
    current_user.email,
    current_user.full_name,
)
```

- The job re-reads the order with items.
- Renders `templates/email/order_confirmation.html`.
- Failures are caught and logged inside the job; the order is unaffected.
- If Redis/arq is unavailable, enqueueing raises **after** the order committed;
  the client sees a 500 even though the order exists.

## Missing capabilities

| Capability | Status |
|---|---|
| List my orders | ❌ |
| Get order by ID | ❌ (repo method exists) |
| Cancel order / restock | ❌ |
| Order status transitions | ❌ |
| Pagination/filtering | ❌ |
| Admin order management | ❌ |
| Payment integration | ❌ |
| Shipping/tax | ❌ |
| Refunds | ❌ |

These are the largest functional gaps for a real storefront and the next
backend milestone.

## Recommended next steps

1. `GET /orders` (user-scoped, paginated) and `GET /orders/{id}`.
2. `POST /orders/{id}/cancel` with stock restore and status transition rules.
3. `IntegrityError` → re-read on idempotency race.
4. `Decimal` totals.
5. Optional payment intent + webhook state machine.
6. Admin order list with filters.
