# Commercify Backend

> A from-first-principles, production-grade e-commerce backend — built in public, day by day.

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
