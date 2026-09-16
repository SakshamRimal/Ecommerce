FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first — Docker layer caching: only re-installs deps if these change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Now copy the actual application code
COPY src/ ./src/
COPY alembic.ini ./

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Graceful shutdown: uvicorn handles SIGTERM correctly by default (ties back to Day 1's lifespan)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]