# Commercify Backend

> A from-first-principles, production-grade e-commerce backend — built in public, day by day.

## Repository layout

| Path | Purpose |
|---|---|
| [`ecommerce-backend/`](ecommerce-backend/) | FastAPI API, worker, migrations, tests |
| [`ecommerce-backend/docs/`](ecommerce-backend/docs/README.md) | Full backend documentation |
| [`ecommerce-backend/.agents/`](ecommerce-backend/.agents/README.md) | Per-feature agent skills |
| [`ecommerce-frontend/`](ecommerce-frontend/) | Frontend planning workspace (app not built yet) |
| [`ecommerce-frontend/docs/`](ecommerce-frontend/docs/README.md) | Frontend docs and build plan |
| [`ecommerce-frontend/.agents/`](ecommerce-frontend/.agents/README.md) | Frontend agent skills |

Agent entry points: [`AGENTS.md`](AGENTS.md), [`ecommerce-backend/AGENTS.md`](ecommerce-backend/AGENTS.md), [`ecommerce-frontend/AGENTS.md`](ecommerce-frontend/AGENTS.md).

Built with **FastAPI**, **PostgreSQL**, **uv**, and clean **Controller → Service → Repository** architecture, following 12-factor app principles. Covers everything from config management and structured logging to caching, search, transactional emails, and observability — with AI features layered in later.

## 🧱 Tech Stack
- **Framework:** FastAPI (async)
- **Package Manager:** uv
- **Database:** PostgreSQL + SQLAlchemy (async) + Alembic
- **Cache:** Redis
- **Search:** Elasticsearch
- **Logging:** structlog (JSON, structured)
- **Architecture:** Controller → Service → Repository, 12-Factor App

## 📅 Build Journal
| Day | Focus |
|---|---|
| 1 | Project skeleton, config, logging, request context, DB, health check |
| 2 | Domain models, migrations, optimized queries |
| 3 | Auth, security middleware |
| 4 | CRUD, validation/serialization layers |
| 5 | Orders, transactions, caching |
| 6 | Elasticsearch, background jobs |
| 7 | Transactional emails, observability |
| 8 | Concurrency, Docker, deployment |
