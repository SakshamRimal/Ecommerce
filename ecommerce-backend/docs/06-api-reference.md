# 06 — API Reference

Base URL: `http://localhost:8000/api/v1`

## Conventions

- **Auth header:** `Authorization: Bearer <access_token>`
- **JSON bodies** unless marked *form*.
- **Money** (`price`, `unit_price`, `subtotal`, `total`, `total_amount`) is a
  `Decimal` serialized by Pydantic as a **string**, e.g. `"19.99"`.
- **IDs** are UUID strings.
- **Errors** from the app: `{"detail": "<message>"}`.
- **Validation errors** (422): `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.
- No response includes `created_at`/`updated_at` today.

---

## Health

### `GET /health` — public

```json
{ "status": "ok", "database": "up" }
```

`status` is `ok` or `degraded`; `database` is `up` or `down`. Only PostgreSQL is
checked.

---

## Auth

### `POST /auth/register` — public

Request:

```json
{
  "email": "shopper@example.com",
  "password": "password123",
  "full_name": "Shopper"
}
```

Validation: `email` must be valid; `password` 8–128 chars; `full_name` 1–255.

Response **201**:

```json
{
  "id": "c3e1…",
  "email": "shopper@example.com",
  "full_name": "Shopper",
  "is_active": true,
  "role": "customer"
}
```

Errors: `409` email already exists; `422` validation.

### `POST /auth/login` — public, *form-encoded*, rate-limited `30/minute`

Content-Type: `application/x-www-form-urlencoded`

```
username=shopper@example.com&password=password123
```

Response **200**:

```json
{
  "access_token": "eyJ…",
  "refresh_token": "eyJ…",
  "token_type": "bearer"
}
```

Errors: `401` invalid credentials or inactive user; `429` rate limited.

### `POST /auth/refresh` — public

Request:

```json
{ "refresh_token": "eyJ…" }
```

Response **200**: same shape as login (new access + new refresh). Rotates and revokes the consumed refresh token.

Errors: `401` invalid/expired/revoked token or wrong token type.

### `POST /auth/logout` — bearer

Request (optional body):

```json
{ "refresh_token": "eyJ…" }
```

Response **200**:

```json
{ "detail": "Logged out" }
```

Revokes the presented access token and (when supplied) the refresh token.

### `GET /auth/me` — bearer

Response **200**: `UserResponse` (same shape as register response).

Errors: `401` missing/invalid token or inactive user.

---

## Products

### `GET /products` — public

Query:

| Param | Type | Default | Bounds |
|---|---|---|---|
| `limit` | int | 20 | 1–100 |
| `offset` | int | 0 | ≥ 0 |
| `category_id` | UUID | — | optional filter |

Response **200**:

```json
[
  {
    "id": "…",
    "name": "Trail Runner",
    "description": "Lightweight trail shoe",
    "image_url": "https://…",
    "price": "89.90",
    "stock_quantity": 12,
    "category": { "id": "…", "name": "Footwear", "slug": "footwear" }
  }
]
```

Served from Redis cache (`product:list:v2:*`) for 300 s by default.

### `GET /products/{product_id}` — public

Response **200**:

```json
{
  "id": "…",
  "name": "Trail Runner",
  "description": "Lightweight trail shoe",
  "image_url": "https://…",
  "price": "89.90",
  "stock_quantity": 12,
  "category": { "id": "…", "name": "Footwear", "slug": "footwear" }
}
```

Errors: `404` not found; `422` malformed UUID.

### `POST /products` — admin

Request:

```json
{
  "name": "Trail Runner",
  "description": "Lightweight trail shoe",
  "price": "89.90",
  "stock_quantity": 12,
  "category_id": "…"
}
```

Validation: `name` 1–255 (trimmed); `description` ≤ 1000; `price` ≥ 0 with at
most 2 decimals; `stock_quantity` ≥ 0; `category_id` required.

Response **201**: `ProductResponse` (includes nested category).

Errors: `403` not admin; `404` category not found; `422` validation.

Side effects: invalidates `product:list:*`; enqueues ES index + embedding jobs.

### `PATCH /products/{product_id}` — admin

Request (all optional):

```json
{
  "name": "Trail Runner v2",
  "description": "Updated",
  "price": "99.00",
  "stock_quantity": 8,
  "category_id": "…"
}
```

Validation: `name` 2–255; `description` ≤ 2000; `price` ≥ 0, 2 decimals;
`stock_quantity` ≥ 0.

Response **200**: `ProductResponse`.

Errors: `403`, `404` product/category, `409` optimistic-lock conflict, `422`.

Side effects: invalidates `product:list:*`; enqueues ES index + embedding jobs.

### `DELETE /products/{product_id}` — admin

Response **204** (empty).

Errors: `403`, `404`, `409` if a cart or order still references the product (FK `RESTRICT`).

Side effects: invalidates cache; enqueues ES delete.

---

## Categories

### `GET /categories` — public

Query: `limit` 1–100 (default 50), `offset` ≥ 0 (default 0).

Response **200**:

```json
[
  { "id": "…", "name": "Footwear", "slug": "footwear" }
]
```

### `GET /categories/{category_id}` — public

Response **200**: `CategoryResponse`.

Errors: `404`.

### `POST /categories` — admin

Request:

```json
{ "name": "Footwear" }
```

Validation: `name` 2–100, trimmed, non-empty.

Response **201**:

```json
{ "id": "…", "name": "Footwear", "slug": "footwear" }
```

Errors: `403`; `409` slug/name already exists; `422`.

### `PATCH /categories/{category_id}` — admin

Request:

```json
{ "name": "Shoes" }
```

Response **200**: `CategoryResponse` (regenerates `slug`).

Errors: `403`, `404`, `409` duplicate name/slug, `422`.

### `DELETE /categories/{category_id}` — admin

Response **204**.

Errors: `403`, `404`, `409` if products still reference the category.

---

## Cart — bearer required

### `GET /cart`

Response **200**:

```json
{
  "id": "…",
  "items": [
    {
      "id": "…",
      "product_id": "…",
      "product_name": "Trail Runner",
      "unit_price": "89.90",
      "quantity": 2,
      "subtotal": "179.80"
    }
  ],
  "total": "179.80"
}
```

A cart is created lazily on first access.

### `POST /cart/items`

Request:

```json
{ "product_id": "…", "quantity": 2 }
```

Validation: `quantity` ≥ 1.

Response **201**: full `CartResponse`.

Behaviour: if the product is already in the cart, quantities are merged.
Stock is checked before adding.

Errors: `401`; `404` product; `409` insufficient stock; `422`.

### `PATCH /cart/items/{product_id}`

Request:

```json
{ "quantity": 3 }
```

Validation: `quantity` ≥ 0 (`0` removes the item from the cart).

Response **200**: full `CartResponse`.

Errors: `401`; `404` product not in cart; `409` insufficient stock; `422`.

### `DELETE /cart/items/{product_id}`

Response **200**: full `CartResponse`.

Errors: `401`; `404` item not in cart.

### `DELETE /cart`

Clears all items.

Response **200**: full `CartResponse` with an empty `items` array and `total`
`"0"`.

Errors: `401`.

---

## Orders — bearer required

### `POST /orders`

Request:

```json
{ "idempotency_key": "client-generated-uuid-or-string" }
```

Response **201**:

```json
{
  "id": "…",
  "status": "confirmed",
  "total_amount": "179.80",
  "items": [
    {
      "product_id": "…",
      "product_name": "Trail Runner",
      "unit_price": "89.90",
      "quantity": 2
    }
  ]
}
```

Behaviour:
- Returns the existing order if `idempotency_key` was already used.
- Locks product rows, re-validates and decrements stock, snapshots name/price.
- Deletes the cart items.
- Enqueues the confirmation email job.

Errors: `401`; `404` product disappeared; `409` empty cart or insufficient
stock; `422`.

### `GET /orders`

Query: `limit` 1–100 (default 20), `offset` ≥ 0 (default 0).

Response **200**: `OrderResponse[]` (current user's orders, newest first).

### `GET /orders/{order_id}`

Response **200**: `OrderResponse` (scoped to current user).

Errors: `401`; `404` order not found.

### `POST /orders/{order_id}/cancel`

Cancels the order (`status = "canceled"`), restores product stock under row locks, invalidates product list cache, and re-indexes affected products.

Response **200**: `OrderResponse`.

Errors: `401`; `404` order not found; `409` order already canceled.

---

## Search — public

### `GET /search/products`

Query:

| Param | Type | Default | Bounds |
|---|---|---|---|
| `q` | string | required | 1–200 |
| `limit` | int | 20 | 1–50 |
| `offset` | int | 0 | ≥ 0 |
| `min_price` | Decimal | — | ≥ 0 |
| `max_price` | Decimal | — | ≥ 0 |
| `category_id` | UUID | — | optional filter |

Response **200**:

```json
{
  "query": "trail",
  "total": 3,
  "results": [
    {
      "id": "…",
      "name": "Trail Runner",
      "description": "Lightweight trail shoe",
      "category_name": "Footwear",
      "price": "89.90",
      "stock_quantity": 12,
      "score": 4.21
    }
  ],
  "limit": 20,
  "offset": 0
}
```

Elasticsearch `multi_match` on `name^3` + `description`, `fuzziness: AUTO`, with PostgreSQL `ILIKE` fallback if Elasticsearch is unavailable.

### `GET /search/products/semantic`

Query: `q` (1–500), `limit` (1–50, default 10), `offset` (≥ 0, default 0), `min_price`, `max_price`, `category_id`.

Response **200**: `ProductListResponse[]` ordered by pgvector cosine distance.

---

## Chat — bearer required, rate-limited `10/minute`

### `POST /chat`

Request:

```json
{ "message": "I need a gift for a coffee lover" }
```

Validation: `message` 1–1000.

Response **200**:

```json
{ "reply": "Here are a few ideas…" }
```

Behaviour: persists user/assistant messages in a single transaction, reuses the user's latest session, runs the bounded OpenAI tool-calling loop (catalog search, product details, stock, semantic search).

### `GET /chat/history`

Query: `limit` 1–200 (default 50).

Response **200**:

```json
{
  "messages": [
    {
      "id": "…",
      "role": "user",
      "content": "I need a gift for a coffee lover",
      "created_at": "2026-11-05T04:00:00Z"
    }
  ]
}
```

---

## System

| Method | Path | Notes |
|---|---|---|
| GET | `/metrics` | Prometheus text exposition |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/openapi.json` | OpenAPI 3 schema |

---

## Status code summary

| Code | Meaning here |
|---|---|
| 200 | Success |
| 201 | Created (register, product/category create, cart item add, order) |
| 204 | Deleted (no body) |
| 401 | Missing/invalid token, bad credentials |
| 403 | Authenticated but not admin |
| 404 | Resource not found |
| 409 | Conflict: duplicate email/slug, stock, empty cart, FK restrict |
| 422 | Validation error |
| 429 | Rate limited (login/chat) |
| 500 | Unhandled error (ES/OpenAI/Redis/integrity) |
