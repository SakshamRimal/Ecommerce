# 05 — Database Schema

PostgreSQL 16 with the `pgvector` extension. SQLAlchemy 2.0 async models use a
UUID primary key and UTC timestamps.

## Base mixins

`src/app/db/base.py`

| Mixin | Columns |
|---|---|
| `UUIDPrimaryKeyMixin` | `id UUID PK DEFAULT uuid4` |
| `TimestampMixin` | `created_at`, `updated_at` — `TIMESTAMPTZ`, UTC, auto-updated |

## Tables

### `users`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `email` | varchar(255) | unique, indexed, not null |
| `hashed_password` | varchar(255) | not null |
| `full_name` | varchar(255) | not null |
| `is_active` | boolean | not null, default true |
| `role` | enum `user_role` | not null, default `CUSTOMER` |
| `created_at`, `updated_at` | timestamptz | not null |

Relationships: `carts` (1→N, cascade delete-orphan).

> DB enum stores names `CUSTOMER` / `ADMIN`; API serializes values
> `customer` / `admin`.

### `categories`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `name` | varchar(255) | unique, indexed, not null |
| `slug` | varchar(255) | unique, indexed, not null |
| `created_at`, `updated_at` | timestamptz | not null |

Relationships: `products` (1→N, cascade delete-orphan at ORM level).

### `products`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `name` | varchar(255) | not null |
| `description` | varchar(2000) | nullable |
| `price` | numeric(10,2) | not null |
| `stock_quantity` | integer | not null, default 0 |
| `category_id` | UUID | FK → `categories.id` `ON DELETE RESTRICT`, not null |
| `version` | integer | not null, default 1 (model) / 0 (migration) |
| `embedding` | vector(1536) | nullable |
| `created_at`, `updated_at` | timestamptz | not null |

Indexes:
- `ix_products_category_id_name` on `(category_id, name)`
- `ix_products_embedding` — ivfflat (`vector_cosine_ops`, `lists = 100`)

Relationships: `category` (N→1), `cart_items` (1→N).

### `carts`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id` `ON DELETE CASCADE`, indexed, not null |
| `created_at`, `updated_at` | timestamptz | not null |

Relationships: `user`, `items` (1→N, cascade delete-orphan).

One cart per user is enforced by application logic, **not** a unique constraint.

### `cart_items`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `cart_id` | UUID | FK → `carts.id` `ON DELETE CASCADE`, indexed, not null |
| `product_id` | UUID | FK → `products.id` `ON DELETE RESTRICT`, indexed, not null |
| `quantity` | integer | not null, default 1 |
| `created_at`, `updated_at` | timestamptz | not null |

Unique: `uq_cart_product(cart_id, product_id)`.

### `orders`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id`, indexed, not null |
| `status` | enum `order_status` | not null, default `PENDING` |
| `total_amount` | numeric(10,2) | not null |
| `idempotency_key` | varchar(255) | unique, indexed, not null |
| `created_at`, `updated_at` | timestamptz | not null |

Status enum names: `PENDING`, `CONFIRMED`, `CANCELED`. API values:
`pending`, `confirmed`, `canceled`.

Relationships: `items` (1→N, cascade delete-orphan), `user`.

### `order_items`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `order_id` | UUID | FK → `orders.id` `ON DELETE CASCADE`, indexed, not null |
| `product_id` | UUID | FK → `products.id` `ON DELETE RESTRICT`, not null |
| `product_name` | varchar(255) | not null (snapshot) |
| `unit_price` | numeric(10,2) | not null (snapshot) |
| `quantity` | integer | not null |
| `created_at`, `updated_at` | timestamptz | not null |

### `chat_sessions`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → `users.id` `ON DELETE CASCADE`, not null |
| `created_at`, `updated_at` | timestamptz | not null |

Relationships: `messages` (1→N, ordered by `created_at`, cascade delete-orphan).

### `chat_messages`

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `session_id` | UUID | FK → `chat_sessions.id` `ON DELETE CASCADE`, indexed, not null |
| `role` | enum `message_role` | not null |
| `content` | text | not null |
| `created_at`, `updated_at` | timestamptz | not null |

Role enum names: `USER`, `ASSISTANT`, `TOOL`.

## Relationship diagram

```
users 1─────N carts 1─────N cart_items N─────1 products N─────1 categories
  │                                              │
  │ 1─────N orders 1─────N order_items N─────────┘
  │
  └──1─────N chat_sessions 1─────N chat_messages
```

## Migration chain

```
61803d562d66  create users, categories, products, carts, cart_items
      ↓
0b88826428e7  add role to users
      ↓
15fbfc4fe96e  add orders and order_items
      ↓
5ac47d7a06c7  add product_name to order_items
      ↓
8244fd95cddb  add version to products
      ↓
8ae726f3d786  add chat_sessions and chat_messages
      ↓
bbcc817dffc2  add embedding to products + ivfflat index
```

Apply with `uv run alembic upgrade head`.

## Data integrity notes

- `products.category_id` is `RESTRICT`, so deleting a category with products
  raises `ConflictError` (409).
- `cart_items.product_id` and `order_items.product_id` are `RESTRICT`, so a
  product referenced by a cart/order cannot be deleted (this can surface as a
  500 on product delete because only the category delete maps `IntegrityError`).
- `orders.user_id` has no `ON DELETE` clause; deleting a user with orders is
  blocked by the FK.
- Order items intentionally denormalize `product_name` and `unit_price` so
  historical orders do not change when the catalog changes.

## pgvector

- Embedding dimension: **1536** (`text-embedding-3-small`).
- Distance: cosine.
- Index: ivfflat with 100 lists. For small datasets the index may not be used;
  run `ANALYZE products;` after bulk loading.
- Embeddings are generated by `generate_product_embedding_task`; see
  [13-background-jobs.md](13-background-jobs.md).
