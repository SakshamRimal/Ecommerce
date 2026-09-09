import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.models.product import Product


class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_cart(self, user_id: uuid.UUID) -> Cart:
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id)
            self.session.add(cart)
            await self.session.flush()
            # Re-fetch with relationships loaded
            cart = await self.get_cart(user_id)

        return cart

    async def get_cart(self, user_id: uuid.UUID) -> Cart | None:
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cart_item(
        self, cart_id: uuid.UUID, product_id: uuid.UUID
    ) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_item(
        self, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartItem:
        item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_item_quantity(
        self, item: CartItem, quantity: int
    ) -> CartItem:
        item.quantity = quantity
        await self.session.flush()
        return item

    async def remove_item(self, item: CartItem) -> None:
        await self.session.delete(item)
        await self.session.flush()

    async def clear_cart(self, cart_id: uuid.UUID) -> None:
        stmt = select(CartItem).where(CartItem.cart_id == cart_id)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        for item in items:
            await self.session.delete(item)
        await self.session.flush()

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        return await self.session.get(Product, product_id)
