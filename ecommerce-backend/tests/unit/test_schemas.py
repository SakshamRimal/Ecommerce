import uuid
import pytest
from pydantic import ValidationError
from app.api.v1.auth.schema import UserRegisterRequest, UserResponse, TokenResponse
from app.api.v1.health.schema import HealthCheckResponse


class TestUserRegisterRequest:
    def test_valid_request(self):
        data = UserRegisterRequest(
            email="user@example.com",
            password="password123",
            full_name="John Doe",
        )
        assert data.email == "user@example.com"
        assert data.full_name == "John Doe"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="not-an-email",
                password="password123",
                full_name="John",
            )

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="user@example.com",
                password="short",
                full_name="John",
            )

    def test_password_max_length(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="user@example.com",
                password="a" * 129,
                full_name="John",
            )

    def test_empty_full_name(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="user@example.com",
                password="password123",
                full_name="",
            )

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(email="user@example.com")


class TestUserResponse:
    def test_valid_response(self):
        resp = UserResponse(
            id=uuid.uuid4(),
            email="user@example.com",
            full_name="John Doe",
            is_active=True,
            role="customer",
        )
        assert resp.is_active is True
        assert resp.role == "customer"

    def test_missing_role_fails(self):
        with pytest.raises(ValidationError):
            UserResponse(
                id=uuid.uuid4(),
                email="user@example.com",
                full_name="John Doe",
                is_active=True,
            )

    def test_from_attributes(self):
        from app.api.v1.auth.schema import UserResponse as UR
        assert hasattr(UR.model_config, "get")
        assert UR.model_config.get("from_attributes") is True


class TestTokenResponse:
    def test_valid_token_response(self):
        token = TokenResponse(
            access_token="abc123",
            refresh_token="def456",
        )
        assert token.token_type == "bearer"
        assert token.access_token == "abc123"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="abc123")


class TestHealthCheckResponse:
    def test_valid_response(self):
        resp = HealthCheckResponse(status="ok", database="up")
        assert resp.status == "ok"
        assert resp.database == "up"

    def test_degraded_response(self):
        resp = HealthCheckResponse(status="degraded", database="down")
        assert resp.database == "down"
