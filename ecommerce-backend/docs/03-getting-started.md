# 03 — Getting Started

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16+ with the `vector` extension (use the `pgvector/pgvector:pg16`
  image)
- Redis 7+
- Elasticsearch 8.15+
- Optional: Docker + Docker Compose, an SMTP server, an OpenAI API key

## Local setup

```bash
cd ecommerce-backend

# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# edit .env — at minimum JWT_SECRET_KEY, MAIL_*, OPENAI_API_KEY

# 3. Start Postgres / Redis / Elasticsearch (Compose is easiest)
docker compose up -d postgres redis elasticsearch otel-collector

# 4. Apply migrations
uv run alembic upgrade head

# 5. Run the API
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir src

# 6. (separate terminal) run the worker
uv run arq app.jobs.worker.WorkerSettings
```

Then open:

| URL | Purpose |
|---|---|
| <http://localhost:8000/docs> | Swagger UI |
| <http://localhost:8000/redoc> | ReDoc |
| <http://localhost:8000/openapi.json> | OpenAPI schema |
| <http://localhost:8000/api/v1/health> | Health |
| <http://localhost:8000/metrics> | Prometheus metrics |

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Services started: `postgres`, `redis`, `elasticsearch`, `otel-collector`, `api`,
`worker`.

- The API container runs migrations from `/app/alembic.ini` on startup.
- The worker runs `arq app.jobs.worker.WorkerSettings` with `working_dir: /app/src`.
- Postgres is the `pgvector/pgvector:pg16` image.
- Elasticsearch runs single-node with security disabled (development only).

## Required environment

The app will not start without these `Settings` fields (they have no defaults):

- `JWT_SECRET_KEY`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_SERVER`
- `OPENAI_API_KEY`

See [04-configuration.md](04-configuration.md) for the full table.

## Database migrations

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic revision --autogenerate -m "describe change"
uv run alembic downgrade -1
```

Migration files live in `src/migrations/versions/` and must form a single linear
chain.

## Create an admin user

The README advertises `uv run ecommerce create-admin ...`, but **the CLI module
does not exist** (`src/app/cli.py` is missing). Until it is restored, create an
admin with a one-off script:

```bash
cd ecommerce-backend
PYTHONPATH=src uv run python - <<'PY'
import asyncio
from app.core.security import hash_password_async
from app.db.session import AsyncSessionFactory
from app.models.user import User, UserRole

async def main():
    async with AsyncSessionFactory() as session:
        user = User(
            email="admin@example.com",
            hashed_password=await hash_password_async("change-me-please"),
            full_name="Admin",
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()
        print("admin created:", user.email)

asyncio.run(main())
PY
```

Then log in:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=change-me-please'
```

## Smoke test

```bash
# health
curl -s http://localhost:8000/api/v1/health

# register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"shopper@example.com","password":"password123","full_name":"Shopper"}'

# login (form-encoded!)
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=shopper@example.com&password=password123'
```

## Running tests

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest -q
```

Baseline: **47 passed, 1 failed** (a stale schema test). See
[15-testing.md](15-testing.md).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ValidationError` for `jwt_secret_key` at import | Missing `.env` / env var |
| `migrations_failed` warning at startup | Not running in Docker (hardcoded `/app/alembic.ini`) |
| Search returns 500 | Elasticsearch not running or index missing |
| Chat fails | `OPENAI_API_KEY` missing/invalid |
| Orders 500 after commit | Redis/arq unavailable while enqueueing email |
| 429 on login/chat | slowapi rate limit (`30/min`, `10/min`) |
| Empty product list after seeding | ES backfill not run / cache stale |
