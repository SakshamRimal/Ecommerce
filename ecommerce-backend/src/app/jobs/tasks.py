import structlog
from sqlalchemy import select
from sqlalchemy.orm import joinedload , selectinload

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory
from app.models.product import Product
from app.core.email import send_order_confirmation_email
from app.models.order import Order



logger = structlog.get_logger("jobs")
settings = get_settings()

async def send_order_confirmation_task(ctx , order_id: str , user_email: str , user_full_name: str) -> None:
    """Background job: send the order confirmation email without blocking the main thread."""
    
    async with AsyncSessionFactory() as session:
        stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            logger.warning(f"Order with ID {order_id} not found. Email not sent.")
        
        items = [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
            }
               for item in order.items
        ]
        
        try:
            await send_order_confirmation_email(
                to_email = user_email,
                full_name = user_full_name,
                order_id = str(order.id),
                items = items,
                total_amount = str(order.total_amount),
            )
            logger.info(f"Order confirmation email sent to {user_email} for order {order_id}.")
        except Exception as e:
            logger.error(f"Failed to send order confirmation email to {user_email} for order {order_id}. Error: {e}")
        
