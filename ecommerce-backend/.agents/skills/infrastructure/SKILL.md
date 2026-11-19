---
name: Infrastructure and Observability
description: Use when changing settings, Redis cache, Elasticsearch client, OpenTelemetry tracing, structured logging, Prometheus metrics, middleware, CORS, or rate limiting.
---

# Infrastructure & Observability

## When to use

- Adding/changing an environment variable.
- Redis caching or invalidation.
- Logging, tracing, metrics.
- Middleware, CORS, security headers, rate limits.
- App startup/shutdown/lifespan.
- Docker Compose or Dockerfile.

## Files

| Concern | File |
|---|---|
| Settings | `src/app/core/config.py` |
| App factory + lifespan | `src/app/main.py` |
| Cache | `src/app/core/cache.py` |
| Elasticsearch client | `src/app/core/elasticsearch.py` |
| Search index | `src/app/core/search_index.py` |
| Job queue | `src/app/core/job_queue.py` |
| Logging | `src/app/core/logging.py` |
| Tracing | `src/app/core/tracing.py` |
| Metrics | `src/app/core/metrics.py` |
| Rate limiter | `src/app/core/rate_limiter.py` |
| Request context | `src/app/middlewares/request_context.py` |
| Security headers | `src/app/middlewares/security_headers.py` |
| Compose | `docker-compose.yml` |
| Image | `Dockerfile` |

## Settings

`Settings(BaseSettings)` reads `.env` at the project root (3 levels above
`core/config.py`) and environment variables. `get_settings()` is `lru_cache`d.
Required fields without defaults: `JWT_SECRET_KEY`, `MAIL_USERNAME`,
`MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_SERVER`, `OPENAI_API_KEY`.
`database_url` is computed for asyncpg.

## Middleware order

Starlette applies middleware in reverse registration order. `create_app` adds:

1. `SecurityHeadersMiddleware`
2. `RequestContextMiddleware`
3. `CORSMiddleware`
4. Prometheus instrumentator + OTel

`RequestContextMiddleware` binds `request_id`, `path`, `method` to structlog
context, logs completion with duration, and echoes `X-Request-ID`.

`SecurityHeadersMiddleware` adds `nosniff`, `DENY` framing, HSTS, and
`strict-origin-when-cross-origin`.

## Caching

- Redis pool from `REDIS_URL`, `decode_responses=True`.
- Helpers: `cache_get`, `cache_set`, `cache_delete_pattern`.
- Default TTL `CACHE_TTL_SECONDS` (300).
- Only product listings are cached today.

## Observability

- **Logs:** structlog; JSON in non-debug, pretty console in debug.
- **Metrics:** `prometheus-fastapi-instrumentator` at `/metrics`; custom counters
  `orders_created_total`, `orders_failed_total{reason}`, histogram
  `order_value_dollars`.
- **Tracing:** OTel OTLP gRPC to `OTEL_EXPORTER_ENDPOINT`; skips exporter if the
  endpoint is unreachable; instruments SQLAlchemy.
- **Health:** `/api/v1/health` checks DB only.

## Rate limiting

`slowapi` limiter keyed by remote address. Applied to login (`30/minute`) and
chat (`10/minute`). Storage is in-memory per process by default — limits are
**not** shared across workers/replicas.

## Rules

1. Add new settings to both `Settings` and `.env.example`.
2. Never log secrets, tokens, passwords, or full prompts.
3. Use `Decimal` for money in metrics/logging where possible.
4. Keep startup resilient: log-and-continue for optional dependencies
   (migrations, ES, OTel).
5. Security headers and request IDs should apply to every HTTP response.

## Gotchas

- `main.py` runs Alembic with a hardcoded `/app/alembic.ini`; outside Docker the
  migration step fails and is only logged as a warning.
- Lifespan only closes the DB engine, ES client, and arq pool; the Redis cache
  pool is not explicitly closed.
- Health does not check Redis, Elasticsearch, or the worker.
- CORS defaults to `http://localhost:3000` only.
- Rate limiting is per-process (not Redis-backed).
- `add_trace_context` is defined but not added to the structlog processor chain.

## Verify

```bash
curl -s localhost:8000/api/v1/health
curl -s localhost:8000/metrics | head
```

## Related

- `docs/04-configuration.md`
- `docs/14-observability.md`
- `docs/16-deployment.md`
- `docs/17-security.md`
