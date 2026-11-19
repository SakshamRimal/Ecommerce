import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user
from app.models.user import User
from app.api.v1.orders.repository import OrderRepository
from app.api.v1.orders.service import OrderService
from app.api.v1.orders.schema import OrderResponse, CreateOrderRequest

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> OrderService:
    return OrderService(session, OrderRepository(session), current_user)


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    data: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
):
    return await service.create_order_from_cart(service.current_user.id, data)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrderService = Depends(get_order_service),
):
    """Return the current user's orders, newest first."""
    return await service.list_orders(
        service.current_user.id, limit=limit, offset=offset
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    service: OrderService = Depends(get_order_service),
):
    return await service.get_order(service.current_user.id, order_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID,
    service: OrderService = Depends(get_order_service),
):
    """Cancel an order and restore its stock."""
    return await service.cancel_order(service.current_user.id, order_id)
