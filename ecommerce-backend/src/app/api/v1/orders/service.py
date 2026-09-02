import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.orders.repository import OrderRepository
from app.api.v1.orders.schema import OrderResponse, CreateOrderRequest
from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import Cart, CartItem
from app.core.exceptions import ConflictError, NotFoundError
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class OrderService:
    def __init__(self, session: AsyncSession, repository: OrderRepository):
        self.session = session  # needed here to control the transaction boundary directly
        self.repository = repository

    async def create_order_from_cart(
        self, user_id: uuid.UUID, data: CreateOrderRequest
    ) -> OrderResponse:
        # --- IDEMPOTENCY CHECK (before touching anything else) ---
        existing = await self.repository.get_by_idempotency_key(data.idempotency_key)
        if existing:
            # Same request retried (double-click, network retry) — return the SAME order, don't create a new one
            return OrderResponse.model_validate(existing)

        # --- FETCH THE USER'S CART WITH ITEMS ---
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart or not cart.items:
            raise ConflictError("Cart is empty — nothing to order")

        # ================= BEGIN TRANSACTION BODY =================
        # (the AsyncSession already has an open transaction — everything below
        #  is part of ONE atomic unit until we commit at the very end)

        order_items: list[OrderItem] = []
        total_amount = 0

        for cart_item in cart.items:
            # Lock the product row — prevents race conditions on concurrent orders
            product = await self.repository.get_product_for_update(cart_item.product_id)

            if not product:
                raise NotFoundError(f"Product '{cart_item.product_id}' no longer exists")

            if product.stock_quantity < cart_item.quantity:
                # Something else bought it in the meantime, or it was always insufficient
                raise ConflictError(
                    f"Insufficient stock for '{product.name}' "
                    f"(requested {cart_item.quantity}, available {product.stock_quantity})"
                )

            # Decrement stock — still inside the same uncommitted transaction
            product.stock_quantity -= cart_item.quantity

            # Snapshot price/name at time of purchase (Step 2's rationale)
            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=cart_item.quantity,
            )
            order_items.append(order_item)
            total_amount += float(product.price) * cart_item.quantity

        order = Order(
            user_id=user_id,
            status=OrderStatus.CONFIRMED,
            total_amount=total_amount,
            idempotency_key=data.idempotency_key,
            items=order_items,
        )
        self.repository.add_order(order)

        # Clear the cart — also part of the same transaction
        for cart_item in cart.items:
            await self.session.delete(cart_item)

        # ================= END TRANSACTION BODY =================
        # Single commit — everything above succeeds together, or...
        await self.session.commit()
        await self.session.refresh(order, attribute_names=["items"])

        return OrderResponse.model_validate(order)
        # ...if ANY exception was raised above, get_db_session's except block
        # (from Day 1) calls session.rollback() automatically — NOTHING above
        # gets persisted. Stock stays untouched, no partial order exists.