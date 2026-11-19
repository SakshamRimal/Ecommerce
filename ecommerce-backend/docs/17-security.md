# 17 — Security Posture

A pragmatic review of what is protected, what is not, and what to fix first.

## Controls present

| Control | Implementation |
|---|---|
| Password hashing | bcrypt via passlib, default cost |
| Async-safe hashing | bcrypt off the event loop |
| Token signing | JWT HS256, secret from env |
| Token typing | `access` vs `refresh` enforced |
| Authorization | `require_admin` on catalog writes |
| Inactive users | rejected on every request |
| SQL injection | parameterised SQLAlchemy queries |
| Password exposure | never returned in schemas |
| Security headers | nosniff, DENY, HSTS, referrer policy |
| CORS | explicit origin allow-list |
| Rate limiting | login 30/min, chat 10/min |
| Request IDs | generated/propagated |
| Input validation | Pydantic bounds on all bodies/params |
| Secrets in VCS | `.env` ignored; `.env.example` only |
| UUID IDs | non-enumerable resources |

## High-priority gaps

### 1. No refresh-token revocation
Refresh tokens remain valid for 7 days even after use. There is no logout,
blacklist, or rotation store. A stolen refresh token gives long-lived access.

**Fix:** store a token ID (`jti`) per refresh token, rotate on use, revoke on
logout, and support "revoke all sessions".

### 2. Rate limiting is per process
slowapi's default storage is in-memory. With multiple workers/replicas each has
its own counters, so the effective limit multiplies.

**Fix:** configure a Redis storage backend or enforce at the gateway.

### 3. Admin category detail is public data but admin-only
`GET /categories/{id}` requires admin. This is an authorization usability bug,
not a leak.

**Fix:** make it public (matching `GET /categories`).

### 4. Product delete can 500 on FK restrict
A product referenced by a cart or order raises an unhandled `IntegrityError`
instead of a clean `409`.

**Fix:** catch `IntegrityError` and map to `ConflictError`, or soft-delete
products.

### 5. Idempotency race
Concurrent checkout requests with the same key can produce a 500 after one
commits.

**Fix:** catch the unique violation and return the existing order.

### 6. bcrypt 72-byte truncation
Passwords up to 128 chars are accepted, but bcrypt only uses the first 72 bytes.

**Fix:** cap at 72 bytes or pre-hash (SHA-256) before bcrypt.

### 7. Error detail leakage
Unhandled exceptions return generic 500s (FastAPI default), but some services
propagate raw DB/ES/OpenAI errors to logs and possibly responses. Ensure
production does not run with `DEBUG=true` (it echoes SQL and enables debug
responses).

## Medium-priority gaps

- **No CSRF protection.** Bearer tokens in headers are not automatically sent by
  browsers, so risk is low — but do not move tokens to cookies without CSRF.
- **No account lockout / CAPTCHA.** Only IP rate limiting on login.
- **No email verification.** Anyone can register any email.
- **No password reset.**
- **No MFA.**
- **No security audit log** (who changed what, admin actions).
- **No file uploads** (good, nothing to exploit there yet).
- **No SSRF surface** in the request path, but tool/LLM arguments are parsed and
  used; validate UUIDs before DB lookups.
- **Prompt injection** is unmitigated in chat. Tools are read-only today, which
  limits blast radius. If you add cart/order mutation tools, require explicit
  confirmation and server-side authorization.

## Data protection

- Passwords: bcrypt.
- Tokens: signed, not encrypted (do not put PII in claims).
- PII stored: email, full name, order history, chat messages.
- Chat content is sent to OpenAI; disclose this in the privacy policy and avoid
  logging message bodies.
- SMTP sends order details to the user's email.

## Infrastructure hardening

- Elasticsearch runs with `xpack.security.enabled=false` in Compose —
  development only. Require auth + TLS in production.
- Postgres and Redis ports are published in Compose — do not expose publicly.
- OTel collector accepts unauthenticated OTLP — keep it on a private network.
- Run containers as non-root and read-only where possible.
- Pin image digests and dependencies; `uv.lock` is committed.
- Do not bake `.env` into images.

## Suggested security roadmap

1. Refresh-token rotation + revocation + logout.
2. Redis-backed rate limiting.
3. Fix authorization/500 issues above.
4. Email verification + password reset.
5. Admin audit logging.
6. Dependency and container scanning in CI.
7. Secrets manager + key rotation runbook.
8. Penetration test before launch.

## Responsible disclosure

No security contact is defined in the repo. Add one (e.g. `SECURITY.md`) before
going public.
