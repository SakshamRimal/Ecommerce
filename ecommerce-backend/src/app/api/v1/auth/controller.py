from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user, oauth2_scheme
from app.models.user import User 
from app.api.v1.auth.repository import UserRepository
from app.api.v1.auth.service import AuthService
from app.api.v1.auth.schema import (
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(UserRepository(session))
    

@router.post("/register" , response_model=UserResponse , status_code=201)
async def register(
    data: UserRegisterRequest,
    service: AuthService = Depends(get_auth_service)
):
    return await service.register(data)

@router.post("/login" , response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    return await service.login(form_data.username , form_data.password)

@router.post("/refresh" , response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    return await service.refresh_token(data.refresh_token)


@router.post("/logout")
async def logout(
    data: LogoutRequest | None = None,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Revoke the current access token and, when supplied, the refresh token."""
    await service.logout(
        access_token,
        data.refresh_token if data else None,
    )
    return {"detail": "Logged out"}

@router.get("/me" , response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


