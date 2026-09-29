import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# ─── Password Hashing ─────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        result = hash_password("mypassword123")
        assert isinstance(result, str)

    def test_hash_password_is_not_plaintext(self):
        result = hash_password("mypassword123")
        assert result != "mypassword123"
        assert result.startswith("$2b$")

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_is_salted(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2  # same input, different hashes (salted)


# ─── JWT Tokens ───────────────────────────────────────────────────────


class TestAccessToken:
    def test_create_returns_string(self):
        token = create_access_token(subject="user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        token = create_access_token(subject="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("not.a.valid.token")

    def test_extra_claims_included(self):
        token = create_access_token(
            subject="user-123", extra_claims={"role": "admin"}
        )
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        from datetime import datetime, timedelta, timezone
        from jose import jwt as jose_jwt
        from app.core.config import get_settings

        settings = get_settings()
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "user-123", "exp": expired, "type": "access"}
        token = jose_jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(token)


class TestRefreshToken:
    def test_create_returns_string(self):
        token = create_refresh_token(subject="user-123")
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        token = create_refresh_token(subject="user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_refresh_token_type_differs_from_access(self):
        access = decode_token(create_access_token(subject="u1"))
        refresh = decode_token(create_refresh_token(subject="u1"))
        assert access["type"] != refresh["type"]
