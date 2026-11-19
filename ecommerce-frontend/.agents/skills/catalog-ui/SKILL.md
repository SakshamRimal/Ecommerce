---
name: Catalog UI
description: Use when building the home page, product listing, product detail, category navigation, or product cards.
---

# Catalog UI

## When to use

- Home/landing page.
- Product listing page (PLP).
- Product detail page (PDP).
- Category navigation.

## Endpoints

| Screen | Endpoints |
|---|---|
| Home | `GET /products?limit=8&offset=0`, `GET /categories` |
| PLP | `GET /products?limit=24&offset=0&category_id=…` |
| PDP | `GET /products/{id}` |
| Categories | `GET /categories?limit=100&offset=0` |

## Response constraints

`ProductListItem` has only:

```ts
{ id, name, price, stock_quantity }
```

No description, category, or image. Cards must work with those four fields. Use
the detail endpoint for category/description.

`Product` adds `description`, `category {id,name,slug}`. There is **no image
field** at all — use placeholders or extend the backend.

## Pagination

- `limit` 1–100 (use 24).
- `offset` increments by `limit`.
- No `total`, so show "Load more" while `items.length === limit`, then stop.
- Offset pagination can duplicate/skip items if products are inserted during
  browsing; acceptable for now.

## Category navigation

- `GET /categories` is public.
- **Do not** call `GET /categories/{id}` publicly — it is admin-only.
- Filter with `GET /products?category_id=…`.
- Slugs exist but there is no by-slug endpoint; use IDs.

## Stock display

- `stock_quantity === 0` → "Out of stock", disable add-to-cart.
- Low stock (e.g. ≤ 5) → "Only N left".
- Stock can change between list and detail; re-check on add-to-cart (409).

## Rules

1. Money is a string: format with `Intl.NumberFormat`.
2. Skeletons for list/detail loading.
3. Empty states for no products and no category results.
4. Error state with retry for 404/500.
5. SEO: server-render PDP/PLP where possible; unique titles/meta.
6. Accessibility: product card is a link with a clear name; images (when added)
   need alt text.

## Gaps to design around

| Missing | Workaround |
|---|---|
| Product images | placeholder/gradient; add backend field later |
| Search filters/sort | only `q` + `limit` |
| Category detail | use list + filter |
| Total count | "Load more" heuristic |
| Variants/SKU | single product model only |

## Related

- `../../../docs/05-pages-and-routes.md`
- `../../../docs/07-components.md`
- `../../../../ecommerce-backend/docs/08-catalog.md`
