---
name: API Client
description: Use when adding or changing network calls, generating types from OpenAPI, handling API errors, or defining the fetch wrapper.
---

# API Client

## When to use

- Adding a new endpoint call.
- Changing auth headers, base URL, or error handling.
- Regenerating types from OpenAPI.
- Mocking the API in tests.

## Contract

- Base: `${NEXT_PUBLIC_API_URL}/api/v1`
- OpenAPI: `GET /openapi.json`
- Auth: `Authorization: Bearer <token>`
- Login is **form-encoded**; everything else is JSON.
- Money is a **string** (`"19.99"`).
- Errors: `{ detail: string | ValidationIssue[] }`.

## Suggested layout

```
lib/api/
├── client.ts        # fetch wrapper, auth injection, refresh retry
├── types.ts         # generated from openapi.json
├── auth.ts
├── products.ts
├── categories.ts
├── cart.ts
├── orders.ts
├── search.ts
└── chat.ts
```

## Fetch wrapper rules

1. Inject the access token from the auth store.
2. On `401`, attempt **one** refresh (single-flight) and replay the request.
3. On a second `401`, clear auth and redirect to `/login`.
4. Parse JSON safely; a `204` returns `undefined`.
5. Throw a typed `ApiError { status, detail, issues }`.
6. Never log tokens or request bodies containing credentials.
7. Support `AbortSignal` for search/chat cancellation.
8. Send `X-Request-ID`? Optional; the backend accepts and echoes it.

```ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public issues: ValidationIssue[] = [],
  ) {
    super(detail);
  }
}
```

## Type generation

```bash
curl -s http://localhost:8000/openapi.json -o openapi.json
pnpm openapi-typescript openapi.json -o src/lib/api/types.ts
```

Wrap generated types in domain aliases (`Product`, `Cart`, …) from
`../../../docs/03-api-contract.md`. Do not hand-edit generated files.

## Rules

1. One function per endpoint, typed request + response.
2. No `fetch` outside `lib/api`.
3. Query strings via `URLSearchParams`.
4. Do not invent fields. If the backend lacks it, log the gap in
   `../../../docs/11-build-plan.md`.
5. Add an MSW handler for every new endpoint used in tests.

## Verify

```bash
pnpm typecheck
pnpm test
```

## Related

- `../../../docs/03-api-contract.md`
- `../../../docs/08-error-handling.md`
- `../../../../ecommerce-backend/docs/06-api-reference.md`
