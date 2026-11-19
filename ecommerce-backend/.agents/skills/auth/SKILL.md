---
name: Authentication and Authorization
description: Use when changing registration, login, token refresh, current-user lookup, JWT handling, password hashing, or role-based access control.
---

# Auth & Authorization

## When to use

- Changing `/api/v1/auth/*` endpoints.
- Touching JWT creation/decoding or password hashing.
- Adding admin-only routes or changing role checks.
- Debugging 401/403 behaviour.

## Files

| Concern | File |
|---|---|
| Routes | `src/app/api/v1/auth/controller.py` |
| Business logic | `src/app/api/v1/auth/service.py` |
| User queries | `src/app/api/v1/auth/repository.py` |
| Schemas | `src/app/api/v1/auth/schema.py` |
| JWT + bcrypt | `src/app/core/security.py` |
| Current user / admin guard | `src/app/core/deps.py` |
| User model + roles | `src/app/models/user.py` |

## Flow

### Register
`POST /auth/register` JSON `{email, password, full_name}` → 201
`UserResponse`. Service checks duplicate email (`ConflictError`), hashes with
bcrypt in a thread pool, creates user, defaults role to `CUSTOMER`.

### Login
`POST /auth/login` uses `OAuth2PasswordRequestForm` — **form-encoded**
(`username`, `password`), not JSON. Rate-limited to `30/minute` per IP.
Returns `{access_token, refresh_token, token_type: "bearer"}`.

### Refresh
`POST /auth/refresh` JSON `{refresh_token}`. Decodes token, requires
`type == "refresh"`, returns a new access + refresh pair. There is **no
revocation/rotation store** — old refresh tokens stay valid until expiry.

### Current user
`GET /auth/me` requires `Authorization: Bearer <access_token>`.
`get_current_user` decodes, requires `type == "access"`, loads the user from DB,
and rejects missing/inactive users.

### RBAC
`require_admin` depends on `get_current_user` and checks
`role == UserRole.ADMIN`. Products/categories writes use it.

## Rules

1. Never return `hashed_password` in a response schema.
2. Keep access and refresh tokens typed (`"access"` / `"refresh"`); enforce the
   type on every decode path.
3. Hash passwords with `hash_password_async` inside request handlers.
4. Add `Depends(require_admin)` to every admin mutation.
5. Do not put secrets in code; `JWT_SECRET_KEY` must come from env.
6. Token subject is the user UUID string (`sub`).

## Gotchas

- Access/refresh tokens contain no role claim; roles are always read from DB.
- `create_access_token` accepts `extra_claims` but service does not use it.
- There is no logout, password reset, email verification, or token blacklist.
- Login is form-data; the frontend must send `application/x-www-form-urlencoded`.

## Verify

```bash
uv run pytest tests/unit/test_auth_service.py tests/unit/test_security.py -q
uv run pytest tests/integration/test_auth.py -q
```

## Related

- `docs/07-auth-and-security.md`
- `docs/17-security.md`
