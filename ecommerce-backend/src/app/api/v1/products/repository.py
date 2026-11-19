import uuid 
from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError
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

    async def search_by_keyword(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[Product]:
        """Basic PostgreSQL fallback used when Elasticsearch is unavailable."""
        pattern = f"%{query}%"
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(
                Product.name.ilike(pattern) | Product.description.ilike(pattern)
            )
        )
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
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
    
    async def update(self, product: Product, expected_version: int, **kwargs) -> Product:
        """Atomically update a product using row locking + an optimistic version check.

        Locking the row before comparing the version serialises concurrent writers,
        which is what makes the version check meaningful.
        """
        stmt = (
            select(Product)
            .where(Product.id == product.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        locked = result.scalar_one_or_none()

        if locked is None:
            raise ConflictError("Product no longer exists")

        if locked.version != expected_version:
            raise ConflictError("Product has been modified by another transaction")

        for key, value in kwargs.items():
            if value is not None:
                setattr(locked, key, value)

        locked.version += 1
        await self.session.commit()
        await self.session.refresh(locked, attribute_names=["category"])
        return locked

    async def delete(self , product: Product) -> None:
        try:
            await self.session.delete(product)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(
                "Cannot delete product: it is still referenced by a cart or order"
            )
            
    async def semantic_search(
        self,
        embedding: list[float],
        limit: int = 10,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[Product]:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.embedding.is_not(None))
        )
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        stmt = (
            stmt.order_by(Product.embedding.cosine_distance(embedding))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())