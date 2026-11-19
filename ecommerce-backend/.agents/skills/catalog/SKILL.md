---
name: Catalog (Products and Categories)
description: Use when changing product or category CRUD, pagination, product caching, category slugs, optimistic locking, or catalog indexing.
---

# Catalog — Products & Categories

## When to use

- Product create/list/detail/update/delete.
- Category create/list/detail/update/delete.
- Slug generation or uniqueness.
- Product cache invalidation or optimistic locking.
- Product indexing into Elasticsearch.

## Files

| Concern | File |
|---|---|
| Product routes | `src/app/api/v1/products/controller.py` |
| Product logic | `src/app/api/v1/products/service.py` |
| Product SQL | `src/app/api/v1/products/repository.py` |
| Product schemas | `src/app/api/v1/products/schema.py` |
| Category routes | `src/app/api/v1/categories/controller.py` |
| Category logic | `src/app/api/v1/categories/service.py` |
| Category SQL | `src/app/api/v1/categories/repository.py` |
| Category schemas + `slugify` | `src/app/api/v1/categories/schema.py` |
| Models | `src/app/models/product.py`, `src/app/models/category.py` |

## Products

- Public: `GET /products`, `GET /products/{id}`.
- Admin: `POST`, `PATCH`, `DELETE`.
- List supports `limit` (1–100, default 20), `offset` (default 0),
  `category_id` filter.
- List is cached in Redis under `product:list:{limit}:{offset}:{category_id}`
  for `CACHE_TTL_SECONDS` (default 300).
- Create validates the category exists, invalidates `product:list:*`, then
  enqueues `index_product_task` and `generate_product_embedding_task`.
- Update validates category if changed, bumps `version`, invalidates list cache.
- Delete removes the row, invalidates list cache, and enqueues
  `delete_product_from_index_task`.
- `ProductResponse` includes nested `category`; `ProductListResponse` does **not**
  (only `id`, `name`, `price`, `stock_quantity`).

## Categories

- Public: `GET /categories` (list only).
- Admin: `GET /categories/{id}`, `POST`, `PATCH`, `DELETE`.
- Slug is generated once at create with `slugify(name)`.
- `PATCH` currently updates **only** `name`; it does **not** regenerate `slug`.
- Delete of a category with products returns `409 Conflict` (FK `RESTRICT`).
- Category list is **not cached**.

## Rules

1. Always validate `category_id` before writing a product.
2. Invalidate `product:list:*` on any product write that changes listing data.
3. Keep the `version` column increment on update.
4. Do not expose `embedding` in API responses.
5. Enqueue ES indexing as a background job; never call Elasticsearch from the
   request path for writes.

## Gotchas

- Optimistic locking is not atomic: the update reads the version, runs a
  non-locking `SELECT`, then commits. Two concurrent writers can both succeed
  and overwrite each other. Use `with_for_update()`/version `WHERE` update for
  a real guarantee. See `docs/18-known-issues.md`.
- `Product.description` is `String(2000)` in the model, `max_length=1000` on
  create, and `2000` on update. Keep these aligned.
- Category detail is admin-only, which is surprising for a storefront.
- Renaming a category leaves the old slug in place, so URL slugs go stale.
- `ProductListResponse` has no category, so storefront cards cannot show it
  without an extra detail call.

## Verify

```bash
uv run pytest tests/integration/test_products.py -q
uv run pytest tests/unit/test_schemas.py -q
```

## Related

- `docs/08-catalog.md`
- `docs/18-known-issues.md`
