# 16 — Deployment

## Dockerfile

Multi-stage-style single stage:

```dockerfile
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ ./src/
COPY alembic.ini ./
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
```

Notes:
- Dependencies are cached separately from source.
- `src/migrations/` is inside `src/`, so migrations ship with the image.
- `alembic.ini` is copied to `/app/alembic.ini`; this is exactly the path used
  by `main.py` at startup.
- Runs as root by default; add a non-root user for production.

## Compose stack

| Service | Image | Port | Notes |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | healthcheck `pg_isready` |
| `redis` | `redis:7-alpine` | 6379 | cache + queue |
| `elasticsearch` | `elasticsearch:8.15.0` | 9200 | single-node, security disabled |
| `otel-collector` | `otel/opentelemetry-collector` | 4317/4318 | gRPC/HTTP OTLP |
| `api` | local build | 8000 | migrates on startup |
| `worker` | local build | — | `arq app.jobs.worker.WorkerSettings` |

The API waits for Postgres healthy and the other services started. Worker depends
on Postgres healthy, Redis, and the collector.

```bash
docker compose up --build
docker compose logs -f api
docker compose down            # keep volumes
docker compose down -v         # wipe data
```

## Startup sequence

1. Container starts uvicorn.
2. `lifespan` runs `alembic upgrade head` with `/app/alembic.ini`.
   Failure is logged as a warning and startup continues.
3. `ensure_product_index_exists()` creates the ES index if missing (best effort).
4. App starts serving.
5. On shutdown: dispose DB engine, close ES client, close arq pool.

## Production checklist

### Required
- [ ] Provide all required env vars via secrets (not a baked `.env`).
- [ ] Set `APP_ENV=production`, `DEBUG=false`.
- [ ] Use a strong `JWT_SECRET_KEY` (32+ random bytes) and rotate periodically.
- [ ] Point `POSTGRES_*` at a managed Postgres with the `vector` extension.
- [ ] Point `REDIS_URL` at a managed Redis; use a separate DB for `ARQ_REDIS_URL`.
- [ ] Point `ELASTICSEARCH_URL` at a secured cluster (auth + TLS).
- [ ] Set `CORS_ALLOWED_ORIGINS` to the real frontend origins.
- [ ] Configure SMTP with a real provider and verified sender.
- [ ] Set `OTEL_EXPORTER_ENDPOINT` to your collector.
- [ ] Terminate TLS at a proxy/ingress; keep HSTS enabled.
- [ ] Run migrations as a deploy step, not only in app startup.
- [ ] Add readiness/liveness probes (`/api/v1/health` is DB-only today).
- [ ] Run as a non-root user.
- [ ] Set CPU/memory limits and DB pool sizes appropriate to replicas.
- [ ] Configure log aggregation for stdout JSON logs.

### Scale-out notes
- `slowapi` uses in-memory storage: rate limits are per replica. Move to Redis
  storage or an API gateway.
- The arq worker is a singleton pool in each process; run at least one replica
  and monitor queue depth.
- Cache invalidation uses `SCAN`; fine at small scale, expensive at large key
  counts.
- Elasticsearch single-node is for development only.
- Auto-migration on every API replica can race; run it once in a job/init
  container.

### Backups
- PostgreSQL: automated backups + PITR. This is the source of truth.
- Elasticsearch: rebuildable from Postgres via the backfill script.
- Embeddings: rebuildable via the embedding backfill (costs OpenAI tokens).
- Redis: ephemeral; losing it loses cache and queued jobs.

## Health/readiness

| Check | Current |
|---|---|
| Process up | implicit |
| DB | `GET /api/v1/health` |
| Redis | not checked |
| Elasticsearch | not checked |
| Worker | not checked |

Add a `/health/ready` that checks all dependencies before routing traffic.

## Local vs Docker differences

| Concern | Local | Docker |
|---|---|---|
| Migrations at startup | fails (hardcoded `/app/alembic.ini`) | works |
| DB host | `localhost` | `postgres` |
| Redis | `localhost` | `redis` |
| ES | `localhost:9200` | `elasticsearch:9200` |
| OTel | `localhost:4317` | `otel-collector:4317` |
