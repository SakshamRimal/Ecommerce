---
name: Backend Architecture
description: Use when adding or restructuring backend modules, wiring FastAPI dependencies, or reviewing the Controller-Service-Repository layering.
---

# Backend Architecture

## When to use

- Adding a new feature/module under `src/app/api/v1/`.
- Deciding where logic belongs.
- Wiring dependencies or app-level middleware.
- Reviewing a change for architectural consistency.

## Structure

```
src/app/
├── api/v1/<feature>/
│   ├── controller.py   # routes + Depends wiring
│   ├── service.py      # business rules
│   ├── repository.py   # SQLAlchemy queries
│   └── schema.py       # Pydantic request/response models
├── ai/                 # OpenAI tools, tool executor, embeddings
├── core/               # config, security, cache, queue, logging, metrics, tracing
├── db/                 # Base + async engine/session
├── jobs/               # arq tasks, worker settings, backfills
├── middlewares/        # request context, security headers
├── models/             # SQLAlchemy models
├── templates/email/    # Jinja email templates
├── main.py             # app factory + lifespan
└── api/v1/router.py    # mounts feature routers
```

## Request flow

```
HTTP → middleware → controller → service → repository → PostgreSQL
                              ↘ cache / Elasticsearch / arq queue
```

## Rules

1. **Controller** does not run business logic or SQL.
   - Use `Depends(get_db_session)` and a local `get_<feature>_service` factory.
   - Declare `response_model` and `status_code` explicitly.
   - Guard admin routes with `dependencies=[Depends(require_admin)]` or a
     `current_user: User = Depends(get_current_user)` parameter.
2. **Service** receives repositories in `__init__`. It raises domain exceptions
   and owns side effects (cache invalidation, job enqueueing).
3. **Repository** receives `AsyncSession` in `__init__`. Only SQLAlchemy here.
   Return models or `None`; never Pydantic models.
4. **Schemas** are per feature. Response models use
   `model_config = ConfigDict(from_attributes=True)` when validating ORM objects.
5. **Dependencies** are created per request. Do not store request state in
   module globals except deliberately shared clients (Redis pool, ES client,
   arq pool).

## Adding a new feature — checklist

1. Create `api/v1/<feature>/__init__.py`.
2. Add ORM model(s) in `models/` and export in `models/__init__.py`.
3. Create an Alembic migration.
4. Add `schema.py`, `repository.py`, `service.py`, `controller.py`.
5. Register the router in `api/v1/router.py`.
6. Add tests (unit service + integration route).
7. Add a skill under `.agents/skills/<feature>/` and a doc under `docs/` if the
   feature is user-facing.
8. Update `docs/06-api-reference.md` and `docs/19-frontend-handoff.md`.

## Existing module map

| Module | Prefix | Auth |
|---|---|---|
| health | `/api/v1/health` | public |
| auth | `/api/v1/auth` | mixed |
| categories | `/api/v1/categories` | mixed (detail/admin writes are admin) |
| products | `/api/v1/products` | public reads, admin writes |
| cart | `/api/v1/cart` | authenticated |
| orders | `/api/v1/orders` | authenticated |
| search | `/api/v1/search` | public |
| chat | `/api/v1/chat` | authenticated |

## Verify

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration/test_routes.py -q
uv run ruff check src
```

## Related

- `docs/02-architecture.md`
- `docs/06-api-reference.md`
- `docs/18-known-issues.md`
