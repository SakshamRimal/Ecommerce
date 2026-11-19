# Agent Guide — Ecommerce Backend

Async FastAPI ecommerce API with PostgreSQL, Redis, Elasticsearch, arq worker,
OpenAI chat, and OpenTelemetry.

## Start here

- **Full documentation:** [`docs/README.md`](docs/README.md)
- **Feature skills:** [`.agents/README.md`](.agents/README.md)
- **Known bugs / risky areas:** [`docs/18-known-issues.md`](docs/18-known-issues.md)
- **Frontend contract:** [`docs/19-frontend-handoff.md`](docs/19-frontend-handoff.md)

## Non-negotiable conventions

1. **Layering:** `controller.py` → `service.py` → `repository.py`.
   - Controllers: FastAPI routing, `Depends(...)`, status codes, response models.
   - Services: business rules, exceptions, cache invalidation, job enqueueing.
   - Repositories: SQLAlchemy queries only. No HTTP concerns.
2. **Async everywhere.** Use `AsyncSession`; never call blocking DB code in a
   request path. CPU-heavy work (bcrypt) goes through `run_in_executor`.
3. **Schemas:** Pydantic models live in each feature's `schema.py`. Requests and
   responses are separate models.
4. **Errors:** raise `AppException` subclasses (`NotFoundError`,
   `ConflictError`, `UnauthorizedError`, `ForbiddenError`). The global handler
   returns `{"detail": "..."}`.
5. **Migrations:** every model change needs an Alembic revision in
   `src/migrations/versions/`.
6. **Tests:** add unit tests for services and integration tests for routes using
   the existing `AsyncMock` fixtures.

## Commands

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --app-dir src
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run ruff check src tests
```

## Environment

Copy `.env.example` to `.env` and fill in the required values
(`JWT_SECRET_KEY`, `MAIL_*`, `OPENAI_API_KEY`, database credentials).
Settings are loaded by `app.core.config.Settings` and cached with `lru_cache`.

## Current state (verified)

- Tests: **118 passed, 0 failed**, `ruff check src tests` clean.
- Admin CLI entry point (`uv run ecommerce create-admin ...`) is implemented in `src/app/cli.py`.
- All critical/high/medium issues in `docs/18-known-issues.md` have been resolved.
