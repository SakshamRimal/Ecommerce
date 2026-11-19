# 09 — Cart

## Data model

- `carts`: one row per user (application-enforced, no unique constraint).
- `cart_items`: `(cart_id, product_id)` unique, `quantity ≥ 1` by schema.
- `product_id` is `ON DELETE RESTRICT`.

## Lifecycle

```
GET /cart
  └─ get_or_create_cart(user_id)
       ├─ SELECT cart + items + products (selectinload)
       └─ if missing: INSERT cart, flush, re-select with relations

POST /cart/items
  ├─ get_or_create_cart
  ├─ validate product exists
  ├─ validate stock >= quantity
  ├─ existing item? merge and re-validate → else insert
  ├─ expire(cart)
  ├─ re-select
  └─ build response (subtotal/total from current prices)

PATCH /cart/items/{product_id}
  ├─ find item or 404
  ├─ quantity <= 0 → delete (unreachable via API, schema requires ≥ 1)
  ├─ else validate stock, update
  ├─ expire → re-select → response

DELETE /cart/items/{product_id}
  ├─ find item or 404 → delete → expire → re-select → response

DELETE /cart
  └─ delete all items → expire → re-select → response
```

## Response computation

`CartService._build_response`:

```python
subtotal = Decimal(str(ci.product.price)) * ci.quantity
total += subtotal
```

- Prices come from the **current** product row, not from the cart.
- `unit_price` and `subtotal` are recomputed on every read.
- Empty cart → `{"items": [], "total": "0"}`.

## Stock rules

| Operation | Check |
|---|---|
| Add new item | `product.stock_quantity >= requested` |
| Add existing item | `product.stock_quantity >= existing + requested` |
| Update quantity | `product.stock_quantity >= new quantity` |
| Remove | none |
| Clear | none |

Stock checks are advisory and not transactional. Checkout re-validates under a
row lock.

## Transaction boundaries

- Repositories use `flush()`, not `commit()`.
- The request-scoped `get_db_session` commits at the end.
- A cart created during a request that later fails is rolled back.
- Because `expire_on_commit=False`, the service explicitly `expire(cart)` and
  re-reads to avoid stale identity-map data.

## Edge cases and gotchas

1. **Duplicate carts under concurrency.** Two simultaneous first requests can
   both create a cart (no unique constraint on `carts.user_id`). Add a unique
   index.
2. **PATCH body requires `product_id`.** It is redundant and ignored.
3. **Zero-quantity removal is unreachable** because `CartItemRequest` enforces
   `quantity >= 1`. Either allow 0 or delete the branch.
4. **No guest cart.** The cart is tied to an authenticated user.
5. **No price snapshot.** If an admin changes a price, the cart total changes on
   the next read; that is usually desired.
6. **No max quantity / line limit.** A client can add up to available stock and
   create many lines.
7. **No cart cache.** The comment "Expire cached cart" refers to the SQLAlchemy
   identity map, not Redis.

## Suggested improvements

- Unique index on `carts.user_id`.
- Accept `quantity=0` to remove, or remove the dead branch.
- Drop `product_id` from the PATCH schema.
- Add `PUT /cart/items` upsert semantics.
- Add optimistic concurrency or idempotency for add-to-cart.
- Return a lightweight `updated_at` so clients can resolve conflicts.
