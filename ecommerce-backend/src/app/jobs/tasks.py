import structlog
from sqlalchemy import select
from sqlalchemy.orm import joinedload , selectinload

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory
from app.models.product import Product
from app.core.email import send_order_confirmation_email
from app.models.order import Order
from app.core.elasticsearch import get_es_client




logger = structlog.get_logger("jobs")
settings = get_settings()

async def index_product_task(ctx , product_id: str) -> None:
    """Background job: sync one product from Postgres into Elasticsearch without blocking the main thread."""
    es_client = get_es_client()
    
    async with AsyncSessionFactory() as session:
        stmt = (
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            logger.warning(f"Product with ID {product_id} not found. Skipping indexing.")
            return
        
        doc = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category_id":str(product.category_id),
            "category_name": product.category.name , 
            "price":float(product.price),
            "stock_quantity": product.stock_quantity,
            "created_at": product.created_at.isoformat(),
        }
        
        await es_client.index(
            index=settings.elasticsearch_products_index,
            id=str(product.id),
            document=doc,
        )
        logger.info(f"Product with ID {product_id} indexed in Elasticsearch successfully.")
    
async def delete_product_from_index_task(ctx , product_id: str) -> None:
    es_client = get_es_client()
    try:
        await es_client.delete(index=settings.elasticsearch_products_index, id=product_id)
        logger.info(f"Product with ID {product_id} deleted from Elasticsearch index successfully.")
    except Exception as e:
        logger.warning(f"Failed to delete product with ID {product_id} from Elasticsearch index. Error: {e}")
 
    
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
        
