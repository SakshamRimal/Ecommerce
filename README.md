# Commercify — AI-Powered Full-Stack E-Commerce Platform

Commercify is a production-grade, async full-stack e-commerce platform built with **FastAPI**, **React 19 + TypeScript + Tailwind CSS v4**, **PostgreSQL 16 + pgvector**, **Redis 7**, **Elasticsearch 8.16**, **MinIO S3 Object Storage**, **ARQ Background Workers**, **OpenAI Tool-Calling Concierge**, and **OpenTelemetry**.

---

## ✨ Key Features

- **Modern Storefront (`ecommerce-frontend/`)**
  - Responsive catalog browsing, category filtering, price sorting, and product detail views with live stock badges.
  - Exact integer-cents money arithmetic formatted in **`NRs`** (`NRs 119.99`) with zero floating-point drift.
  - Persistent slide-over shopping bag drawer, full cart page, and multi-method checkout (**Credit / Debit Card**, **Digital Wallet**, **Pay on Delivery**) with client and server idempotency protection.
  - Dark & light theme support, accessible primitives, and responsive navigation.
- **AI Shopping Concierge & Hybrid Vector Search**
  - Slide-over AI Shopping Concierge (`POST /api/v1/chat`, `GET /api/v1/chat/history`, `DELETE /api/v1/chat/history`) powered by OpenAI function calling (`search_products`, `semantic_search_products`, `get_product_details`, `check_stock`) with an intelligent live-catalog fallback when offline or out of API quota.
  - Hybrid search page supporting **Elasticsearch full-text search** (`GET /api/v1/search/products`) and **pgvector semantic meaning search** (`GET /api/v1/search/products/semantic`) with price and category filters.
- **Concurrency-Safe Checkout, Row Locking & Deadlock Prevention**
  - **User Cart Row Locking**: `SELECT ... FOR UPDATE` on the user's `Cart` serializes concurrent checkout requests from the same user.
  - **Deterministic Product Lock Ordering**: Line items are sorted by `product_id` before acquiring `SELECT ... FOR UPDATE` row locks (`populate_existing=True`), eliminating circular-wait deadlocks under high concurrency.
  - **Idempotency Keys**: Duplicate or retried `POST /api/v1/orders` requests with the same `idempotency_key` return the existing confirmed order without double-charging or double-decrementing stock.
  - **Order Cancellation & Restock**: `POST /api/v1/orders/{order_id}/cancel` atomically restores reserved product inventory under row locks and invalidates Redis caches.
- **MinIO Object Storage for Product Images**
  - Admin Console (`http://localhost:3000/admin/products`) uploads binary product images (`JPEG`, `PNG`, `WEBP`, `GIF`, `AVIF` up to 10 MB) via `POST /api/v1/products/upload-image` directly into a **MinIO S3 bucket** (`product-images`) signed with async AWS Signature V4 (`AWS4-HMAC-SHA256`).
- **Authentication, Token Rotation & RBAC**
  - JWT access and refresh tokens with `jti` claims, atomic single-use refresh token rotation (`consume_token_once` via Redis `SET NX EX`), token revocation on `POST /api/v1/auth/logout`, and role-based access control (`customer`, `admin`).
- **Transactional HTML Order Confirmation Emails**
  - Sends styled HTML order confirmation receipts (`src/app/templates/email/order_confirmation.html`) with `NRs` line-item breakdowns via SMTP (`FastMail`) through the ARQ worker or non-blocking background fallback.
- **Observability & Production Infrastructure**
  - Structured JSON logging (`structlog`) with OpenTelemetry `trace_id` correlation, Prometheus `/metrics`, multi-component `/api/v1/health`, and multi-stage Docker + Nginx production containers.

---

## 🧱 Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 6, TypeScript 5, Tailwind CSS v4, TanStack Query v5, Zustand, React Router v7, Lucide Icons, Vitest |
| **Backend API** | FastAPI, Python 3.12, SQLAlchemy 2.0 (Async), Pydantic v2, Alembic, SlowAPI, FastMail, `uv` |
| **Data & Storage** | PostgreSQL 16 (`pgvector/pgvector:pg16`), Redis 7, Elasticsearch 8.16, MinIO (S3-compatible object storage) |
| **AI & Async Jobs** | OpenAI API (`gpt-4o-mini` + `text-embedding-3-small`), ARQ Redis Worker |
| **Observability & Ops** | OpenTelemetry Collector, Prometheus Instrumentator, `structlog`, Docker Compose, Nginx 1.27 Alpine |

---

## 📁 Repository Layout

