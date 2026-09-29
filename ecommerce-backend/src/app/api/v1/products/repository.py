import uuid 
from sqlalchemy import select 
from sqlalchemy.orm import joinedload 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.core.exceptions import ConflictError


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
    
    async def list_products(
        self , limit: int = 50 , offset: int = 0 , category_id: uuid.UUID | None = None
    ) -> list[Product]:
        stmt = select(Product).options(joinedload(Product.category))
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        stmt = stmt.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self , **kwargs) -> Product:
        product = Product(**kwargs)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product , attribute_names=["category"])
        return product
    
    async def update(self, product: Product,expected_version: int , **kwargs ) -> Product:
        for key, value in kwargs.items():
            if value is not None:
                setattr(product, key, value)
                
        stmt = (
        select(Product)
        .where(Product.id == product.id, Product.version == expected_version)
    )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise ConflictError("Product has been modified by another transaction")
        
        product.version += 1  # Increment the version for optimistic locking
        await self.session.commit()
        await self.session.refresh(product, attribute_names=["category"])
        return product
    
    async def delete(self , product: Product) -> None:
        await self.session.delete(product)
        await self.session.commit()
            
    async def semantic_search(self , embedding: list[float] , limit: int = 10) -> list[Product]:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.embedding.is_not(None))
            .order_by(Product.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())