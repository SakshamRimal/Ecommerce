# Agent Guide — Ecommerce Frontend

The frontend is built with **React 19 + Vite + TypeScript + Tailwind CSS v4 + TanStack Query v5 + Zustand**. This file and `.agents/` define how to work in `ecommerce-frontend/`.

## Context

- Backend: `../ecommerce-backend`, API base `/api/v1`.
- Contract: `../ecommerce-backend/docs/06-api-reference.md` and `19-frontend-handoff.md`.
- Planning docs: `docs/README.md`.
- Feature skills: `.agents/README.md`.

## Rules

1. **Contract first.** Every network call must exist in the backend API docs.
   Never guess a field, endpoint, or status code.
2. **Money is `string`.** Use `Intl.NumberFormat` for display and a decimal
   helper for arithmetic — never `parseFloat` + `toFixed` for calculations.
3. **Auth:** access token in memory, refresh single-flight, retry once on 401.
4. **Server state:** use TanStack Query (or equivalent) — no ad-hoc `useEffect`
   fetching. Define query keys centrally.
5. **Cart:** authenticated only. No guest cart exists on the backend.
6. **Errors:** model the `{detail}` and 422 array shapes; map 401/403/404/409/422/429.
7. **Accessibility:** every page needs keyboard access, focus states, labels,
   and loading/empty/error states.
8. **Tests:** unit + component + one E2E happy path per core flow.
9. **No secrets in the browser.** Only public API URLs and public keys.
10. **Do not build** order history, logout, password reset, public category
    detail, or semantic search until the backend gaps are resolved. See
    `docs/11-build-plan.md`.

## Recommended stack (proposal)

- Next.js App Router + TypeScript, or Vite + React Router
- TanStack Query, Zustand (cart UI), Zod
- Tailwind CSS + shadcn/ui
- Vitest + Testing Library, Playwright
- `openapi-typescript` for generated API types

## Commands

```bash
npm install
npm run dev
npm test
npm run typecheck
npm run build
```
