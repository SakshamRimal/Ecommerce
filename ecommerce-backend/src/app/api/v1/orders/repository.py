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
        """SELECT ... FOR UPDATE to lock the product row for update to prevent race conditions during"""
        stmt = select(Product).where(Product.id == product_id).with_for_update()
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
    
    