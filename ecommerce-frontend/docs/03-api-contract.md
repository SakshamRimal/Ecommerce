# 03 — API Contract

The backend is the source of truth. This page mirrors
[`../../ecommerce-backend/docs/06-api-reference.md`](../../ecommerce-backend/docs/06-api-reference.md)
for frontend consumption.

## Base

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL!;
const BASE = `${API_URL}/api/v1`;
```

| Concern | Value |
|---|---|
| Auth | `Authorization: Bearer <access_token>` |
| JSON | `Content-Type: application/json` |
| Login | `application/x-www-form-urlencoded` |
| Money | string (`"19.99"`) |
| IDs | UUID strings |
| Errors | `{ detail: string \| Issue[] }` |

## Endpoints

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/auth/register` | — | `{email,password,full_name}` | 201 `User` |
| POST | `/auth/login` | — | form `username,password` | `TokenResponse` |
| POST | `/auth/refresh` | — | `{refresh_token}` | `TokenResponse` |
| GET | `/auth/me` | bearer | — | `User` |
| GET | `/products` | — | `limit,offset,category_id` | `ProductListItem[]` |
| GET | `/products/{id}` | — | — | `Product` |
| POST | `/products` | admin | `ProductCreate` | 201 `Product` |
| PATCH | `/products/{id}` | admin | `ProductUpdate` | `Product` |
| DELETE | `/products/{id}` | admin | — | 204 |
| GET | `/categories` | — | `limit,offset` | `Category[]` |
| GET | `/categories/{id}` | admin | — | `Category` |
| POST | `/categories` | admin | `{name}` | 201 `Category` |
| PATCH | `/categories/{id}` | admin | `{name?}` | `Category` |
| DELETE | `/categories/{id}` | admin | — | 204 |
| GET | `/cart` | bearer | — | `Cart` |
| POST | `/cart/items` | bearer | `{product_id,quantity}` | 201 `Cart` |
| PATCH | `/cart/items/{product_id}` | bearer | `{product_id,quantity}` | `Cart` |
| DELETE | `/cart/items/{product_id}` | bearer | — | `Cart` |
| DELETE | `/cart` | bearer | — | `Cart` |
| POST | `/orders` | bearer | `{idempotency_key}` | 201 `Order` |
| GET | `/search/products` | — | `q,limit` | `SearchResponse` |
| POST | `/chat` | bearer | `{message}` | `{reply}` |
| GET | `/health` | — | — | `{status,database}` |

## Types

```ts
export type UUID = string;
export type Money = string;

export interface User {
  id: UUID;
  email: string;
  full_name: string;
  is_active: boolean;
  role: "customer" | "admin";
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface Category {
  id: UUID;
  name: string;
  slug: string;
}

export interface ProductListItem {
  id: UUID;
  name: string;
  price: Money;
  stock_quantity: number;
}

export interface Product {
  id: UUID;
  name: string;
  description: string | null;
  price: Money;
  stock_quantity: number;
  category: Category;
}

export interface ProductCreate {
  name: string;              // 1..255
  description?: string | null; // <= 1000
  price: Money;              // >= 0, 2dp
  stock_quantity?: number;   // >= 0
  category_id: UUID;
}

export interface ProductUpdate {
  name?: string;             // 2..255
  description?: string | null; // <= 2000
  price?: Money;
  stock_quantity?: number;
  category_id?: UUID;
}

export interface CartItem {
  id: UUID;
  product_id: UUID;
  product_name: string;
  unit_price: Money;
  quantity: number;
  subtotal: Money;
}

export interface Cart {
  id: UUID;
  items: CartItem[];
  total: Money;
}

export interface OrderItem {
  product_id: UUID;
  product_name: string;
  unit_price: Money;
  quantity: number;
}

export interface Order {
  id: UUID;
  status: "pending" | "confirmed" | "canceled" | string;
  total_amount: Money;
  items: OrderItem[];
}

export interface SearchResult {
  id: UUID;
  name: string;
  description: string | null;
  category_name: string;
  price: Money;
  stock_quantity: number;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiErrorBody {
  detail: string | ValidationIssue[];
}
```

## Validation bounds

| Field | Bound |
|---|---|
| `email` | valid email |
| `password` | 8–128 |
| `full_name` | 1–255 |
| product `name` | create 1–255; update 2–255 |
| `description` | create ≤ 1000; update ≤ 2000 |
| `price` | ≥ 0, ≤ 2 decimals |
| `stock_quantity` | integer ≥ 0 |
| category `name` | 2–100 |
| cart `quantity` | integer ≥ 1 |
| `message` | 1–1000 |
| `q` | 1–200 |
| product list `limit` | 1–100 (default 20) |
| search `limit` | 1–50 (default 20) |
| category list `limit` | 1–100 (default 50) |

## Status codes

| Code | UI meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | Deleted |
| 401 | Unauthenticated — refresh or login |
| 403 | Not allowed (admin/customer) |
| 404 | Not found |
| 409 | Conflict (stock, duplicate, cart empty, FK) |
| 422 | Validation — map `loc` to fields |
| 429 | Rate limited |
| 500 | Unexpected — show retry |

## Quirks to encode in the client

1. Login is form-encoded.
2. Money is a string.
3. `PATCH /cart/items/{id}` needs `product_id` in the body.
4. `GET /categories/{id}` is admin-only.
5. `DELETE /cart` returns 200 with an empty cart, not 204.
6. `POST /orders` returns the only order snapshot; there is no GET.
7. Product lists have no total; infer "load more" from `items.length === limit`.
8. Search `total` can exceed `results.length`.
9. Product delete may 500 when referenced.
10. Chat has no history endpoint.

## Contract change process

1. Change the backend first.
2. Update backend `docs/06-api-reference.md` and `19-frontend-handoff.md`.
3. Regenerate types.
4. Update this document.
5. Update mocks/tests.
