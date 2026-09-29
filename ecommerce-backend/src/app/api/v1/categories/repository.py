import uuid 
from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models.category import Category
from app.core.exceptions import ConflictError

class CategoryRepository:
    def __init__(self , session: AsyncSession):
        self.session = session 
        
    async def get_by_id(self , category_id: uuid.UUID) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_slug(self , slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_all(self , limit: int = 50 , offset: int = 0) -> list[Category]:
        stmt = select(Category).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self , name: str , slug: str) -> Category:
        category = Category(name=name , slug=slug)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def update(self , category: Category , name: str) -> Category:
        category.name = name 
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
    async def delete(self , category:Category) -> None:
        try:
            await self.session.delete(category)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(
                "Cannot delete category: it still has products referenced by orders or carts"
            )
        
    
    
    

        

