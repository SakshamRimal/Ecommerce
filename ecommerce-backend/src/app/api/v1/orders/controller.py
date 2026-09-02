from fastapi import APIRouter , Depends 
from sqlalchemy.ext.asyncio import AsyncSession 

from app.db.session import get_db_session 
from app.core.deps import get_current_user 
from app.models.user import User 
from app.api.v1.orders.repository import OrderRepository
from app.api.v1.orders.service import OrderService
from app.api.v1.orders.schema import OrderResponse , CreateOrderRequest

router = APIRouter(prefix="/orders" , tags=["orders"])

def get_order_service(session: AsyncSession  = Depends(get_db_session)) -> OrderService:
    return OrderService(session , OrderRepository(session))

@router.post("" , response_model=OrderResponse , status_code=201)
async def create_order(
    data: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    return await service.create_order_from_cart(current_user.id , data)


    
