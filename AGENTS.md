# Agent Guide — Commercify

This repository has two packages, each with its own agent guide and feature
skills.

| Package | Guide | Skills | Docs |
|---|---|---|---|
| Workspace Root | [`AGENTS.md`](AGENTS.md) | [`.agents/`](.agents/README.md) (`git-commit`) | [`README.md`](README.md) |
| Backend (FastAPI) | [`ecommerce-backend/AGENTS.md`](ecommerce-backend/AGENTS.md) | [`ecommerce-backend/.agents/`](ecommerce-backend/.agents/README.md) | [`ecommerce-backend/docs/`](ecommerce-backend/docs/README.md) |
| Frontend (React 19 + Vite) | [`ecommerce-frontend/AGENTS.md`](ecommerce-frontend/AGENTS.md) | [`ecommerce-frontend/.agents/`](ecommerce-frontend/.agents/README.md) | [`ecommerce-frontend/docs/`](ecommerce-frontend/docs/README.md) |

## How to work

1. Open the package you are changing as the working directory so its
   `.agents/skills/` are discoverable.
2. Load the matching skill by ID (e.g. `auth`, `orders`, `cart-ui`).
3. Read the linked docs before editing.
4. Follow the layering rules in the backend guide and the contract rules in the
   frontend guide.

## Source of truth

- Backend API behaviour: [`ecommerce-backend/docs/06-api-reference.md`](ecommerce-backend/docs/06-api-reference.md)
- Cross-package contract: [`ecommerce-backend/docs/19-frontend-handoff.md`](ecommerce-backend/docs/19-frontend-handoff.md)
- Known bugs/risks: [`ecommerce-backend/docs/18-known-issues.md`](ecommerce-backend/docs/18-known-issues.md)

## Current state

- Backend: completed, all 118 tests pass, zero Ruff lint errors, all documented known issues resolved.
- Frontend: completed, full storefront + AI shopping concierge + admin console built in `ecommerce-frontend/` with React 19, Vite, TypeScript, Tailwind CSS v4, TanStack Query v5, and Zustand; `npm run typecheck`, `npm test`, and `npm run build` all pass.
