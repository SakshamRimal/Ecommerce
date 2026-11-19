# 18 — Known Issues & Risks (Resolution Log)

All critical, high, and medium issues identified during the initial code audit have been **resolved and verified by tests** (`118 passed, 0 failed`).

## Resolved Issues Summary

1. **CLI (`src/app/cli.py`)**: Implemented `uv run ecommerce create-admin --email ... --password ... [--full-name ...] [--promote-existing]`.
2. **Semantic search in chat (`api/v1/chat/controller.py`)**: Wired `SearchService(ProductRepository(session))` into `ToolExecutor`.
3. **`check_stock` tool schema (`ai/tools.py`)**: Fixed `"paramters"` typo to `"parameters"`.
4. **Product update re-indexing (`api/v1/products/service.py`)**: Enqueues `index_product_task` and `generate_product_embedding_task` on `PATCH /products/{id}`.
5. **Atomic optimistic locking (`api/v1/products/repository.py`)**: Uses `SELECT ... FOR UPDATE` with `populate_existing=True` before comparing `version` and incrementing.
6. **Idempotency race (`api/v1/orders/service.py`)**: Catches `IntegrityError` on commit, rolls back, re-reads by `idempotency_key`, and returns the winning order.
7. **Product delete FK conflict (`api/v1/products/repository.py`)**: Catches `IntegrityError` and raises `409 ConflictError`.
8. **Public category detail (`api/v1/categories/controller.py`)**: Removed `require_admin` from `GET /categories/{category_id}`.
9. **Order read & cancel endpoints (`api/v1/orders/`)**: Added `GET /orders`, `GET /orders/{order_id}`, and `POST /orders/{order_id}/cancel` with row-locked stock restoration, cache invalidation, and ES re-indexing.
10. **Token rotation, revocation & logout (`core/token_store.py`, `api/v1/auth/`)**: Added `jti` claims, Redis-backed (with in-memory fallback) token revocation, refresh rotation, and `POST /auth/logout`.
11. **Shared rate limiting (`core/rate_limiter.py`, `core/config.py`)**: Configurable `RATE_LIMIT_STORAGE_URI` (Redis in Docker Compose, memory fallback locally).
12. **Cart item update payload (`api/v1/cart/`)**: Added `CartItemUpdateRequest {quantity}` (`ge=0`, where `0` removes the item) and `uq_carts_user_id` unique constraint + `ON CONFLICT DO NOTHING` in `get_or_create_cart`.
13. **Category slug updates & conflict handling (`api/v1/categories/`)**: Regenerates `slug` on category rename and maps `IntegrityError` to `409 ConflictError`.
14. **Decimal order totals (`api/v1/orders/service.py`)**: Uses `Decimal` end-to-end instead of `float`.
15. **Chat safety & history (`api/v1/chat/`, `ai/tool_executor.py`)**: Added `CHAT_MAX_TOOL_ITERATIONS` cap, single-transaction `add_exchange`, defensive `ToolExecutor` error handling, and `GET /chat/history`.
16. **Search filters, fallback & semantic endpoint (`api/v1/search/`)**: Added `offset`, `min_price`, `max_price`, `category_id` filters, PostgreSQL `ILIKE` fallback when Elasticsearch is down, and `GET /search/products/semantic`.
17. **Startup migrations, trace context & cache resilience (`main.py`, `core/logging.py`, `core/cache.py`)**: Runs Alembic upgrade in executor with local `alembic.ini` resolution, registers `add_trace_context` in structlog processors, closes Redis pool on shutdown, and degrades gracefully if Redis cache is unreachable.


### 2. Semantic search crashes in the chat path
- **Where:** `api/v1/chat/controller.py` builds
  `ToolExecutor(SearchService(), ProductRepository(session))`; `SearchService`
  has `product_repository=None`. `search/service.py:semantic_search_products`
  calls `self.product_repository.semantic_search(...)`.
- **Impact:** the `semantic_search_products` tool raises `AttributeError`; the
  chat turn fails.
- **Fix:** construct `SearchService(ProductRepository(session))`, and/or create
  the repository inside the service.

