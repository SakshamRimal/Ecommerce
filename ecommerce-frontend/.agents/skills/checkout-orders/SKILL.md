---
name: Checkout and Orders
description: Use when building checkout, order submission, idempotency handling, order confirmation, or order history.
---

# Checkout & Orders

## When to use

- Checkout page.
- Submit order.
- Order confirmation screen.
- Order history (blocked by backend).

## Endpoints

| Action | Call |
|---|---|
| Read cart | `GET /cart` |
| Create order | `POST /orders` `{idempotency_key}` |

There is **no** `GET /orders`, `GET /orders/{id}`, or cancel endpoint. Order
history cannot be built yet.

## Checkout flow

1. Require auth; redirect with `?next=/checkout`.
2. Fetch the cart; block if empty.
3. Show line items, quantities, and the server `total`.
4. Collect any required customer details (the backend does not store an address
   or payment method — see gaps).
5. Generate an idempotency key (UUID v4) when the checkout page loads and keep it
   for retries of the same cart.
6. `POST /orders`.
7. On 201, show the confirmation from the response and invalidate the cart
   query.
8. On 409 (empty/stock), refetch cart and explain.
9. On network timeout, retry with the **same** key.

## Order response

```ts
{
  id: string;
  status: "confirmed" | string;
  total_amount: string;
  items: { product_id, product_name, unit_price, quantity }[];
}
```

Order items are snapshots; do not refetch products to render them.

## Rules

1. Never generate a new key on retry of the same attempt.
2. Never compute the total client-side.
3. Disable the submit button while pending.
4. Confirm the cart is cleared after success (`DELETE /cart` is done by the
   backend as part of checkout).
5. Persist the last order response in memory for the confirmation screen; a page
   refresh loses it (no order detail endpoint).
6. Do not promise email delivery UX beyond "a confirmation email will be sent".

## Gaps blocking real checkout

| Missing | Impact |
|---|---|
| Payment | no payment intent/webhook |
| Address/shipping | no fields in the order model |
| Tax | not modelled |
| Shipping cost | not modelled |
| Order history/detail | cannot list or revisit orders |
| Cancel/refund | no endpoint |
| Email status | async, no delivery status API |

Design checkout as a **review + place order** flow for now, and mark payment and
address as future work.

## Related

- `../../../docs/05-pages-and-routes.md`
- `../../../docs/11-build-plan.md`
- `../../../../ecommerce-backend/docs/10-orders.md`
