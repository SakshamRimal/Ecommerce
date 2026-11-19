from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.user import User 

class UserRepository:
    def __init__(self , session:AsyncSession):
        self.session = session
        
    async def get_by_email(self , email:str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self , email:str , hashed_password:str , full_name:str) -> User:
        user = User(email=email , hashed_password=hashed_password , full_name=full_name)
        self.session.add(user)
        try:
            await self.session.flush()
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("Email already exists")
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self , user_id) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    