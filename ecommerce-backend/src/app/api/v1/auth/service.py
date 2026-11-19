import uuid

from app.api.v1.auth.repository import UserRepository
from app.api.v1.auth.schema import UserRegisterRequest, TokenResponse, UserResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password_async,
    verify_password_async,
)
from app.core.token_store import consume_token_once, is_token_revoked, revoke_token
from app.core.exceptions import ConflictError, UnauthorizedError


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, data: UserRegisterRequest) -> UserResponse:
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already exists")

        hashed = await hash_password_async(data.password)
        user = await self.repository.create(data.email, hashed, data.full_name)

        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:

        user = await self.repository.get_by_email(email)
        if not user or not await verify_password_async(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("User is inactive")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        jti = payload.get("jti")
        if jti and await is_token_revoked(jti):
            raise UnauthorizedError("Refresh token has been revoked")

        user_id = payload.get("sub")
        try:
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            raise UnauthorizedError("Invalid refresh token")

        user = await self.repository.get_by_id(user_uuid)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        # Atomic rotation: ensure two concurrent refresh requests with the same
        # token cannot both succeed.
        if jti and not await consume_token_once(jti, payload.get("exp")):
            raise UnauthorizedError("Refresh token has been revoked")

        access_token = create_access_token(subject=str(user_uuid))
        new_refresh_token = create_refresh_token(subject=str(user_uuid))
        return TokenResponse(
            access_token=access_token, refresh_token=new_refresh_token
        )

    async def logout(self, *tokens: str | None) -> None:
        """Revoke any supplied access/refresh tokens. Best effort and idempotent."""
        for token in tokens:
            if not token:
                continue
            try:
                payload = decode_token(token)
            except ValueError:
                continue
            await revoke_token(payload.get("jti"), payload.get("exp"))
