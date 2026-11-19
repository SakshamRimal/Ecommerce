# 04 — Auth & Session

## Backend model

- Access token: JWT, 30 min, `sub` = user UUID, `type = access`.
- Refresh token: JWT, 7 days, `type = refresh`.
- No role claim — fetch the role from `GET /auth/me`.
- No logout/revocation endpoint.
- Login is form-encoded.

## Client state

```ts
interface AuthState {
  accessToken: string | null;
  user: User | null;
  status: "loading" | "authenticated" | "anonymous";
  login(email: string, password: string): Promise<void>;
  logout(): void;
  bootstrap(): Promise<void>;
}
```

- Access token in memory (or `sessionStorage` for reload survival).
- Refresh token storage:
  - **Preferred:** backend sets an `httpOnly; Secure; SameSite=Lax` cookie on a
    new `/auth/login` + `/auth/refresh` that also returns tokens. Not implemented
    today.
  - **Current:** the API returns the refresh token in JSON. If you must persist
    it, `localStorage` is XSS-exposed; use a short refresh lifetime and a strict
    CSP, or keep it in memory and accept re-login on reload.

## Bootstrap

On app load:
1. If there is an access token, call `GET /auth/me`.
2. On success → authenticated.
3. On 401 → try one refresh.
4. On refresh failure → anonymous.

Never render protected UI before bootstrap resolves; use a skeleton.

## Login

```ts
const form = new URLSearchParams({ username: email, password });
const tokens = await api.post<TokenResponse>("/auth/login", form, {
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
});
setTokens(tokens);
const user = await api.get<User>("/auth/me");
```

Do not send JSON to `/auth/login`.

## Refresh (single-flight)

```ts
let refreshPromise: Promise<TokenResponse> | null = null;

export function refresh(): Promise<TokenResponse> {
  refreshPromise ??= api
    .post<TokenResponse>("/auth/refresh", {
      refresh_token: getRefreshToken(),
    })
    .finally(() => { refreshPromise = null; });
  return refreshPromise;
}
```

The fetch wrapper:
1. Sends the access token.
2. On 401 (once), awaits `refresh()`, replaces the token, retries.
3. On a second 401, calls `logout()` and redirects.

Exclude `/auth/login`, `/auth/register`, and `/auth/refresh` from the retry.

## Guards

| Route | Rule |
|---|---|
| `/cart`, `/checkout`, `/account` | authenticated |
| `/admin/**` | authenticated + `role === "admin"` |
| `/login`, `/register` | redirect to `/` if authenticated |

Implement in middleware/proxy or a layout-level client guard. Always keep
server-side enforcement in mind: the backend is the real guard.

## Session expiry UX

- Proactively refresh when the access token is near expiry (optional).
- On refresh failure, show "Session expired, please sign in again."
- Preserve the current URL in `?next=`.

## Logout

```ts
function logout() {
  setAccessToken(null);
  setRefreshToken(null);
  queryClient.clear();
  router.push("/login");
}
```

The refresh token remains valid on the server until it expires. Document this.

## Security checklist

- [ ] Access token never logged.
- [ ] Refresh single-flight, no thundering herd.
- [ ] 401 retry only once.
- [ ] Admin guard checks `user.role`, not a local flag.
- [ ] `next` redirect validated to be same-origin.
- [ ] CSP blocks inline scripts; no token in URLs.
- [ ] 429 login attempts show a cooldown.
- [ ] Never display "email already exists" on login (only on register, which is
      already a 409).

## Gaps to raise with backend

1. Add httpOnly cookie refresh + `POST /auth/logout` with revocation.
2. Add a `jti`/rotation store.
3. Add password reset + email verification.
4. Consider returning `role` in the token for fewer `/auth/me` calls (keep DB
   check for revocation).
