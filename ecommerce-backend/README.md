# Ecommerce Backend

A production-ready, async-first ecommerce API built with FastAPI, PostgreSQL, Redis, and Elasticsearch.

## Overview

This is a RESTful backend for an ecommerce platform supporting product management, shopping carts, order processing, full-text search, background jobs, and observability. Built with a clean layered architecture (Controller → Service → Repository) and designed for horizontal scaling.

## Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | FastAPI 0.141 |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Cache | Redis 7 |
| Search | Elasticsearch 8.15 |
| Background Jobs | arq (Redis-based) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Observability | OpenTelemetry, Prometheus, structlog |
| Containerization | Docker, Docker Compose |
| Package Manager | uv |

## Project Structure

```
ecommerce-backend/
├── src/
│   └── app/
│       ├── api/v1/
│       │   ├── auth/          # Register, login, token refresh
│       │   ├── products/      # CRUD with optimistic locking
│       │   ├── categories/    # Product categories
│       │   ├── cart/          # Shopping cart management
│       │   ├── orders/        # Order creation with idempotency
│       │   ├── search/        # Elasticsearch full-text search
│       │   └── health/        # Health check endpoint
│       ├── core/              # Config, security, logging, metrics, cache, etc.
│       ├── db/                # Engine, session factory
│       ├── jobs/              # Background tasks (arq worker)
│       ├── middlewares/       # Request context, security headers
│       ├── models/            # SQLAlchemy ORM models
│       └── main.py            # App factory, lifespan, middleware stack
├── migrations/                # Alembic migration versions
├── tests/                     # Unit, integration, load tests
├── Dockerfile
├── docker-compose.yml
├── otel-collector-config.yaml
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Elasticsearch 8.15+
- uv (package manager)

### 1. Clone and install

```bash
git clone <repo-url>
cd ecommerce-backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src
```

API docs at http://localhost:8000/docs

### Docker (recommended)

```bash
docker compose up --build
```

This starts all services: PostgreSQL, Redis, Elasticsearch, OpenTelemetry Collector, API, and worker.

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | List products (with pagination) |
| POST | `/api/v1/products` | Create product (admin) |
| GET | `/api/v1/products/{id}` | Get product by ID |
| PATCH | `/api/v1/products/{id}` | Update product (admin) |
| DELETE | `/api/v1/products/{id}` | Delete product (admin) |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories` | List categories |
| POST | `/api/v1/categories` | Create category (admin) |
| GET | `/api/v1/categories/{id}` | Get category |
| PATCH | `/api/v1/categories/{id}` | Update category (admin) |
| DELETE | `/api/v1/categories/{id}` | Delete category (admin) |

### Cart
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cart` | Get current cart |
| POST | `/api/v1/cart/items` | Add item to cart |
| PATCH | `/api/v1/cart/items/{product_id}` | Update item quantity |
| DELETE | `/api/v1/cart/items/{product_id}` | Remove item from cart |
| DELETE | `/api/v1/cart` | Clear cart |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/orders` | Create order from cart |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/search/products?q=term` | Full-text search products |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check (DB status) |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

## Key Features

### Authentication & Authorization
- JWT-based auth with access + refresh tokens
- Role-based access control (customer, admin)
- Password hashing with bcrypt

### Product Management
- Optimistic locking via version column
- Cache invalidation on updates
- Background Elasticsearch indexing

### Order Processing
- Idempotency keys for duplicate prevention
- Stock validation with row-level locking
- Order confirmation emails via background jobs

### Observability
- Structured logging with structlog (JSON in production)
- Request tracing with OpenTelemetry
- Prometheus metrics (order counts, values)
- Request ID propagation

### Caching
- Redis-based product list caching
- Automatic cache invalidation on writes

## CLI Commands

```bash
# Create an admin user
uv run ecommerce create-admin --email admin@example.com --password secret123 --full-name "Admin"

# Apply migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Run load tests
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# Load tests
uv run locust -f tests/load/locustfile.py --host http://localhost:8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | — |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `ecommerce` |
| `JWT_SECRET_KEY` | Secret for JWT signing | — |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ARQ_REDIS_URL` | Redis URL for job queue | `redis://localhost:6379/1` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `OTEL_EXPORTER_ENDPOINT` | OTel collector endpoint | `localhost:4317` |
| `MAIL_SERVER` | SMTP server | — |
| `MAIL_PORT` | SMTP port | `2525` |

## License

MIT
