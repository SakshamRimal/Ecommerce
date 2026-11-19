# 01 — Overview

## Vision

A fast, accessible storefront for the `ecommerce-backend` API that lets shoppers
browse a catalog, search, manage a cart, check out, and ask an AI shopping
assistant for help. A small admin area lets staff manage products and categories.

## Users

| Persona | Needs |
|---|---|
| Shopper (guest) | Browse, search, view products |
| Shopper (authenticated) | Cart, checkout, account |
| Store admin | Product/category CRUD, visibility into catalog |

## Scope for v1

### In scope
- Home/landing with featured products and categories.
- Product listing with category filter and "load more".
- Product detail.
- Register, login, session refresh, current user.
- Cart drawer + cart page (add/update/remove/clear).
- Checkout review + place order; confirmation from the response.
- Search results.
- AI assistant panel (single-turn request/response UI).
- Admin product/category CRUD.
- Responsive, accessible, tested.

### Out of scope for v1 (blocked or deferred)
- Payments (backend has no payment model).
- Shipping addresses, tax, shipping costs.
- Order history/detail/cancel (no backend endpoints).
- Password reset / email verification / logout-everywhere.
- Product images, variants, SKUs.
- Semantic search UI (no HTTP endpoint).
- Wishlists, reviews, coupons, recommendations.
- Guest cart (backend requires auth).
- i18n/multi-currency.

## Success criteria

1. A new shopper can register, log in, browse, add to cart, and place an order.
2. An admin can create a category, create a product, edit it, and see it in the
   storefront.
3. Search returns and links to products.
4. The assistant answers catalog questions and never invents prices.
5. Lighthouse: performance ≥ 90 on the home/PLP, accessibility ≥ 95.
6. All core flows have automated tests.

## Constraints from the backend

- Money is a **string**.
- Login is form-encoded.
- No guest cart.
- `GET /categories/{id}` is admin-only.
- Lists have no total count.
- Search has only `q` and `limit`.
- No order read endpoints.
- No logout/revocation.
- No image fields.
- Rate limits: login 30/min, chat 10/min.

These are documented in [`03-api-contract.md`](03-api-contract.md) and
[`11-build-plan.md`](11-build-plan.md).
