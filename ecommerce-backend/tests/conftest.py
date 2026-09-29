import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db_session
from app.models.user import User, UserRole


# ─── Unit Test Fixtures ───────────────────────────────────────────────


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$LJ3m4ys3Gq0oRf1KqKqKqOqKqKqKqKqKqKqKqKqKqKqKqKqKqK",
        full_name="Test User",
        is_active=True,
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
def sample_admin_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password="$2b$12$LJ3m4ys3Gq0oRf1KqKqKqOqKqKqKqKqKqKqKqKqKqKqKqKqKq",
        full_name="Admin User",
        is_active=True,
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_health_repository():
    repo = AsyncMock()
    repo.check_database = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_auth_repository():
    repo = AsyncMock()
    repo.get_by_email = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


# ─── Integration Test Fixtures ────────────────────────────────────────


async def override_get_db_session():
    """Yield a mock session for integration tests (no real DB needed)."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    yield session


@pytest.fixture
async def client():
    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
