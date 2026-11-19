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


def _make_mock_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.expire = MagicMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.get = AsyncMock(return_value=None)

    default_result = MagicMock()
    default_result.scalar_one.return_value = 1
    default_result.scalar_one_or_none.return_value = None
    default_result.scalars.return_value.all.return_value = []
    default_result.scalars.return_value.first.return_value = None
    session.execute = AsyncMock(return_value=default_result)
    return session


@pytest.fixture
def mock_session() -> AsyncMock:
    return _make_mock_session()


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
    yield _make_mock_session()


@pytest.fixture
async def client():
    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
