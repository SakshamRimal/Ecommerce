# 01 — Overview

## What this is

`ecommerce-backend` is an async, production-oriented REST API for an online
store. It covers authentication, product/category catalog management, a
per-user shopping cart, checkout, full-text and semantic search, an AI shopping
assistant, background jobs, and observability.

It follows a strict **Controller → Service → Repository** layering and 12-factor
configuration.

## Tech stack

| Area | Technology |
|---|---|
| Framework | FastAPI 0.141 |
| Language | Python 3.12 |
| Package manager | uv |
| Database | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Cache | Redis 7 |
| Search | Elasticsearch 8.15 / 8.16 client |
| Background jobs | arq (Redis) |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Email | `fastapi-mail` + Jinja2 |
| AI | OpenAI (`AsyncOpenAI`), `text-embedding-3-small` |
| Observability | structlog, Prometheus, OpenTelemetry |
| Rate limiting | slowapi |
| Containers | Docker + Docker Compose |

## Features

### Authentication & authorization
- Register, login, refresh, current user.
- Access + refresh JWTs.
- bcrypt password hashing off the event loop.
- Role-based access (`customer`, `admin`).

### Catalog
- Product CRUD with pagination and category filter.
- Category CRUD with automatic slugs.
- Redis-cached product listings.
- Optimistic-locking `version` column (with caveats).
- Elasticsearch indexing and pgvector embeddings in the background.

### Cart
- One lazily-created cart per user.
- Add/merge/update/remove/clear items.
- Stock validation and live totals.

### Orders
- Checkout from the cart in one transaction.
- Row-level stock locking (`SELECT ... FOR UPDATE`).
- Idempotency keys.
- Order snapshots (product name + unit price).
- Confirmation email via background job.

### Search & AI
- Elasticsearch `multi_match` search with fuzziness and field weighting.
- pgvector cosine-distance semantic search.
- OpenAI shopping assistant with four tools and persisted chat history.

### Platform
- Structured JSON logging with request IDs.
- Prometheus metrics and OpenTelemetry traces.
- Security headers, CORS, rate limits.
- Health check, Docker Compose stack, load tests.

## Module map

```
src/app/
├── api/v1/
│   ├── auth/          register, login, refresh, me
│   ├── categories/    category CRUD
│   ├── products/      product CRUD
│   ├── cart/          cart + items
│   ├── orders/        checkout
│   ├── search/        Elasticsearch + semantic search
│   ├── chat/          AI assistant
│   ├── health/        DB health
│   └── router.py      mounts all routers under /api/v1
├── ai/                tool definitions, executor, embeddings
├── core/              config, security, cache, queue, logging, metrics, tracing
├── db/                declarative base, engine, session
├── jobs/              arq tasks, worker, backfills
├── middlewares/       request context, security headers
├── models/            SQLAlchemy models
├── templates/email/   order confirmation HTML
└── main.py            app factory + lifespan
```

## Current state

### Verified working
- App boots and serves all routes (integration route tests pass).
- 47 of 48 unit tests pass.
- Auth, product list/detail, cart, and health have integration coverage.
- Docker Compose defines Postgres, Redis, Elasticsearch, OTel collector, API,
  and worker.

### Incomplete / missing
- `pyproject.toml` declares `ecommerce = "app.cli:main"` but `src/app/cli.py`
  does not exist (no `create-admin` command).
- Orders have only a create endpoint.
- Chat has only a send endpoint.
- Search has no price/category filters or semantic HTTP endpoint.
- Product updates do not re-index or regenerate embeddings.
- No logout, password reset, email verification, or refresh-token revocation.
- One baseline test fails (`UserResponse.role`).

See [18-known-issues.md](18-known-issues.md) for the full list.

## Design principles

1. **Explicit layers.** HTTP, business rules, and persistence stay separate.
2. **Async I/O.** All DB, cache, HTTP, and queue calls are async.
3. **Fail loudly in requests, resiliently at boot.** Domain errors map to 4xx;
   optional infrastructure (ES, OTel, migrations) logs and continues.
4. **DB is the source of truth.** Cache and search indexes are derived.
5. **Side effects are deferred.** Emails, indexing, and embeddings run in arq.
6. **UUID identifiers.** No enumerable integer IDs.
