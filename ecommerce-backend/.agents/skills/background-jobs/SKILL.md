---
name: Background Jobs
description: Use when adding or changing arq workers, product indexing, embedding generation, order confirmation email, or backfill scripts.
---

# Background Jobs

## When to use

- Adding a task to the arq worker.
- Changing product indexing / embedding / email jobs.
- Building a backfill or one-off maintenance script.
- Debugging job execution or worker settings.

## Files

| Concern | File |
|---|---|
| arq pool (producer) | `src/app/core/job_queue.py` |
| Tasks | `src/app/jobs/tasks.py` |
| Worker settings | `src/app/jobs/worker.py` |
| Embedding backfill | `src/app/jobs/backfill_embeddings.py` |
| Search index backfill | `src/app/jobs/backfill_search_index.py` |
| Email sender | `src/app/core/email.py` |
| Email template | `src/app/templates/email/order_confirmation.html` |

## Tasks

| Task | Trigger | Purpose |
|---|---|---|
| `index_product_task(ctx, product_id)` | product create | upsert product into Elasticsearch |
| `delete_product_from_index_task(ctx, product_id)` | product delete | remove ES document |
| `generate_product_embedding_task(ctx, product_id)` | product create, backfill | compute + store pgvector embedding |
| `send_order_confirmation_task(ctx, order_id, email, name)` | order create | render + send confirmation email |

## Worker

`WorkerSettings` registers all four functions, uses `ARQ_REDIS_URL`, `max_jobs=10`,
`job_timeout=60`. Started with:

```bash
uv run arq app.jobs.worker.WorkerSettings
```

Docker Compose runs it as the `worker` service (`working_dir: /app/src`).

## Rules

1. Jobs must be idempotent; retries can happen.
2. Open a fresh `AsyncSessionFactory()` session inside a job; never reuse a
   request session.
3. Catch and log failures for non-critical side effects (email, ES delete).
4. Keep jobs short (< 60 s) or raise `job_timeout`.
5. Enqueue from services **after** the DB commit for writes whose side effect
   must not precede persistence.

## Gotchas

- Tasks that mutate state use their own session and commit; they are not part of
  the request transaction.
- `index_product_task` logs "not found" and returns, so a job can silently no-op.
- Product updates never enqueue re-index/embedding jobs.
- The email task catches send failures, so failed emails are only in logs.
- Backfill scripts are synchronous `asyncio.run(...)` entry points, not arq jobs.

## Verify

```bash
# with Redis + worker running
uv run python -m app.jobs.backfill_search_index
uv run python -m app.jobs.backfill_embeddings
```

## Related

- `docs/13-background-jobs.md`
- `docs/10-orders.md`
- `docs/11-search.md`
