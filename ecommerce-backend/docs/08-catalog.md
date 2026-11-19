# 08 — Catalog (Products & Categories)

## Products

### Read path

`GET /products` → controller validates pagination → service builds a cache key
`product:list:{limit}:{offset}:{category_id}` → Redis hit returns immediately;
on a miss, the repository selects with `joinedload(Product.category)` ordered by
`created_at DESC`, the response is serialized, and the JSON-safe list is cached.

`GET /products/{id}` always hits the DB (no detail cache).

### Write path

| Action | Validation | Cache | Background jobs |
|---|---|---|---|
| Create | category must exist | delete `product:list:*` | ES index + embedding |
| Update | product exists; category (if changed) exists | delete `product:list:*` | none |
| Delete | product exists | delete `product:list:*` | ES delete |

### Optimistic locking (intended)

`Product.version` starts at 1. The repository receives `expected_version` and:

1. Applies the incoming attributes to the ORM object.
2. Runs `SELECT ... WHERE id = ... AND version = expected_version`.
3. Raises `ConflictError` if no row matches.
4. Increments `version` and commits.

**Verified weakness:** step 2 is a plain `SELECT` without `FOR UPDATE`, and with
`autoflush=False` the possibly-dirty object is not flushed first. Two concurrent
transactions can both read the same version and both commit `version + 1`,
losing an update. A robust fix is a conditional `UPDATE ... WHERE version = :v`
and checking `rowcount`, or `SELECT ... FOR UPDATE`.

### Response shapes

`ProductResponse`:

```json
{
  "id": "uuid",
  "name": "Trail Runner",
  "description": "Lightweight trail shoe",
  "price": "89.90",
  "stock_quantity": 12,
  "category": { "id": "uuid", "name": "Footwear", "slug": "footwear" }
}
```

`ProductListResponse`:

```json
{ "id": "uuid", "name": "Trail Runner", "price": "89.90", "stock_quantity": 12 }
```

The list shape deliberately omits description, category, and timestamps.

### Pagination

- `limit` 1–100, default 20.
- `offset` ≥ 0, default 0.
- No total count and no next/prev cursor; the frontend cannot know when to stop
  except by receiving fewer than `limit` rows.

## Categories

### Create

- Input `{name}` (2–100, trimmed, non-empty).
- `slugify` lowercases, replaces non-alphanumerics with `-`, trims `-`.
- Duplicate slug → `409 Conflict`.
- Name is unique in the DB as well.

```python
def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug
```

### Update

- Only `name` is accepted.
- The slug is **not** regenerated, so `Shoes` can keep slug `footwear`.
- No duplicate-name handling in the service; a DB unique violation would surface
  as an unhandled 500 rather than a 409.

### Delete

- Attempts the delete; on `IntegrityError`, rolls back and raises
  `409 Conflict` because products reference the category (`ON DELETE RESTRICT`).
- ORM relationship declares `cascade="all, delete-orphan"` on
  `Category.products`, which conflicts conceptually with the DB `RESTRICT`. In
  practice the DB wins; be careful when changing cascade settings.

## Caching

| Key | TTL | Invalidated by |
|---|---|---|
| `product:list:{limit}:{offset}:{category_id}` | `CACHE_TTL_SECONDS` (300) | product create/update/delete |

- Cache is JSON-encoded in Redis.
- No cache for single products, categories, or search.
- Invalidation uses `SCAN` + `DEL` per key; fine at small scale, consider
  `UNLINK`/versioned keys at larger scale.
- Cache failures are not caught, so Redis outages surface as 500s on product
  list and on writes that invalidate.

## Search/embedding coupling

- Create enqueues both ES indexing and embedding generation.
- Update enqueues neither, so ES documents and vectors go stale.
- Delete enqueues only ES deletion. The embedding lives on the deleted row.

See [11-search.md](11-search.md) and [13-background-jobs.md](13-background-jobs.md).
