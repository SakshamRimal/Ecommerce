# 19 — Frontend Handoff

This is the backend contract the future frontend should build against. It is the
source for `ecommerce-frontend/docs/`.

## Base configuration

| Item | Value |
|---|---|
| API base | `http://localhost:8000/api/v1` (dev) |
| Auth scheme | `Authorization: Bearer <access_token>` |
| Content type | `application/json` |
| Login content type | `application/x-www-form-urlencoded` |
| CORS | backend must allow the frontend origin (`CORS_ALLOWED_ORIGINS`) |
| OpenAPI | `GET /openapi.json` |

## Auth contract

| Need | Endpoint | Notes |
|---|---|---|
| Register | `POST /auth/register` | JSON; returns user |
| Login | `POST /auth/login` | **form** `username`, `password` |
| Refresh | `POST /auth/refresh` | JSON `{refresh_token}` (rotates & revokes old token) |
| Logout | `POST /auth/logout` | Bearer + optional JSON `{refresh_token}` |
| Current user | `GET /auth/me` | Bearer |

Token storage recommendation:

- Access token: in memory (or a short-lived cookie if you add CSRF).
- Refresh token: `httpOnly`, `Secure`, `SameSite=Lax` cookie is ideal, but the
  backend returns it in JSON today. Storing it in `localStorage` works but is
  XSS-exposed. Prefer moving to an httpOnly cookie on the backend.
- There is **no logout endpoint**; discard tokens client-side.

Login example:

```ts
const body = new URLSearchParams({ username: email, password });
const res = await fetch(`${API}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body,
});
```

## Types (derived from the API)

```ts
type UUID = string;
type Money = string; // "19.99"

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
  description: string | null;
  image_url: string | null;
  price: Money;
  stock_quantity: number;
  category: Category;
}

export interface Product {
  id: UUID;
  name: string;
  description: string | null;
  image_url: string | null;
  price: Money;
  stock_quantity: number;
  category: Category;
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

export interface ChatResponse {
  reply: string;
}
```

> Money is a string. Never do float math on it; use a decimal library or integer
> cents.

## Endpoint → screen mapping

| Screen | Data needed | Endpoints |
|---|---|---|
| Home | featured/new products, categories | `GET /products?limit=…`, `GET /categories` |
| Catalog / PLP | paginated products, category filter | `GET /products?limit&offset&category_id` |
| Product detail | product + category | `GET /products/{id}` |
| Search | results | `GET /search/products?q&limit` |
| Login / Register | tokens | `POST /auth/login`, `POST /auth/register` |
| Account | current user | `GET /auth/me` |
| Cart drawer/page | cart | `GET /cart`, `POST /cart/items`, `PATCH/DELETE /cart/items/{id}`, `DELETE /cart` |
| Checkout | create order | `POST /orders` |
| Order confirmation | order snapshot | response from `POST /orders` or `GET /orders/{id}` |
| Order history | user orders | `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/cancel` |
| AI assistant | reply + history | `POST /chat`, `GET /chat/history` |
| Admin: products | CRUD | `GET/POST/PATCH/DELETE /products` |
| Admin: categories | CRUD | `GET/POST/PATCH/DELETE /categories` |

## Client rules

1. **Always send the access token** on cart, orders, chat, `/auth/me`, and all
   admin writes.
2. **Refresh once** on 401, then retry the original request once; on a second
   401, log out.
3. **Do not call `/auth/refresh` in parallel** from multiple interceptors; use a
   single-flight lock.
4. **Parse money as strings.** Display with `Intl.NumberFormat`.
5. **Handle stock conflicts** (409) by refetching the product/cart and showing a
   message.
6. **Checkout idempotency:** generate a UUID per checkout attempt and reuse it
   on retry for the same cart.
7. **Search is ES-backed and eventually consistent**; after admin edits, allow a
   short delay or refetch from `/products`.
8. **Chat is rate-limited** to 10/min; disable the send button while pending and
   surface 429.
9. **Cart endpoints are authenticated only** — there is no guest cart. Prompt
   login before adding to cart or implement a local guest cart that merges after
   login (backend merge endpoint does not exist; you would need to add items
   one-by-one after login).
10. **Category detail is admin-only**; do not build a public category page that
    calls it. Use the list and filter products client-side, or fix the backend.

## Error shape to model

```ts
interface ApiError {
  detail: string | Array<{ loc: (string | number)[]; msg: string; type: string }>;
}
```

Map:

| Status | UX |
|---|---|
| 401 | redirect to login / refresh |
| 403 | "You don't have permission" |
| 404 | not found state |
| 409 | conflict (stock, duplicate email, category in use) |
| 422 | inline field errors |
| 429 | "Too many requests, try again shortly" |
| 500 | generic error + retry |

## Backend gaps that block UI features

| UI feature | Blocker |
|---|---|
| Order history / detail | no `GET /orders` |
| Cancel order | no endpoint |
| Public category page | `GET /categories/{id}` is admin-only |
| Guest cart | no guest/anonymous cart |
| Product filters/sort | list API only supports category/limit/offset |
| Search filters | only `q` + `limit` |
| Semantic search UI | no HTTP endpoint |
| Chat history | no history endpoint |
| Logout everywhere | no revocation endpoint |
| Password reset | no endpoint |
| Admin image upload | products have no image field |
| Variants/SKUs | model has no variants |

## Recommended frontend stack (proposal, not decided)

- Next.js (App Router) + TypeScript, or Vite + React Router if SPA-only.
- TanStack Query for server state; Zustand/Context for cart UI state.
- Tailwind CSS + shadcn/ui or a design system.
- Zod schemas generated from `openapi.json` (or `openapi-typescript`).
- Playwright for E2E; Vitest + Testing Library for units.
- `httpOnly` refresh cookie preferred; otherwise in-memory access token.

See `ecommerce-frontend/docs/` for the full frontend plan.
