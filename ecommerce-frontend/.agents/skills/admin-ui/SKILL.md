---
name: Admin UI
description: Use when building admin product and category management, admin guards, forms, or table/list views.
---

# Admin UI

## When to use

- `/admin` area.
- Product create/edit/delete.
- Category create/edit/delete.
- Admin-only navigation and guards.

## Guard

- Requires auth and `user.role === "admin"` from `GET /auth/me`.
- A customer must see a 403 page, not a redirect loop.
- Never rely on hiding the UI only; the backend enforces `require_admin`.

## Product management

| Action | Call |
|---|---|
| List | `GET /products?limit=100&offset=0` |
| Detail | `GET /products/{id}` |
| Create | `POST /products` |
| Update | `PATCH /products/{id}` |
| Delete | `DELETE /products/{id}` |

### Create form fields

| Field | Rules |
|---|---|
| `name` | 1–255, trimmed |
| `description` | ≤ 1000 (create) / ≤ 2000 (update) |
| `price` | ≥ 0, max 2 decimals |
| `stock_quantity` | integer ≥ 0 |
| `category_id` | required UUID |

### Edit notes

- All fields optional in `PATCH`.
- The backend does **not** re-index search or regenerate embeddings on update.
  Tell the admin that search may lag until a backfill.
- Product delete can return 500 if the product is referenced by a cart/order
  (backend bug). Show a clear error and suggest deactivating stock instead.
- There is no image upload or variants.

## Category management

| Action | Call |
|---|---|
| List | `GET /categories?limit=100&offset=0` |
| Detail | `GET /categories/{id}` (admin) |
| Create | `POST /categories` |
| Rename | `PATCH /categories/{id}` `{name}` |
| Delete | `DELETE /categories/{id}` |

Notes:
- Slug is generated on create and **not** updated on rename.
- Delete returns 409 if products reference it.
- No duplicate-name pre-check in the backend; a rename collision may 500.

## UX rules

1. Use a data table with empty/loading/error states.
2. Confirm destructive actions.
3. Inline validation mirroring backend bounds.
4. After mutations invalidate the relevant query keys.
5. Show 409 messages verbatim enough to be actionable.
6. Do not expose admin routes in the customer nav.
7. Add an "admin" badge in the header when the role is admin.

## Verification

- Customer cannot open `/admin` (403).
- Create → appears in list (after refetch).
- Update → detail reflects changes.
- Delete category with products → 409 message.
- Delete product in a cart → error handled, not a blank screen.

## Related

- `../../../docs/12-admin.md`
- `../../../../ecommerce-backend/docs/08-catalog.md`
