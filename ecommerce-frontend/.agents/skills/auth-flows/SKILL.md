---
name: Auth Flows
description: Use when implementing login, registration, token storage, refresh, route guards, or current-user state.
---

# Auth Flows

## When to use

- Login/register pages.
- Token storage and refresh.
- Protected routes (`/cart`, `/checkout`, `/account`, `/admin`).
- Rendering based on `role`.

## Backend endpoints

| Action | Call | Notes |
|---|---|---|
| Register | `POST /auth/register` JSON | returns user |
| Login | `POST /auth/login` **form** | `username`=email, `password` |
| Refresh | `POST /auth/refresh` JSON | new access + refresh |
| Me | `GET /auth/me` Bearer | user + role |

There is no logout endpoint; clear client state only.

## Login implementation

```ts
const body = new URLSearchParams({ username: email, password });
await api.post("/auth/login", body, {
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
});
```

Do **not** send JSON to login.

## Token strategy

- Access token: in memory (preferred) or `sessionStorage`.
- Refresh token: `httpOnly` cookie is ideal but the backend returns JSON today.
  If stored client-side, understand the XSS trade-off and keep CSP tight.
- Refresh single-flight: one promise shared by all waiters.
- Retry the original request once after refresh.
- On refresh failure: clear tokens, redirect to `/login?next=…`.

## Route guards

| Area | Guard |
|---|---|
| `/cart`, `/checkout` | authenticated |
| `/account` | authenticated |
| `/admin/**` | authenticated + `role === "admin"` |
| `/login`, `/register` | redirect if already authenticated |

Check the role from `GET /auth/me`, not from a JWT claim (tokens have no role).

## UX rules

1. Show inline field errors from 422 (`loc` → field).
2. Show a generic message for 401 (`Invalid email or password`).
3. Surface 429 with a cooldown.
4. Never reveal whether an email exists on login.
5. After register, either auto-login or send the user to login.
6. Preserve the intended destination with `?next=`.

## Gaps

- No logout/revocation: tokens remain valid until expiry.
- No password reset or email verification.
- No "remember me".
- No refresh token expiry UX; treat any refresh 401 as logged out.

## Verify

- Wrong password → 401 message.
- Expired access token → silent refresh + retry.
- Refresh failure → redirect.
- Customer hitting `/admin` → 403 page.

## Related

- `../../../docs/04-auth-and-session.md`
- `../../../../ecommerce-backend/docs/07-auth-and-security.md`
