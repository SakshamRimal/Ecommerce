# 07 — Auth & Security

## Overview

Authentication is stateless JWT with bcrypt password hashing. Authorization is a
single role check (`customer` vs `admin`). There is no server-side session and no
token revocation store.

## Password handling

`src/app/core/security.py`

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

- `hash_password` / `verify_password` are synchronous bcrypt calls.
- `hash_password_async` / `verify_password_async` wrap them in
  `loop.run_in_executor` so bcrypt does not block the event loop.
- Auth service uses the async variants.
- bcrypt truncates inputs beyond 72 bytes; the register schema allows up to 128
  chars. Very long passphrases therefore share a prefix. Consider rejecting > 72
  bytes or pre-hashing with SHA-256.

## Tokens

| Token | Lifetime | Claims |
|---|---|---|
| Access | `ACCESS_TOKEN_EXPIRE_MINUTES` (30) | `sub`, `exp`, `type="access"` |
| Refresh | `REFRESH_TOKEN_EXPIRE_DAYS` (7) | `sub`, `exp`, `type="refresh"` |

- Algorithm: `HS256` (configurable).
- Signed with `JWT_SECRET_KEY`.
- `sub` is the user UUID string.
- `decode_token` raises `ValueError("Invalid token")` on any `JWTError`
  (expired, bad signature, malformed).

### Refresh flow

1. Client posts `{refresh_token}`.
2. Service decodes and requires `type == "refresh"`.
3. Issues a new access **and** a new refresh token.
4. The old refresh token is **not** revoked; it remains valid until expiry.

## Current user

`src/app/core/deps.py`

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
```

- Extracts the bearer token.
- Requires `type == "access"`.
- Loads the user by UUID from PostgreSQL on every request.
- Rejects missing or inactive users.

Implications:
- Deactivating a user takes effect on the next request (good).
- Every authenticated request costs one DB lookup (cacheable later).

## Roles

`UserRole` is a `str` enum with values `customer` and `admin`. The DB enum stores
names `CUSTOMER`/`ADMIN`.

`require_admin` raises `ForbiddenError` (403) unless `role == UserRole.ADMIN`.

| Route group | Access |
|---|---|
| `GET /products`, `GET /products/{id}` | public |
| `POST/PATCH/DELETE /products` | admin |
| `GET /categories` | public |
| `GET/POST/PATCH/DELETE /categories/{id}` | admin |
| `/cart`, `/orders`, `/chat`, `/auth/me` | authenticated |
| `/search/products`, `/health` | public |

## Transport & headers

`SecurityHeadersMiddleware` adds to every HTTP response:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

`RequestContextMiddleware` adds `X-Request-ID` (echoes the incoming header or
generates a UUID).

CORS is configured from `CORS_ALLOWED_ORIGINS` (default
`http://localhost:3000`) with credentials allowed and methods
`GET/POST/PUT/PATCH/DELETE`. The code comment explicitly warns against `"*"`.

## Rate limiting

slowapi keyed by `get_remote_address`:

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 30/minute |
| `POST /chat` | 10/minute |

Default storage is **in-memory per process**, so limits are not shared across
uvicorn workers or replicas. Move to Redis storage for production.

## Request IDs

`RequestContextMiddleware` binds `request_id`, `path`, and `method` to structlog
context. Every log line in the request then includes them. The response echoes
`X-Request-ID`.

## Error semantics

| Situation | Status |
|---|---|
| No/invalid token | 401 |
| Wrong token type | 401 |
| Inactive user | 401 |
| Not admin | 403 |
| Duplicate email | 409 |
| Validation | 422 |

## Gaps and recommendations

- No logout endpoint or refresh-token revocation list.
- No password reset, email verification, or account lockout.
- No MFA.
- No CSRF protection (API is bearer-token based, so low risk; cookies are not
  used).
- No brute-force protection beyond the login rate limit.
- JWT secret rotation invalidates all sessions.
- `GET /categories/{id}` being admin-only is a likely authorisation bug for a
  storefront.
- Add a unique constraint or upsert for one-cart-per-user to avoid duplicate
  carts under concurrency.

See [17-security.md](17-security.md) for the broader posture.
