import uuid
import pytest
from unittest.mock import AsyncMock
from app.api.v1.auth.service import AuthService
from app.api.v1.auth.schema import UserRegisterRequest, TokenResponse
from app.core.exceptions import ConflictError, UnauthorizedError


class TestAuthServiceRegister:
    async def test_register_new_user(self, mock_auth_repository, mock_session):
        from app.models.user import User, UserRole

        user = User(
            id=uuid.uuid4(),
            email="new@example.com",
            hashed_password="hashed",
            full_name="New User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_email = AsyncMock(return_value=None)
        mock_auth_repository.create = AsyncMock(return_value=user)

        service = AuthService(mock_auth_repository)
        data = UserRegisterRequest(
            email="new@example.com",
            password="password123",
            full_name="New User",
        )
        result = await service.register(data)

        assert result.email == "new@example.com"
        assert result.full_name == "New User"
        mock_auth_repository.get_by_email.assert_awaited_once_with("new@example.com")

    async def test_register_duplicate_email_raises(self, mock_auth_repository):
        from app.models.user import User, UserRole

        existing = User(
            id=uuid.uuid4(),
            email="existing@example.com",
            hashed_password="hashed",
            full_name="Existing",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_email = AsyncMock(return_value=existing)

        service = AuthService(mock_auth_repository)
        data = UserRegisterRequest(
            email="existing@example.com",
            password="password123",
            full_name="Existing",
        )
        with pytest.raises(ConflictError, match="Email already exists"):
            await service.register(data)


class TestAuthServiceLogin:
    async def test_login_invalid_email(self, mock_auth_repository):
        mock_auth_repository.get_by_email = AsyncMock(return_value=None)

        service = AuthService(mock_auth_repository)
        with pytest.raises(UnauthorizedError, match="Invalid email or password"):
            await service.login("nobody@example.com", "password123")

    async def test_login_wrong_password(self, mock_auth_repository):
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        hashed = hash_password("correctpassword")
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password=hashed,
            full_name="User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_email = AsyncMock(return_value=user)

        service = AuthService(mock_auth_repository)
        with pytest.raises(UnauthorizedError, match="Invalid email or password"):
            await service.login("user@example.com", "wrongpassword")

    async def test_login_inactive_user(self, mock_auth_repository):
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        hashed = hash_password("correctpassword")
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password=hashed,
            full_name="User",
            is_active=False,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_email = AsyncMock(return_value=user)

        service = AuthService(mock_auth_repository)
        with pytest.raises(UnauthorizedError, match="User is inactive"):
            await service.login("user@example.com", "correctpassword")

    async def test_login_success_returns_tokens(self, mock_auth_repository):
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        hashed = hash_password("correctpassword")
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password=hashed,
            full_name="User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_email = AsyncMock(return_value=user)

        service = AuthService(mock_auth_repository)
        result = await service.login("user@example.com", "correctpassword")

        assert isinstance(result, TokenResponse)
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0
        assert result.token_type == "bearer"