### 3. `check_stock` tool schema has a typo
- **Where:** `ai/tools.py`, key `"paramters"` instead of `"parameters"`.
- **Impact:** the tool definition is malformed; the model may never call it or
  the API may reject the request.
- **Fix:** rename to `"parameters"`.

### 4. Product updates never re-index or regenerate embeddings
- **Where:** `api/v1/products/service.py:update` (no `enqueue_job` calls).
- **Impact:** Elasticsearch and pgvector keep old names, prices, stock, and
  text; search and AI answers go stale after edits.
- **Fix:** enqueue `index_product_task` and
  `generate_product_embedding_task` after update.

### 5. Optimistic locking is not atomic
- **Where:** `api/v1/products/repository.py:update`.
- **Evidence:** it mutates the object, runs a non-locking
  `SELECT ... WHERE version = expected`, then increments and commits. With
  `autoflush=False` and no `FOR UPDATE`, two concurrent writers can both pass
  and overwrite each other.
- **Impact:** lost updates despite the `version` column.
- **Fix:** `UPDATE products SET ..., version = version + 1 WHERE id = :id AND
  version = :v` and check `rowcount`, or `SELECT ... FOR UPDATE`.

### 6. Idempotency race returns 500
- **Where:** `api/v1/orders/service.py` — check-then-insert on a unique key.
- **Impact:** two concurrent checkouts with the same key: one succeeds, the
  other hits `IntegrityError` and returns 500 instead of the existing order.
- **Fix:** catch `IntegrityError`, roll back, re-read by key, return it.

### 7. Product delete can return 500
- **Where:** `api/v1/products/service.py:delete` → repository delete.
- **Impact:** products referenced by `cart_items` or `order_items`
  (`ON DELETE RESTRICT`) raise an unhandled `IntegrityError`.
- **Fix:** catch and map to `409`, or soft-delete.

## High

### 8. Category detail is admin-only
- **Where:** `api/v1/categories/controller.py:get_category`.
- **Impact:** a storefront cannot fetch a single category; only the list is
  public.
- **Fix:** remove the admin dependency.

### 9. Orders have no read/cancel endpoints
- **Where:** `api/v1/orders/controller.py` only defines `POST ""`.
- **Impact:** users cannot view order history or details; no cancel/restock.
- `OrderRepository.get_by_id` exists but is unused.
- **Fix:** add `GET /orders`, `GET /orders/{id}`, and cancellation with a status
  state machine.

### 10. Refresh tokens never expire early
- **Where:** `api/v1/auth/service.py:refresh_token`.
- **Impact:** no logout/revocation; a leaked refresh token is valid for
  `REFRESH_TOKEN_EXPIRE_DAYS`.
- **Fix:** add `jti`, rotation, revocation, and logout.

### 11. Rate limiting is per process
- **Where:** `core/rate_limiter.py` uses slowapi's default memory storage.
- **Impact:** limits multiply with workers/replicas.
- **Fix:** Redis storage or gateway-level limiting.

## Medium

### 12. `PATCH /cart/items/{product_id}` requires `product_id` in the body
- **Where:** `cart/controller.py` reuses `CartItemRequest`; the body value is
  ignored.
- **Fix:** add a `CartItemUpdateRequest {quantity}`.

### 13. Zero-quantity removal is unreachable
- **Where:** `cart/schema.py` enforces `quantity >= 1`; `cart/service.py` has a
  `quantity <= 0` delete branch.
- **Fix:** allow `ge=0` on update or delete the branch.

### 14. Duplicate carts possible under concurrency
- **Where:** no unique constraint on `carts.user_id`; `get_or_create_cart` is
  read-then-insert.
- **Fix:** add a unique index and handle the conflict.

### 15. Category rename leaves the slug stale
- **Where:** `categories/service.py:update` only sets `name`.
- **Impact:** URLs/slugs no longer match the name; duplicate names can 500.
- **Fix:** regenerate slug on rename and handle uniqueness conflicts.

### 16. Category duplicate name returns 500
- **Where:** service does not pre-check name; DB unique violation is unhandled.
- **Fix:** check or catch `IntegrityError` → 409.

