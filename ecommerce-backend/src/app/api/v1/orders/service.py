import asyncio
import uuid
from decimal import Decimal

from arq.connections import ArqRedis
import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.orders.repository import OrderRepository
from app.api.v1.orders.schema import OrderResponse, CreateOrderRequest
from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import Cart, CartItem
from app.core.email import send_order_confirmation_email
from app.core.exceptions import ConflictError, NotFoundError
from app.core.cache import cache_delete_pattern
from app.core.job_queue import get_job_queue
from app.core.metrics import orders_created_total, orders_failed_total, order_value_dollars

logger = structlog.get_logger("orders")


class OrderService:
    def __init__(self, session: AsyncSession, repository: OrderRepository, current_user):
        self.session = session
        self.repository = repository
        self.current_user = current_user
        self._background_tasks: set[asyncio.Task] = set()

    async def _send_confirmation_email_safe(
        self,
        to_email: str,
        full_name: str,
        order_id: str,
        items: list[dict],
        total_amount: str,
    ) -> None:
        try:
            await send_order_confirmation_email(
                to_email=to_email,
                full_name=full_name,
                order_id=order_id,
                items=items,
                total_amount=total_amount,
            )
            logger.info(
                "order_confirmation_email_sent",
                order_id=order_id,
                to_email=to_email,
            )
        except Exception as exc:
            logger.warning(
                "order_confirmation_email_failed",
                order_id=order_id,
                to_email=to_email,
                error=str(exc),
            )

    async def create_order_from_cart(
        self, user_id: uuid.UUID, data: CreateOrderRequest
    ) -> OrderResponse:
        # --- IDEMPOTENCY CHECK (FAST PATH) ---
        existing = await self.repository.get_by_idempotency_key(data.idempotency_key)
        if existing:
            return OrderResponse.model_validate(existing)

        # --- LOCK & FETCH THE USER'S CART WITH ITEMS ---
        # Locking the Cart row serializes concurrent checkout requests from the
        # same user so two simultaneous requests cannot double-order the same cart.
        stmt = (
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart or not cart.items:
            # Re-check idempotency in case a concurrent request with the same
            # idempotency key just committed and cleared the cart while we
            # waited on the Cart lock.
            existing = await self.repository.get_by_idempotency_key(data.idempotency_key)
            if existing:
                return OrderResponse.model_validate(existing)
            orders_failed_total.labels(reason="empty_cart").inc()
            raise ConflictError("Cart is empty — nothing to order")

        # ================= BEGIN TRANSACTION BODY =================
        order_items: list[OrderItem] = []
        total_amount = Decimal("0")

        # Sort cart items by product_id before acquiring row locks to guarantee
        # a strict global lock order and prevent multi-product deadlocks.
        sorted_cart_items = sorted(cart.items, key=lambda ci: str(ci.product_id))

        try:
            for cart_item in sorted_cart_items:
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
                product.version = (product.version or 1) + 1

                order_item = OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=cart_item.quantity,
                )
                order_items.append(order_item)
                total_amount += Decimal(str(product.price)) * cart_item.quantity

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
        try:
            await self.session.commit()
        except IntegrityError:
            # Two concurrent requests used the same idempotency key. The other
            # request won the unique constraint; return its order.
            await self.session.rollback()
            existing = await self.repository.get_by_idempotency_key(data.idempotency_key)
            if existing:
                return OrderResponse.model_validate(existing)
            orders_failed_total.labels(reason="internal_error").inc()
            raise

        await self.session.refresh(order, attribute_names=["items"])

        orders_created_total.inc()
        order_value_dollars.observe(float(total_amount))

        await cache_delete_pattern("product:list:*")

        email_items = [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": f"{Decimal(str(item.unit_price)):.2f}",
            }
            for item in order.items
        ]
        formatted_total = f"{Decimal(str(order.total_amount)):.2f}"

        try:
            queue = await get_job_queue()
            if isinstance(queue, ArqRedis):
                worker_active = bool(await queue.exists("arq:health-check"))
                if worker_active:
                    await queue.enqueue_job(
                        "send_order_confirmation_task",
                        str(order.id),
                        self.current_user.email,
                        self.current_user.full_name,
                    )
                else:
                    task = asyncio.create_task(
                        self._send_confirmation_email_safe(
                            to_email=self.current_user.email,
                            full_name=self.current_user.full_name,
                            order_id=str(order.id),
                            items=email_items,
                            total_amount=formatted_total,
                        )
                    )
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
            else:
                await queue.enqueue_job(
                    "send_order_confirmation_task",
                    str(order.id),
                    self.current_user.email,
                    self.current_user.full_name,
                )
            for item in order.items:
                await queue.enqueue_job("index_product_task", str(item.product_id))
        except Exception as exc:
            # The order is already committed. A failed enqueue must not turn a
            # successful checkout into a 500.
            logger.warning(
                "order_confirmation_enqueue_failed",
                order_id=str(order.id),
                error=str(exc),
            )

        return OrderResponse.model_validate(order)

    async def list_orders(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[OrderResponse]:
        orders = await self.repository.list_by_user(user_id, limit=limit, offset=offset)
        return [OrderResponse.model_validate(order) for order in orders]

    async def get_order(
        self, user_id: uuid.UUID, order_id: uuid.UUID
    ) -> OrderResponse:
        order = await self.repository.get_by_id_for_user(order_id, user_id)
        if not order:
            raise NotFoundError(f"Order with id '{order_id}' not found")
        return OrderResponse.model_validate(order)

    async def cancel_order(
        self, user_id: uuid.UUID, order_id: uuid.UUID
    ) -> OrderResponse:
        order = await self.repository.get_by_id_for_user_for_update(order_id, user_id)
        if not order:
            raise NotFoundError(f"Order with id '{order_id}' not found")

        if order.status == OrderStatus.CANCELED:
            raise ConflictError("Order is already canceled")

        # Restore stock under the same deterministic product_id lock order used by checkout.
        for item in sorted(order.items, key=lambda oi: str(oi.product_id)):
            product = await self.repository.get_product_for_update(item.product_id)
            if product is not None:
                product.stock_quantity += item.quantity
                product.version = (product.version or 1) + 1

        order.status = OrderStatus.CANCELED
        await self.session.commit()
        await self.session.refresh(order, attribute_names=["items"])

        await cache_delete_pattern("product:list:*")

        try:
            queue = await get_job_queue()
            for item in order.items:
                await queue.enqueue_job("index_product_task", str(item.product_id))
        except Exception as exc:
            logger.warning(
                "order_cancel_reindex_enqueue_failed",
                order_id=str(order.id),
                error=str(exc),
            )

        return OrderResponse.model_validate(order)
