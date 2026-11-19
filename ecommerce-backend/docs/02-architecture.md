# 02 — Architecture

## Layering

```
┌──────────────┐   HTTP    ┌───────────────────┐
│   Client     │ ────────▶ │  Controller        │  routing, Depends, status,
└──────────────┘           │  (api/v1/*/ctrl)   │  response_model
                           └─────────┬─────────┘
                                     │
                           ┌─────────▼─────────┐
                           │  Service           │  business rules, domain errors,
                           │                    │  cache invalidation, jobs
                           └─────────┬─────────┘
                                     │
                           ┌─────────▼─────────┐
                           │  Repository        │  SQLAlchemy only
                           └─────────┬─────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
        PostgreSQL              Redis cache             arq queue
                                         ↘ Elasticsearch, OpenAI, SMTP
```

### Controller (`controller.py`)
- Owns the `APIRouter` and path/status/response declarations.
- Wires dependencies via `Depends`.
- Contains no business rules and no SQL.
- Builds a service through a module-level factory, for example:

```python
def get_product_service(session: AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(ProductRepository(session), CategoryRepository(session))
```

### Service (`service.py`)
- Receives repositories/clients via `__init__`.
- Enforces invariants and raises `AppException` subclasses.
- Coordinates cache invalidation and background jobs.
- Maps ORM models to response schemas.

### Repository (`repository.py`)
- Receives `AsyncSession`.
- Contains only SQLAlchemy queries (selects, writes, locks, eager loading).
- Returns ORM models or `None`; no HTTP/Pydantic concerns.

## Request lifecycle

1. **Middleware**
   - `RequestContextMiddleware` assigns/propagates `X-Request-ID` and binds
     `request_id`, `path`, `method` to structlog.
   - `SecurityHeadersMiddleware` appends security headers to every response.
   - `CORSMiddleware` enforces the configured origins.
2. **Rate limiting** (slowapi) on login and chat.
3. **Routing** to the feature controller.
4. **Dependency injection** creates the `AsyncSession` and service.
5. **Service/repository** perform the work.
6. **Commit** at the end of the request by `get_db_session`; rollback on
   exception.
7. **Response** serialized by Pydantic; Prometheus/OTel observe it.

## Database session

`src/app/db/session.py`:

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug,
)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

async def get_db_session():
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

Notes:
- `expire_on_commit=False` means objects remain usable after commit.
- `autoflush=False` means explicit `flush()`/`commit()` is required.
- Repositories sometimes commit themselves (auth, products, categories), while
  cart/orders rely on the request-scoped commit. This is inconsistent; see
  [18-known-issues.md](18-known-issues.md).

## App factory and lifespan

`src/app/main.py`:

```python
async def lifespan(app):
    configure seed/startup work
    alembic upgrade head          # /app/alembic.ini (Docker only)
    ensure_product_index_exists() # ES
    yield
    engine.dispose()
    close_es_client()
    close_job_queue()
```

The app then:
- registers the `AppException` handler → `{"detail": ...}`
- installs slowapi and its 429 handler
- adds security headers, request context, CORS
- mounts `api_router` at `/api/v1`
- exposes Prometheus metrics at `/metrics`
- configures OpenTelemetry tracing

## Shared clients

| Client | Pattern | File |
|---|---|---|
| Redis cache | module-level connection pool | `core/cache.py` |
| Elasticsearch | lazy global singleton | `core/elasticsearch.py` |
| arq queue | lazy global singleton | `core/job_queue.py` |
| OpenAI | per-service `AsyncOpenAI` instance | `ai/*`, `chat/service.py` |
| DB engine | module-level engine | `db/session.py` |

## Error handling

Domain exceptions live in `core/exceptions.py`:

| Exception | Status |
|---|---|
| `AppException` | 500 |
| `ConflictError` | 409 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `NotFoundError` | 404 |

Handled globally in `main.create_app`:

```json
{ "detail": "Product with id '…' not found" }
```

FastAPI's own validation errors keep their standard shape:
`{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.

## Module responsibilities

| Layer | Allowed to know about |
|---|---|
| Controller | FastAPI, schemas, services |
| Service | schemas, repositories, core utilities, models |
| Repository | SQLAlchemy, models |
| Core | settings, external clients, cross-cutting helpers |
| Jobs | DB session, models, core clients, AI/email |

## Extension checklist

Adding a feature:
1. Model + migration.
2. `schema.py` request/response models.
3. `repository.py` queries.
4. `service.py` business rules.
5. `controller.py` routes + DI.
6. Register in `api/v1/router.py`.
7. Unit + integration tests.
8. Update `docs/06-api-reference.md`, `docs/19-frontend-handoff.md`, and add a
   `.agents/skills/<feature>/SKILL.md`.
