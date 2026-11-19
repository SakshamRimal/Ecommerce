---
name: Backend Testing
description: Use when adding or fixing unit, integration, or load tests, or when mocking the database and services in this backend.
---

# Backend Testing

## When to use

- Adding tests for a service, schema, endpoint, or security helper.
- Fixing a failing test.
- Setting up mocks or dependency overrides.
- Running load tests.

## Layout

```
tests/
├── conftest.py                 # fixtures + ASGI client
├── unit/
│   ├── test_auth_service.py
│   ├── test_exceptions.py
│   ├── test_health_service.py
│   ├── test_schemas.py
│   └── test_security.py
├── integration/
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_products.py
│   └── test_routes.py
└── load/
    └── locustfile.py
```

## Patterns

- `asyncio_mode = "auto"` is configured, so async tests need no decorator.
- `client` fixture uses `httpx.AsyncClient` + `ASGITransport`; it overrides
  `get_db_session` with an `AsyncMock` session.
- Endpoint tests override the service factory, e.g.
  `app.dependency_overrides[get_product_service] = lambda: mock_service`.
- Always pop overrides after the test (existing tests do this manually).
- Unit tests use `AsyncMock` repositories.
- `pytest` `pythonpath = ["src"]` so imports are `app.*`.

## Rules

1. Prefer testing the service with a mocked repository for business rules.
2. Use integration tests for routing, status codes, auth guards, and validation.
3. Don't hit real Postgres/Redis/ES in unit or integration tests.
4. Keep overrides scoped; leakage causes flaky cross-test failures.
5. For new response fields, update both schema tests and endpoint tests.

## Known failure (baseline)

`tests/unit/test_schemas.py::TestUserResponse::test_valid_response` fails because
`UserResponse` now requires `role` but the test omits it. Either add
`role="customer"` in the test or give the field a default. Do not "fix" it by
removing the field from the schema.

Current baseline: **47 passed, 1 failed**.

## Commands

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest -q
uv run pytest --cov=app --cov-report=term-missing
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Related

- `docs/15-testing.md`
- `docs/18-known-issues.md`
