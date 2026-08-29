import uuid 
from fastapi import Depends 
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.security import decode_token
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.api.v1.auth.repository import UserRepository
from app.models.user import User, UserRole 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)) -> User:
    try:
        payload = decode_token(token)
    except ValueError:
        raise UnauthorizedError("Invalid token")
    
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    
    repository = UserRepository(session)
    user = await repository.get_by_id(uuid.UUID(payload["sub"]))
    
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin privileges required")
    return current_user
    
