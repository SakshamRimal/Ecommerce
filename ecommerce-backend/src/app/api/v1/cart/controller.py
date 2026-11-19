import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user
from app.models.user import User
from app.api.v1.cart.repository import CartRepository
from app.api.v1.cart.service import CartService
from app.api.v1.cart.schema import (
    CartItemRequest,
    CartItemUpdateRequest,
    CartResponse,
)

router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_service(session: AsyncSession = Depends(get_db_session)) -> CartService:
    return CartService(CartRepository(session))


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.get_cart(current_user.id)


@router.post("/items", response_model=CartResponse, status_code=201)
async def add_item(
    data: CartItemRequest,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.add_item(current_user.id, data)


@router.patch("/items/{product_id}", response_model=CartResponse)
async def update_item(
    product_id: uuid.UUID,
    data: CartItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.update_item_quantity(
        current_user.id, product_id, data.quantity
    )


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_item(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.remove_item(current_user.id, product_id)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service),
):
    return await service.clear_cart(current_user.id)
