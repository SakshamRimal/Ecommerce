# 08 — Error Handling

## Backend error shapes

```ts
// AppException (4xx/5xx)
{ "detail": "Insufficient stock for 'Trail Runner' (requested 3, available 1)" }

// FastAPI validation (422)
{
  "detail": [
    { "loc": ["body", "password"], "msg": "String should have at least 8 characters", "type": "string_too_short" }
  ]
}
```

Normalize both into one client type:

```ts
class ApiError extends Error {
  status: number;
  issues: ValidationIssue[];
  constructor(status: number, body: ApiErrorBody) {
    super(typeof body.detail === "string" ? body.detail : "Validation failed");
    this.status = status;
    this.issues = Array.isArray(body.detail) ? body.detail : [];
  }
}
```

## Status → UX map

| Status | Where | UX |
|---|---|---|
| 400 | rare | generic message |
| 401 | any auth call | refresh once → retry; on failure redirect to `/login` |
| 403 | admin/guard | "You don't have permission" page |
| 404 | PDP/admin detail | `not-found` page or inline "Not found" |
| 409 | cart/order/register/category | actionable message + refetch |
| 422 | forms | inline field errors from `loc` |
| 429 | login/chat | cooldown message, disable action |
| 500 | any | generic error + retry; log correlation ID |
| Network | offline/timeout | "Check your connection" + retry |

## Form error mapping

```ts
function fieldErrors(err: unknown): Record<string, string> {
  if (!(err instanceof ApiError)) return {};
  return Object.fromEntries(
    err.issues.map((issue) => [String(issue.loc.at(-1)), issue.msg]),
  );
}
```

- `loc` is `["body", "email"]` → field `email`.
- Non-field issues go to a form-level banner.

## Specific flows

### Login
- 401 → "Invalid email or password." (do not distinguish).
- 429 → "Too many attempts. Try again in a minute."
- 422 → field errors (unlikely, form validates first).

### Register
- 409 → "An account with this email already exists."
- 422 → field errors.

### Add to cart
- 401 → open login prompt, preserve intended product.
- 404 → product removed; refresh catalog.
- 409 → "Only N available"; refetch product/cart.

### Checkout
- 409 empty cart → redirect to `/cart` with a notice.
- 409 stock → show the item and available quantity.
- 500 → keep the cart intact and offer retry with the same idempotency key.

### Admin
- 403 → 403 page.
- 404 → row disappeared; refetch.
- 409 category delete → "Category still has products."
- 500 product delete → explain the likely reference and suggest zeroing stock.

### Chat
- 429 → cooldown; disable composer.
- 5xx → "Assistant is unavailable" + retry.
- Network → keep draft.

## Error boundaries

- Route-level `error.tsx` (Next.js) / React `ErrorBoundary` for render errors.
- Global `not-found.tsx`.
- Show a support reference using the backend `X-Request-ID` when available.

## Logging

- Client logs: status, endpoint, request ID; never tokens or passwords.
- Send 5xx client-side errors to your telemetry tool with the request ID.
- Do not log chat message contents by default.

## Copy guidelines

- Say what happened and what the user can do.
- Do not expose stack traces, SQL, or internal identifiers.
- For 409, include the backend's message (it is already user-readable).
- For 500, use a generic message plus retry.
