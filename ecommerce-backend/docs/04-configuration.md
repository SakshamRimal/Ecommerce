# 04 — Configuration

Configuration is a Pydantic `BaseSettings` class in
`src/app/core/config.py`. It reads, in order:

1. Environment variables
2. `.env` at the backend project root (`ecommerce-backend/.env`)

Matching is case-insensitive and unknown keys are ignored. Settings are cached
with `@lru_cache`, so changes require a process restart.

## Required values (no defaults)

| Variable | Why |
|---|---|
| `JWT_SECRET_KEY` | Signing access/refresh tokens |
| `MAIL_USERNAME` | SMTP auth |
| `MAIL_PASSWORD` | SMTP auth |
| `MAIL_FROM` | Sender address |
| `MAIL_SERVER` | SMTP host |
| `OPENAI_API_KEY` | Chat + embeddings |

## Full reference

### App

| Variable | Default | Notes |
|---|---|---|
| `APP_NAME` | `ecommerce-backend` | OTel service name / FastAPI title |
| `APP_ENV` | `local` | `local` / `staging` / `production` |
| `DEBUG` | `false` | Enables SQL echo + console logs |
| `LOG_LEVEL` | `INFO` | structlog filtering threshold |
| `HOST` | `0.0.0.0` | Declared, not used by uvicorn CLI |
| `PORT` | `8000` | Declared, not used by uvicorn CLI |

### PostgreSQL

| Variable | Default |
|---|---|
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` (example uses a placeholder) |
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `ecommerce` |
| `DATABASE_POOL_SIZE` | `10` |
| `DATABASE_MAX_OVERFLOW` | `20` |

`database_url` is computed:
`postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}`.

### JWT

| Variable | Default |
|---|---|
| `JWT_SECRET_KEY` | **required** |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |

### CORS

| Variable | Default |
|---|---|
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:3000"]` |

Provided as a JSON array when set via env, e.g.
`CORS_ALLOWED_ORIGINS=["https://shop.example.com"]`.

### Redis / cache

| Variable | Default |
|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` |
| `CACHE_TTL_SECONDS` | `300` |
| `ARQ_REDIS_URL` | `redis://localhost:6379/1` |

### Email

| Variable | Default |
|---|---|
| `MAIL_USERNAME` | **required** |
| `MAIL_PASSWORD` | **required** |
| `MAIL_FROM` | **required** |
| `MAIL_FROM_NAME` | `YourShop` |
| `MAIL_SERVER` | **required** |
| `MAIL_PORT` | `2525` |
| `MAIL_STARTTLS` | `true` |
| `MAIL_SSL_TLS` | `false` |

### Elasticsearch

| Variable | Default |
|---|---|
| `ELASTICSEARCH_URL` | `http://localhost:9200` |
| `ELASTICSEARCH_PRODUCTS_INDEX` | `products` |

### OpenTelemetry

| Variable | Default |
|---|---|
| `OTEL_EXPORTER_ENDPOINT` | `localhost:4317` |

If the endpoint is unreachable at startup, tracing is configured without an
exporter and a warning is logged.

### OpenAI

| Variable | Default |
|---|---|
| `OPENAI_API_KEY` | **required** |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | `800` |
| `CHAT_MAX_HISTORY_MESSAGES` | `20` |

## Docker Compose overrides

Compose rewrites service hostnames for containers:

| Variable | Compose value |
|---|---|
| `POSTGRES_HOST` | `postgres` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `ARQ_REDIS_URL` | `redis://redis:6379/1` |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` |
| `OTEL_EXPORTER_ENDPOINT` | `otel-collector:4317` |

## Secrets hygiene

- `.env` is git-ignored; `.env.example` is the documented template.
- Never log `JWT_SECRET_KEY`, passwords, tokens, or `OPENAI_API_KEY`.
- `MAIL_*` credentials and `OPENAI_API_KEY` should be provided by the platform
  secret store in production.
- Rotate `JWT_SECRET_KEY` invalidates every issued token (there is no key ID).

## Validation behaviour

Pydantic fails at startup if a required field is missing. Because settings are
imported by `db/session.py`, `core/cache.py`, `core/elasticsearch.py`,
`core/job_queue.py`, `core/email.py`, and `core/security.py` at import time, a
missing value surfaces as an import-time `ValidationError` rather than a clean
startup message.
