# Agent Skills — Ecommerce Backend

This directory contains project-local skills for AI coding agents working on the
backend. OpenCode discovers project skills in `.agents/skills/` (a compatibility
source) and in `.opencode/skills/`.

Each feature of the backend has its own skill so an agent can load only the
context it needs instead of reading the whole codebase.

## Layout

```
.agents/
├── README.md
└── skills/
    ├── api-contract/SKILL.md
    ├── auth/SKILL.md
    ├── background-jobs/SKILL.md
    ├── backend-architecture/SKILL.md
    ├── cart/SKILL.md
    ├── catalog/SKILL.md
    ├── database-migrations/SKILL.md
    ├── infrastructure/SKILL.md
    ├── orders/SKILL.md
    ├── search/SKILL.md
    ├── ai-chat/SKILL.md
    ├── git-commit/SKILL.md
    └── testing/SKILL.md
```

## How to use

1. Pick the skill that matches the feature being changed.
2. Load it by ID (for example `@skill-auth` or the `skill` tool with ID `auth`).
3. Read the linked docs under `../docs/` for full detail.
4. Follow the "Rules" and "Verify" sections in the skill.

## Skill map

| Skill ID | Use it for |
|---|---|
| `backend-architecture` | New modules, layering, dependency injection, app wiring |
| `auth` | Registration, login, refresh, current user, RBAC |
| `catalog` | Products and categories CRUD, cache invalidation, optimistic locking |
| `cart` | Per-user cart and cart items |
| `orders` | Checkout, stock locking, idempotency |
| `search` | Elasticsearch full-text and semantic search |
| `ai-chat` | OpenAI shopping assistant, tool calling, chat persistence |
| `background-jobs` | arq worker, indexing, embeddings, email jobs |
| `infrastructure` | Config, Redis cache, ES client, tracing, logging, metrics, middleware, rate limits |
| `database-migrations` | Models, Alembic revisions, schema changes |
| `testing` | Unit/integration/load tests and mocking patterns |
| `api-contract` | Request/response shapes and frontend-facing contract |
| `git-commit` | Conventional Commits, pre-commit verification gates, and pushing to GitHub |

## Golden rules

- Keep the **Controller → Service → Repository** boundary intact.
- Controllers wire dependencies and translate HTTP; services hold business rules;
  repositories own SQL.
- Every new endpoint needs a schema, a service method, a repository method (if it
  touches the DB), and tests.
- Read `../docs/18-known-issues.md` before fixing behaviour — several bugs are
  already documented there.
- Never expose secrets from `.env`; use `.env.example` for documentation.
