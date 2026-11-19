# Agent Skills — Ecommerce Frontend

Project-local skills for AI agents building the storefront. OpenCode discovers
`.agents/skills/<id>/SKILL.md`.

The frontend does not exist yet; these skills describe the intended conventions
and the backend contract to build against.

## Layout

```
.agents/
├── README.md
└── skills/
    ├── frontend-architecture/SKILL.md
    ├── api-client/SKILL.md
    ├── auth-flows/SKILL.md
    ├── catalog-ui/SKILL.md
    ├── cart-ui/SKILL.md
    ├── checkout-orders/SKILL.md
    ├── search-ui/SKILL.md
    ├── ai-assistant-ui/SKILL.md
    ├── state-and-data/SKILL.md
    ├── design-system/SKILL.md
    ├── admin-ui/SKILL.md
    ├── git-commit/SKILL.md
    └── frontend-testing/SKILL.md
```

## Skill map

| Skill ID | Use it for |
|---|---|
| `frontend-architecture` | App structure, routing, rendering, folders |
| `api-client` | Typed fetch client, error handling, generated types |
| `auth-flows` | Login/register, tokens, refresh, route guards |
| `catalog-ui` | Home, product list, product detail, categories |
| `cart-ui` | Cart drawer/page, add/update/remove, stock conflicts |
| `checkout-orders` | Checkout, idempotency, confirmation |
| `search-ui` | Search bar, results, empty/loading states |
| `ai-assistant-ui` | Chat panel, streaming-free UX, rate limits |
| `state-and-data` | TanStack Query keys, caching, mutations, Zustand |
| `design-system` | Tokens, primitives, layout, accessibility |
| `admin-ui` | Admin product/category CRUD |
| `frontend-testing` | Unit, component, MSW, E2E |
| `git-commit` | Conventional Commits, pre-commit verification gates, and pushing to GitHub |

## Golden rules

- Read `../../ecommerce-backend/docs/06-api-reference.md` before coding.
- Read `../docs/03-api-contract.md` for TypeScript types.
- Money is a string. Never do float math.
- Don't invent endpoints; log gaps in `../docs/11-build-plan.md`.
- Every feature needs loading, empty, error, and unauthorized states.