```text
Ecommerce/
├── docker-compose.yml                # Root full-stack Docker Compose orchestration
├── AGENTS.md                         # Workspace AI agent guide
├── .agents/                          # Workspace agent skills (git-commit)
├── ecommerce-backend/                # FastAPI async backend service
│   ├── Dockerfile                    # Python 3.12 + uv production image
│   ├── docker-compose.yml            # Backend + Frontend + Infra Compose stack
│   ├── pyproject.toml                # Dependencies & `ecommerce` CLI entrypoint
│   ├── src/
│   │   ├── app/
│   │   │   ├── ai/                   # OpenAI tool definitions, ToolExecutor, embeddings
│   │   │   ├── api/v1/               # Layered modules: auth, products, categories, cart, orders, search, chat, health
│   │   │   ├── core/                 # Config, JWT security, Redis cache, MinIO storage, SMTP email, logging, metrics
│   │   │   ├── db/                   # Async SQLAlchemy engine, session factory, base mixins
│   │   │   ├── jobs/                 # ARQ worker tasks (ES indexing, embeddings, order emails)
│   │   │   ├── middlewares/          # Request ID context & security headers
│   │   │   ├── models/               # SQLAlchemy ORM models (User, Product, Category, Cart, Order, Chat)
│   │   │   ├── templates/email/      # HTML order confirmation email template
│   │   │   ├── cli.py                # `create-admin` and `seed-catalog` CLI commands
│   │   │   └── main.py               # FastAPI application entrypoint
│   │   └── migrations/               # Alembic database migrations
│   ├── tests/                        # Unit, integration, and Locust load tests (124 tests)
│   └── docs/                         # Architectural and API documentation
└── ecommerce-frontend/               # React 19 + TypeScript storefront & admin console
    ├── Dockerfile                    # Multi-stage Node 20 build -> Nginx 1.27 Alpine runtime
    ├── nginx.conf                    # SPA fallback, /api/ reverse proxy, gzip, security headers
    ├── src/
    │   ├── components/               # Reusable UI primitives, ProductCard, Header, CartDrawer, AssistantDrawer
    │   ├── lib/                      # Typed API client, NRs money utilities, TanStack Query keys
    │   ├── pages/                    # Home, Products, ProductDetail, Search, Cart, Checkout, Orders, Auth, Admin
    │   └── stores/                   # Zustand auth and UI state stores
    ├── tests/                        # Vitest unit and component tests
    └── docs/                         # Frontend architecture and API contract documentation
```

---

## 🚀 Quick Start (Docker Compose — Recommended)

### 1. Configure Environment

```bash
cd ecommerce-backend
cp .env.example .env
# Edit .env to set your JWT_SECRET_KEY, MAIL_* SMTP credentials, and OPENAI_API_KEY
```

### 2. Start the Full Stack

```bash
cd ecommerce-backend
docker compose up -d
```

### 3. Seed Curated Catalog & Create an Admin Account

```bash
cd ecommerce-backend
# Seed 6+ categories with 4+ products per category and high-resolution images
POSTGRES_PORT=5434 REDIS_URL=redis://localhost:16379/0 uv run ecommerce seed-catalog

# Create or promote an administrator account
POSTGRES_PORT=5434 uv run ecommerce create-admin \
  --email admin@commercify.dev \
  --password AdminPassword123 \
  --full-name "Store Admin" \
  --promote-existing
```

### 4. Access Services

| Service | URL | Notes |
|---|---|---|
| **Storefront & Admin UI** | http://localhost:3000 | Customer storefront + `/admin/products` console |
| **FastAPI Backend & Swagger Docs** | http://localhost:8000/docs | Interactive OpenAPI documentation |
| **Health Check** | http://localhost:8000/api/v1/health | Postgres, Redis, and Elasticsearch status |
| **MinIO S3 API** | http://localhost:9000 | Serves uploaded product images (`/product-images/<key>`) |
| **MinIO Web Console** | http://localhost:9001 | Default login: `minioadmin` / `minioadmin` |
| **Elasticsearch** | http://localhost:9200 | Product search index |
| **PostgreSQL (`pgvector`)** | `localhost:5434` | Container port `5432` mapped to host `5434` |
| **Redis** | `localhost:16379` | Container port `6379` mapped to host `16379` |

---

## 💻 Local Development (Without Docker for App Processes)

### Backend (`ecommerce-backend/`)

```bash
cd ecommerce-backend
uv sync
uv run alembic upgrade head
uv run ecommerce seed-catalog

# Start FastAPI dev server with hot reload
uv run uvicorn app.main:app --reload --port 8000

# Optional: start ARQ background worker in a second terminal
uv run arq app.jobs.worker.WorkerSettings
```

### Frontend (`ecommerce-frontend/`)

```bash
cd ecommerce-frontend
npm install

# Start Vite dev server on http://localhost:3000 (proxies /api to http://localhost:8000)
npm run dev
```

---

## 🔌 REST API Overview (`/api/v1`)

