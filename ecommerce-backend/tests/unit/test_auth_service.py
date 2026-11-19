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


class TestAuthServiceRefreshAndLogout:
    async def test_refresh_token_rotates_and_revokes_previous(self, mock_auth_repository):
        from app.models.user import User, UserRole
        from app.core.security import create_refresh_token, decode_token
        from app.core.token_store import clear_memory_revocations, is_token_revoked

        clear_memory_revocations()
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="user@example.com",
            hashed_password="hashed",
            full_name="User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_auth_repository.get_by_id = AsyncMock(return_value=user)

        old_refresh = create_refresh_token(subject=str(user_id))
        old_jti = decode_token(old_refresh)["jti"]

        service = AuthService(mock_auth_repository)
        tokens = await service.refresh_token(old_refresh)

        assert isinstance(tokens, TokenResponse)
        assert tokens.refresh_token != old_refresh
        assert await is_token_revoked(old_jti) is True

        with pytest.raises(UnauthorizedError, match="revoked"):
            await service.refresh_token(old_refresh)

    async def test_refresh_rejects_access_token(self, mock_auth_repository):
        from app.core.security import create_access_token

        access = create_access_token(subject=str(uuid.uuid4()))
        service = AuthService(mock_auth_repository)
        with pytest.raises(UnauthorizedError, match="Invalid token type"):
            await service.refresh_token(access)

    async def test_logout_revokes_tokens(self, mock_auth_repository):
        from app.core.security import create_access_token, create_refresh_token, decode_token
        from app.core.token_store import clear_memory_revocations, is_token_revoked

        clear_memory_revocations()
        uid = str(uuid.uuid4())
        access = create_access_token(subject=uid)
        refresh = create_refresh_token(subject=uid)

        service = AuthService(mock_auth_repository)
        await service.logout(access, refresh, "invalid-token", None)

        assert await is_token_revoked(decode_token(access)["jti"]) is True
        assert await is_token_revoked(decode_token(refresh)["jti"]) is True

    async def test_user_repository_create_concurrent_integrity_error_raises_409(
        self, mock_session
    ):
        from sqlalchemy.exc import IntegrityError
        from app.api.v1.auth.repository import UserRepository

        mock_session.flush = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("users_email_key"))
        )
        repo = UserRepository(mock_session)
        with pytest.raises(ConflictError, match="Email already exists"):
            await repo.create("dup@example.com", "hashed", "Dup User")
        mock_session.rollback.assert_awaited_once()

    async def test_consume_token_once_blocks_concurrent_replay(self):
        from app.core.token_store import clear_memory_revocations, consume_token_once
        from unittest.mock import patch

        clear_memory_revocations()
        with patch(
            "app.core.token_store.get_redis",
            side_effect=RuntimeError("redis offline"),
        ):
            first = await consume_token_once("jti-race-1", None)
            second = await consume_token_once("jti-race-1", None)

        assert first is True
        assert second is False
