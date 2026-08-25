import uuid 
from sqlalchemy import select 
from sqlalchemy.orm import joinedload 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self , session:AsyncSession):
        self.session = session
        
    async def get_by_id(self , product_id: uuid.UUID) -> Product | None:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_products(self , limit:int =20 , offset: int = 0 ) -> list[Product]:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .order_by(Product.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    