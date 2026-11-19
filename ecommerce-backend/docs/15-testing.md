# 15 — Testing

## Layout

```
tests/
├── conftest.py
├── unit/
│   ├── test_auth_service.py     service logic with mocked repo
│   ├── test_exceptions.py       status codes + inheritance
│   ├── test_health_service.py   healthy/degraded paths
│   ├── test_schemas.py          Pydantic validation
│   └── test_security.py         bcrypt + JWT
├── integration/
│   ├── test_auth.py             endpoints with service overrides
│   ├── test_health.py           real health route
│   ├── test_products.py         product routes + admin guards
│   └── test_routes.py           route registration + OpenAPI
└── load/
    └── locustfile.py
```

## Configuration

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
```

`asyncio_mode = "auto"` means `async def test_*` needs no decorator.

## Fixtures (`tests/conftest.py`)

| Fixture | Purpose |
|---|---|
| `sample_user` | customer ORM instance |
| `sample_admin_user` | admin ORM instance |
| `mock_session` | `AsyncMock` session |
| `mock_health_repository` | repo returning `True` |
| `mock_auth_repository` | repo with async methods |
| `client` | `httpx.AsyncClient` over `ASGITransport(app)` with DB override |

The `client` fixture overrides `get_db_session` with an async generator that
yields an `AsyncMock` session, so integration tests never touch PostgreSQL.

## Adding an endpoint test

```python
from unittest.mock import AsyncMock
from app.main import app
from app.api.v1.products.controller import get_product_service

async def test_list_products(client):
    service = AsyncMock()
    service.list_products = AsyncMock(return_value=[])
    app.dependency_overrides[get_product_service] = lambda: service
    try:
        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
    finally:
        app.dependency_overrides.pop(get_product_service, None)
```

## Adding a service test

```python
async def test_register_duplicate(mock_auth_repository):
    mock_auth_repository.get_by_email = AsyncMock(return_value=existing_user)
    service = AuthService(mock_auth_repository)
    with pytest.raises(ConflictError):
        await service.register(payload)
```

## Test strategy

- **Unit:** business rules, schemas, security helpers. Mock repositories.
- **Integration:** routing, status codes, auth guards, validation, OpenAPI.
- **Load:** Locust simulates login + browsing + search + health.

Current integration tests do not exercise real SQL, Elasticsearch, Redis, or the
worker. There is no end-to-end suite against the Compose stack.

## Baseline (verified)

```
uv run pytest tests/unit -q
# 1 failed, 47 passed
```

The single failure:

```
tests/unit/test_schemas.py::TestUserResponse::test_valid_response
ValidationError: role — Field required
```

Cause: `UserResponse` gained a required `role` field, but the test still omits
it. Fix the test by passing `role="customer"` (preferred) or give the field a
default. Do not delete the field.

## Commands

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest -q
uv run pytest -q --cov=app --cov-report=term-missing
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Gaps

| Area | Coverage |
|---|---|
| Auth | good unit + integration |
| Security helpers | good |
| Health | good |
| Products | basic integration |
| Categories | route existence only |
| Cart | route existence only |
| Orders | none |
| Search | route existence with patched service |
| Chat | none |
| Jobs | none |
| Repositories | none (no real DB) |
| Migrations | none |

Priorities: orders (stock/idempotency), cart mutations, jobs, and a real
DB-backed integration suite.
