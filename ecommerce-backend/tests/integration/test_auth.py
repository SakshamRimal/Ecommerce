import uuid
from unittest.mock import AsyncMock
from httpx import AsyncClient
from app.main import app
from app.api.v1.auth.service import AuthService
from app.api.v1.auth.controller import get_auth_service
from app.api.v1.auth.schema import TokenResponse, UserResponse
from app.core.deps import get_current_user
from app.models.user import User, UserRole


def make_mock_service() -> AsyncMock:
    return AsyncMock(spec=AuthService)


class TestRegisterEndpoint:
    async def test_register_success(self, client: AsyncClient):
        mock_service = make_mock_service()
        user = User(
            id=uuid.uuid4(),
            email="new@example.com",
            hashed_password="x",
            full_name="New User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_service.register = AsyncMock(
            return_value=UserResponse.model_validate(user)
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        app.dependency_overrides.pop(get_auth_service, None)

    async def test_register_validation_error_short_password(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "short",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 422

    async def test_register_validation_error_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com"},
        )
        assert resp.status_code == 422

    async def test_register_duplicate_email(self, client: AsyncClient):
        from app.core.exceptions import ConflictError

        mock_service = make_mock_service()
        mock_service.register = AsyncMock(
            side_effect=ConflictError("Email already exists")
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "full_name": "Existing",
            },
        )
        assert resp.status_code == 409
        app.dependency_overrides.pop(get_auth_service, None)


class TestLoginEndpoint:
    async def test_login_success(self, client: AsyncClient):
        mock_service = make_mock_service()
        mock_service.login = AsyncMock(
            return_value=TokenResponse(
                access_token="access-token-abc",
                refresh_token="refresh-token-xyz",
            )
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "access-token-abc"
        assert data["token_type"] == "bearer"
        app.dependency_overrides.pop(get_auth_service, None)

    async def test_login_invalid_credentials(self, client: AsyncClient):
        from app.core.exceptions import UnauthorizedError

        mock_service = make_mock_service()
        mock_service.login = AsyncMock(
            side_effect=UnauthorizedError("Invalid email or password")
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        app.dependency_overrides.pop(get_auth_service, None)

    async def test_login_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={})
        assert resp.status_code == 422


class TestMeEndpoint:
    async def test_me_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    async def test_me_returns_user(self, client: AsyncClient):
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password="x",
            full_name="User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        app.dependency_overrides[get_current_user] = lambda: user

        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@example.com"
        app.dependency_overrides.pop(get_current_user, None)


class TestRefreshAndLogoutEndpoints:
    async def test_refresh_success(self, client: AsyncClient):
        mock_service = make_mock_service()
        mock_service.refresh_token = AsyncMock(
            return_value=TokenResponse(
                access_token="new-access",
                refresh_token="new-refresh",
            )
        )
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "old-refresh"},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"] == "new-access"
        app.dependency_overrides.pop(get_auth_service, None)

    async def test_logout_success(self, client: AsyncClient):
        user = User(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password="x",
            full_name="User",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        mock_service = make_mock_service()
        mock_service.logout = AsyncMock(return_value=None)
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_auth_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer dummy-access-token"},
            json={"refresh_token": "dummy-refresh-token"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"detail": "Logged out"}
        mock_service.logout.assert_awaited_once_with(
            "dummy-access-token", "dummy-refresh-token"
        )
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_auth_service, None)
