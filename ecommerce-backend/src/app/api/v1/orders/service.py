import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.orders.repository import OrderRepository
from app.api.v1.orders.schema import OrderResponse, CreateOrderRequest
from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import Cart, CartItem
from app.core.exceptions import ConflictError, NotFoundError
from app.core.job_queue import get_job_queue
from app.core.metrics import orders_created_total, orders_failed_total, order_value_dollars



class OrderService:
    def __init__(self, session: AsyncSession, repository: OrderRepository, current_user):
        self.session = session
        self.repository = repository
        self.current_user = current_user

    async def create_order_from_cart(
        self, user_id: uuid.UUID, data: CreateOrderRequest
    ) -> OrderResponse:
        # --- IDEMPOTENCY CHECK ---
        existing = await self.repository.get_by_idempotency_key(data.idempotency_key)
        if existing:
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
            orders_failed_total.labels(reason="empty_cart").inc()
            raise ConflictError("Cart is empty — nothing to order")

        # ================= BEGIN TRANSACTION BODY =================
        order_items: list[OrderItem] = []
        total_amount = 0

        try:
            for cart_item in cart.items:
                product = await self.repository.get_product_for_update(cart_item.product_id)

                if not product:
                    raise NotFoundError(f"Product '{cart_item.product_id}' no longer exists")

                if product.stock_quantity < cart_item.quantity:
                    orders_failed_total.labels(reason="insufficient_stock").inc()
                    raise ConflictError(
                        f"Insufficient stock for '{product.name}' "
                        f"(requested {cart_item.quantity}, available {product.stock_quantity})"
                    )

                product.stock_quantity -= cart_item.quantity

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

            for cart_item in cart.items:
                await self.session.delete(cart_item)

        except (ConflictError, NotFoundError):
            raise
        except Exception:
            orders_failed_total.labels(reason="internal_error").inc()
            raise

        # ================= END TRANSACTION BODY =================
        await self.session.commit()
        await self.session.refresh(order, attribute_names=["items"])

        orders_created_total.inc()
        order_value_dollars.observe(total_amount)

        queue = await get_job_queue()
        await queue.enqueue_job(
            "send_order_confirmation_task",
            str(order.id),
            self.current_user.email,
            self.current_user.full_name,
        )

        return OrderResponse.model_validate(order)