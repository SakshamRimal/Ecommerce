---
name: API Contract
description: Use when adding or changing request/response shapes, status codes, auth requirements, or anything the frontend consumes.
---

# API Contract

## When to use

- Designing a new endpoint or changing an existing payload.
- Updating frontend-facing types.
- Reviewing backwards compatibility.
- Writing OpenAPI/API docs.

## Conventions

- Base path: `/api/v1`.
- JSON for all bodies except `POST /auth/login`, which is form-encoded.
- IDs are UUID strings.
- Money is serialized as a decimal string or number by Pydantic (`Decimal`).
- Timestamps are not currently returned by any response schema.
- Auth uses `Authorization: Bearer <access_token>`.
- Errors from `AppException`: `{"detail": "<message>"}`.
- Validation errors: FastAPI's `{"detail": [{loc, msg, type}]}`.
- Health is `GET /api/v1/health` (public).

## Endpoint summary

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/auth/register` | public | 201 `UserResponse` |
| POST | `/auth/login` | public | 200 `TokenResponse` |
| POST | `/auth/refresh` | public | 200 `TokenResponse` |
| GET | `/auth/me` | bearer | 200 `UserResponse` |
| GET | `/products` | public | 200 `ProductListResponse[]` |
| GET | `/products/{id}` | public | 200 `ProductResponse` |
| POST | `/products` | admin | 201 `ProductResponse` |
| PATCH | `/products/{id}` | admin | 200 `ProductResponse` |
| DELETE | `/products/{id}` | admin | 204 |
| GET | `/categories` | public | 200 `CategoryResponse[]` |
| GET | `/categories/{id}` | admin | 200 `CategoryResponse` |
| POST | `/categories` | admin | 201 `CategoryResponse` |
| PATCH | `/categories/{id}` | admin | 200 `CategoryResponse` |
| DELETE | `/categories/{id}` | admin | 204 |
| GET | `/cart` | bearer | 200 `CartResponse` |
| POST | `/cart/items` | bearer | 201 `CartResponse` |
| PATCH | `/cart/items/{product_id}` | bearer | 200 `CartResponse` |
| DELETE | `/cart/items/{product_id}` | bearer | 200 `CartResponse` |
| DELETE | `/cart` | bearer | 200 `CartResponse` |
| POST | `/orders` | bearer | 201 `OrderResponse` |
| GET | `/search/products` | public | 200 `SearchResponse` |
| POST | `/chat` | bearer | 200 `ChatResponse` |
| GET | `/health` | public | 200 `HealthCheckResponse` |
| GET | `/metrics` | public | Prometheus text |
| GET | `/docs`, `/redoc`, `/openapi.json` | public | docs |

## Rules

1. Additive changes are safe; renaming/removing fields is breaking.
2. Keep request and response schemas separate.
3. Return a `response_model` on every route.
4. Use 201 for creation, 204 for deletion with no body, 409 for conflicts.
5. Document new endpoints in `docs/06-api-reference.md` and
   `docs/19-frontend-handoff.md` in the same change.

## Consistency watchlist

- `GET /categories/{id}` is admin-only while `GET /categories` is public.
- `ProductListResponse` omits category/description.
- `PATCH /cart/items/{product_id}` still requires `product_id` in the body.
- Orders only has a create endpoint.
- No pagination metadata (`total`, `next`) — only arrays.
- Search has no filters or pagination metadata beyond `limit`.

## Related

- `docs/06-api-reference.md`
- `docs/19-frontend-handoff.md`
- `.agents/skills/backend-architecture/SKILL.md`