### 17. Description length mismatch
- Model `String(2000)`, create schema `max_length=1000`, update `2000`.
- **Fix:** align to one limit.

### 18. Order totals use float
- **Where:** `orders/service.py` `total_amount += float(product.price) * qty`.
- **Impact:** floating-point drift before storing `Numeric(10,2)`.
- **Fix:** accumulate with `Decimal`.

### 19. Unbounded chat tool loop
- **Where:** `chat/service.py` `while choice.finish_reason == "tool_calls"`.
- **Impact:** a misbehaving model can loop, increasing latency/cost.
- **Fix:** cap iterations (e.g. 5) and return a graceful message.

### 20. Chat can persist a user message without a reply
- **Where:** `ChatRepository.add_message` commits before the model call.
- **Impact:** failed OpenAI/tool calls leave an orphan user message.
- **Fix:** write both messages in one transaction, or mark failures.

### 21. Chat tool errors abort the turn
- **Where:** `ToolExecutor.get_product_details` calls `uuid.UUID(...)` without
  guarding; price filters are applied post-limit.
- **Fix:** validate args and return `{"error": ...}` JSON instead of raising.

### 22. Search has no filters or pagination
- `GET /search/products` only accepts `q` and `limit`; no `min_price`,
  `max_price`, `category_id`, offset, or sort.
- The chat tool advertises `max_price` but the executor ignores it.

### 23. Elasticsearch outage returns 500
- No fallback to PostgreSQL and no degraded response.

### 24. Health checks only PostgreSQL
- Redis, ES, SMTP, worker, and OpenAI are unchecked.

### 25. Startup migration is Docker-only and blocking
- **Where:** `main.py` uses `Config("/app/alembic.ini")` and a synchronous
  `command.upgrade` inside async `lifespan`.
- **Impact:** local runs log `migrations_failed`; migrations block startup.
- **Fix:** run migrations as a deploy step and use `run_in_executor` if kept.

### 26. `add_trace_context` is never registered
- **Where:** `core/logging.py` defines it, but the structlog processor list does
  not include it.
- **Impact:** `trace_id` is missing from logs.

### 27. `BaseHTTPMiddleware` request-context performance
- **Where:** `middlewares/request_context.py`.
- **Impact:** known overhead/streaming caveats with Starlette
  `BaseHTTPMiddleware`; prefer pure ASGI middleware.

## Low / consistency

### 28. Money is serialized as strings
- `Decimal` → JSON string (`"19.99"`). Documented, but clients must parse.
  Do not change without a frontend migration.

### 29. No pagination metadata
- Product/category lists return bare arrays; no `total`, `next`, or `has_more`.
  Clients must infer the end from `len(items) < limit`.

### 30. `ProductListResponse` omits category and description
- Storefront cards need a detail call for category.

### 31. Order status enum is underused
- `PENDING`/`CANCELED` exist but are never set; responses type `status` as
  `str`.

### 32. Enum naming duality
- DB stores `CUSTOMER`/`ADMIN`/`PENDING`, API emits `customer`/`admin`/
  `pending`. Raw SQL must use the DB names.

### 33. `products.version` default mismatch
- Model default `1`, migration `server_default 0`.

### 34. Embedding comment says 768
- `models/product.py` comment says 768; the column and
  `text-embedding-3-small` are 1536.

### 35. Missing `__init__.py` in some feature packages
- `chat/`, `orders/`, `search/` have no `__init__.py` (namespace packages work,
  but it is inconsistent with `auth/`, `products/`, etc.).

### 36. Duplicate dependency sources
- `requirements.txt` and `pyproject.toml`/`uv.lock` can drift; prefer uv.

### 37. ES client/image version mismatch
- Client `8.16`, Compose image `8.15`. Align versions.

### 38. Unused imports / dead code
- e.g. `hash_password` imported in auth service; `OrderRepository.get_by_id`
  unused; `OrderStatus.PENDING/CANCELED` unused.

## Test baseline

```
tests/unit/test_schemas.py::TestUserResponse::test_valid_response
ValidationError: role — Field required
```

Fix the test or default the field. See [15-testing.md](15-testing.md).
