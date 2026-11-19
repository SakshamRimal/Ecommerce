import uuid 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product

class OrderRepository:
    def __init__(self , session: AsyncSession):
        self.session = session 
        
    async def get_by_idempotency_key(self , key: str) -> Order | None:
        stmt = select(Order).options(selectinload(Order.items)).where(Order.idempotency_key == key)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_product_for_update(self , product_id: uuid.UUID) -> Product | None:
        """SELECT ... FOR UPDATE with populate_existing=True so locked rows always
        reflect the latest committed stock_quantity rather than stale session cache."""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    def add_order(self , order: Order):
        self.session.add(order) # NOT committed yet — part of a larger transaction
        
    async def get_by_id(self , order_id: uuid.UUID) -> Order | None:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order | None:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user_for_update(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is not None:
            await self.session.refresh(order, attribute_names=["items"])
        return order

    async def list_by_user(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    