# 12 — Admin

## Access

- Requires `user.role === "admin"` from `GET /auth/me`.
- Backend enforces `require_admin`; the UI guard is convenience only.
- Customer → 403 page, not a redirect loop.
- Show admin nav only to admins.

## Product management

### List

`GET /products?limit=100&offset=0`

Table columns: name, price, stock, category (needs detail calls or a joined
view — the list response omits category), actions.

> The list endpoint does not include `category`, `description`, or images. For a
> category column, either fetch product details lazily or add a backend field.

### Create

`POST /products`

| Field | Validation |
|---|---|
| name | 1–255, trimmed |
| description | ≤ 1000 |
| price | ≥ 0, ≤ 2 decimals |
| stock_quantity | integer ≥ 0 |
| category_id | required; fetch from `GET /categories` |

### Edit

`PATCH /products/{id}`

- All fields optional.
- Description allows up to 2000 here (inconsistent with create).
- After save, warn that search/AI data may lag (backend does not re-index on
  update).
- No image/variant fields exist.

### Delete

`DELETE /products/{id}`

- Confirm first.
- May return **500** if the product is referenced by a cart or order (FK
  `RESTRICT`, unhandled). Catch and explain.
- Prefer setting `stock_quantity = 0` when deletion fails.

## Category management

### List

`GET /categories?limit=100&offset=0`

Table columns: name, slug, actions.

### Create

`POST /categories` `{name}` (2–100)

Slug is generated automatically.

### Rename

`PATCH /categories/{id}` `{name}`

- Slug does **not** change; show a warning.
- Duplicate names may 500 (no service pre-check). Handle gracefully.

### Delete

`DELETE /categories/{id}`

- 409 if products reference it; show "Move or delete its products first."
- 404 if already gone.

## UX

- Dense data table with sticky header.
- Inline validation mirroring backend bounds.
- Optimistic UI is discouraged; wait for the server and refetch.
- After writes, invalidate `products`, `product`, `categories` as appropriate.
- Show the backend `detail` on 409 for actionable messages.
- Add a "last updated" note based on refetch time.
- Destructive actions in a confirm dialog with the object name.

## Security

- Never trust client-side role checks.
- Do not expose admin tokens to third-party scripts.
- Audit log is not available in the backend; note this as a gap.
- Admin mutations are rate-limited only by global middleware (none specific).

## Gaps

| Gap | Impact |
|---|---|
| No product images | cards/tables need placeholders |
| No variants/SKU | one row per product only |
| No bulk actions | edit one at a time |
| No audit log | cannot see who changed what |
| No soft delete | delete is permanent (or blocked) |
| No search re-index on update | stale search results |
| No category detail public | admin-only, fine for admin |
| No order admin | cannot view/manage orders |

## Verification checklist

- [ ] Customer gets 403 at `/admin`.
- [ ] Admin sees the nav link.
- [ ] Create product → visible in storefront.
- [ ] Edit price → storefront reflects it after refetch.
- [ ] Delete category with products → 409 message.
- [ ] Delete a product in a cart → handled error, no crash.
- [ ] All forms validate before submit.
