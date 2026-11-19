# Ecommerce Backend — Documentation

Complete, code-derived documentation for `ecommerce-backend`.

## Read in this order

| # | Document | What it covers |
|---|---|---|
| 01 | [Overview](01-overview.md) | Purpose, stack, features, current state |
| 02 | [Architecture](02-architecture.md) | Layers, request flow, app wiring, module map |
| 03 | [Getting Started](03-getting-started.md) | Local + Docker setup, migrations, admin user |
| 04 | [Configuration](04-configuration.md) | Every environment variable and default |
| 05 | [Database Schema](05-database-schema.md) | Tables, columns, relations, enums, indexes |
| 06 | [API Reference](06-api-reference.md) | Every endpoint, payload, response, error |
| 07 | [Auth & Security](07-auth-and-security.md) | JWT, password hashing, RBAC, headers, CORS |
| 08 | [Catalog](08-catalog.md) | Products, categories, caching, locking |
| 09 | [Cart](09-cart.md) | Cart lifecycle, stock checks, totals |
| 10 | [Orders](10-orders.md) | Checkout, idempotency, row locks, email |
| 11 | [Search](11-search.md) | Elasticsearch, index, semantic search |
| 12 | [AI Chat](12-ai-chat.md) | OpenAI assistant, tools, persistence, embeddings |
| 13 | [Background Jobs](13-background-jobs.md) | arq tasks, worker, backfills |
| 14 | [Observability](14-observability.md) | Logging, metrics, tracing, health |
| 15 | [Testing](15-testing.md) | Test layout, fixtures, commands, baseline |
| 16 | [Deployment](16-deployment.md) | Docker, Compose, production checklist |
| 17 | [Security Posture](17-security.md) | Threats, controls, gaps, hardening plan |
| 18 | [Known Issues](18-known-issues.md) | Verified bugs, quirks, and risks |
| 19 | [Frontend Handoff](19-frontend-handoff.md) | Contract and plan for the future frontend |

## Quick facts

- **API prefix:** `/api/v1`
- **Framework:** FastAPI 0.141, Python 3.12, async SQLAlchemy 2.0
- **Data:** PostgreSQL 16 (+ pgvector), Redis 7, Elasticsearch 8.15
- **Jobs:** arq on Redis
- **Auth:** JWT access + refresh, bcrypt, roles `customer` / `admin`
- **Money:** `Numeric(10,2)`; JSON-encoded as **strings** (`"19.99"`)
- **Test baseline:** 47 passed, 1 failed

## Conventions used in these docs

- "Verified" means confirmed by reading the code and, where practical, running
  it.
- "Gotcha" marks behaviour that is surprising or likely a bug. The consolidated
  list is in [18-known-issues.md](18-known-issues.md).
- Example JSON is what the API actually serializes, not what the Python type
  suggests. Money is a string because Pydantic serializes `Decimal` in JSON mode
  as a decimal string.
