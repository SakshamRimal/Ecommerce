# 13 — Background Jobs

## Why

Writes that touch slow/external systems (Elasticsearch, OpenAI embeddings, SMTP)
are deferred so the HTTP request stays fast. arq is a Redis-backed async job
queue.

## Components

| Component | File |
|---|---|
| Producer (enqueue) | `src/app/core/job_queue.py` |
| Tasks | `src/app/jobs/tasks.py` |
| Worker settings | `src/app/jobs/worker.py` |
| Backfill: embeddings | `src/app/jobs/backfill_embeddings.py` |
| Backfill: search | `src/app/jobs/backfill_search_index.py` |
| Email renderer | `src/app/core/email.py` |
| Email template | `src/app/templates/email/order_confirmation.html` |

## Queue

```python
_pool: ArqRedis | None = None

async def get_job_queue() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(settings.arq_redis_url))
    return _pool
```

- Uses `ARQ_REDIS_URL` (default DB 1, separate from the cache DB 0).
- The pool is a lazy singleton, closed in the app lifespan.
- Jobs are enqueued by name, e.g. `queue.enqueue_job("index_product_task", id)`.

## Tasks

### `index_product_task(ctx, product_id)`
- Loads the product with `joinedload(Product.category)`.
- No-ops with a warning if the product is gone.
- Upserts the ES document (index + id).
- Used on product create and by the search backfill.

### `delete_product_from_index_task(ctx, product_id)`
- Deletes the ES document by ID.
- Catches all exceptions and logs a warning (best effort).

### `generate_product_embedding_task(ctx, product_id)`
- Loads product + category.
- Builds `name-category-description` text.
- Calls `text-embedding-3-small`.
- Stores the 1536-dim vector on `products.embedding`.
- Used on create and by the embedding backfill.

### `send_order_confirmation_task(ctx, order_id, user_email, user_full_name)`
- Loads the order with items.
- Renders the Jinja email template.
- Sends via `fastapi-mail`.
- Catches send failures and logs them; the order is unaffected.

## Worker

```python
class WorkerSettings:
    functions = [
        index_product_task,
        delete_product_from_index_task,
        send_order_confirmation_task,
        generate_product_embedding_task,
    ]
    redis_settings = RedisSettings.from_dsn(settings.arq_redis_url)
    max_jobs = 10
    job_timeout = 60
```

Run:

```bash
uv run arq app.jobs.worker.WorkerSettings
```

Docker Compose service `worker` builds the same image and runs the same command
with `working_dir: /app/src`.

## Backfills

These are standalone scripts, not jobs:

```bash
# embeddings for products with embedding IS NULL
uv run python -m app.jobs.backfill_embeddings

# every product → Elasticsearch
uv run python -m app.jobs.backfill_search_index
```

They call the task functions directly with `ctx={}`.

## Delivery guarantees

- arq jobs run **at least once**; make tasks idempotent.
- ES index/delete are idempotent.
- Embedding generation overwrites the vector (idempotent).
- Email is **not** idempotent: a retry sends a duplicate email.
- Jobs open their own `AsyncSessionFactory()` session and commit internally.

## Failure modes

| Failure | Effect |
|---|---|
| Redis down while enqueueing | Request raises after the DB commit (order/product created) |
| ES down during indexing | Job raises; arq retries/logs |
| OpenAI down during embedding | Job raises; vector stays null |
| SMTP down | Task catches and logs; no retry |
| Worker down | Jobs queue up in Redis |

## Recommended improvements

1. Add job retry/backoff configuration per task.
2. Track enqueue failures explicitly (outbox pattern) so committed orders always
   get emails eventually.
3. Make email idempotent with an `order_id` dedupe key.
4. Add re-index/embedding jobs on product update.
5. Add a dead-letter queue/alerting.
6. Add a scheduled reconciliation job (DB vs ES vs embeddings).