| Area | Method & Path | Auth | Description |
|---|---|---|---|
| **Auth** | `POST /api/v1/auth/register` | Public | Register a new customer account |
| **Auth** | `POST /api/v1/auth/login` | Public | Authenticate (form-urlencoded) and receive access + refresh JWTs |
| **Auth** | `POST /api/v1/auth/refresh` | Public | Atomically rotate single-use refresh token |
| **Auth** | `POST /api/v1/auth/logout` | Public | Revoke access and refresh token `jti` claims |
| **Auth** | `GET /api/v1/auth/me` | Bearer | Get current authenticated user profile and role |
| **Products** | `GET /api/v1/products` | Public | List products with pagination and optional `category_id` filter |
| **Products** | `GET /api/v1/products/{id}` | Public | Get product details by UUID |
| **Products** | `POST /api/v1/products` | Admin | Create a product and enqueue search indexing + embedding jobs |
| **Products** | `PATCH /api/v1/products/{id}` | Admin | Update product with row-locked optimistic `version` check |
| **Products** | `DELETE /api/v1/products/{id}` | Admin | Delete unreferenced product (`409` if referenced by cart/order) |
| **Products** | `POST /api/v1/products/upload-image` | Admin | Upload product image file (`multipart/form-data`) to MinIO bucket |
| **Categories** | `GET /api/v1/categories` | Public | List all categories |
| **Categories** | `GET /api/v1/categories/{id}` | Public | Get category details by UUID |
| **Categories** | `POST /api/v1/categories` | Admin | Create category with automatic URL slug generation |
| **Categories** | `PATCH /api/v1/categories/{id}` | Admin | Rename category and regenerate slug |
| **Categories** | `DELETE /api/v1/categories/{id}` | Admin | Delete category (`409` if products reference it) |
| **Cart** | `GET /api/v1/cart` | Bearer | Get or create the current user's shopping cart (`NRs` subtotals) |
| **Cart** | `POST /api/v1/cart/items` | Bearer | Add item to cart with live stock validation |
| **Cart** | `PATCH /api/v1/cart/items/{product_id}` | Bearer | Update item quantity (`0` removes item) |
| **Cart** | `DELETE /api/v1/cart/items/{product_id}` | Bearer | Remove single item from cart |
| **Cart** | `DELETE /api/v1/cart` | Bearer | Clear all items from cart |
| **Orders** | `POST /api/v1/orders` | Bearer | Create order from cart with `idempotency_key` and `FOR UPDATE` locks |
| **Orders** | `GET /api/v1/orders` | Bearer | List current user's orders, newest first |
| **Orders** | `GET /api/v1/orders/{order_id}` | Bearer | Get single order receipt for current user |
| **Orders** | `POST /api/v1/orders/{order_id}/cancel` | Bearer | Cancel order and atomically restore product stock |
| **Search** | `GET /api/v1/search/products` | Public | Full-text product search with `min_price`, `max_price`, `category_id` |
| **Search** | `GET /api/v1/search/products/semantic` | Public | Semantic vector similarity search via `pgvector` |
| **AI Chat** | `POST /api/v1/chat` | Bearer | Send message to AI Shopping Concierge |
| **AI Chat** | `GET /api/v1/chat/history` | Bearer | Retrieve recent chat session messages |
| **AI Chat** | `DELETE /api/v1/chat/history` | Bearer | Start a fresh AI chat session |
| **System** | `GET /api/v1/health` | Public | Health check for PostgreSQL, Redis, and Elasticsearch |

---

## 🧪 Testing & Quality Gates

### Backend (`ecommerce-backend/`)

```bash
cd ecommerce-backend

# Lint check (0 errors)
uv run ruff check src tests

# Full unit & integration test suite (124 passed)
uv run pytest -q

# Load testing with Locust
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

### Frontend (`ecommerce-frontend/`)

```bash
cd ecommerce-frontend

# TypeScript typecheck
npm run typecheck

# Vitest unit & component tests (10 passed)
npm test

# Production bundle build
npm run build
```

---

## 📚 Detailed Documentation

- **Backend Documentation Index:** [`ecommerce-backend/docs/README.md`](ecommerce-backend/docs/README.md)
- **Backend API Reference:** [`ecommerce-backend/docs/06-api-reference.md`](ecommerce-backend/docs/06-api-reference.md)
- **Frontend Documentation Index:** [`ecommerce-frontend/docs/README.md`](ecommerce-frontend/docs/README.md)
- **Agent Guides:** [`AGENTS.md`](AGENTS.md), [`ecommerce-backend/AGENTS.md`](ecommerce-backend/AGENTS.md), [`ecommerce-frontend/AGENTS.md`](ecommerce-frontend/AGENTS.md)

## 📄 License

MIT
