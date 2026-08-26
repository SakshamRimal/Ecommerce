from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user
from app.models.user import User 
from app.api.v1.auth.repository import UserRepository
from app.api.v1.auth.service import AuthService
from app.api.v1.auth.schema import (
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(UserRepository(session))
    

@router.post("/register" , response_model=UserResponse , status_code=201)
async def register(
    
)