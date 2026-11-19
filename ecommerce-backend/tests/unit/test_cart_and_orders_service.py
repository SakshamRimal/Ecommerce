from decimal import Decimal
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.exc import IntegrityError

from app.api.v1.cart.schema import CartItemRequest
from app.api.v1.cart.service import CartService
from app.api.v1.orders.schema import CreateOrderRequest
from app.api.v1.orders.service import OrderService
from app.core.exceptions import ConflictError, NotFoundError
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product


def _make_product(price: str = "19.99", stock: int = 10) -> Product:
    return Product(
        id=uuid.uuid4(),
        name="Coffee Grinder",
        description="Burr grinder",
        price=Decimal(price),
        stock_quantity=stock,
        category_id=uuid.uuid4(),
        version=1,
    )


def _make_cart(user_id: uuid.UUID, items: list[CartItem] | None = None) -> Cart:
    cart = Cart(id=uuid.uuid4(), user_id=user_id)
    cart.items = items or []
    return cart


class TestCartService:
    async def test_add_item_success_and_total(self):
        user_id = uuid.uuid4()
        product = _make_product(price="25.50", stock=5)
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=uuid.uuid4(),
            product_id=product.id,
            quantity=2,
            product=product,
        )
        empty_cart = _make_cart(user_id, [])
        populated_cart = _make_cart(user_id, [cart_item])

        repo = AsyncMock()
        repo.session = MagicMock()
        repo.get_or_create_cart = AsyncMock(return_value=empty_cart)
        repo.get_product = AsyncMock(return_value=product)
        repo.get_cart_item = AsyncMock(return_value=None)
        repo.add_item = AsyncMock(return_value=cart_item)
        repo.get_cart = AsyncMock(return_value=populated_cart)

        service = CartService(repo)
        res = await service.add_item(
            user_id, CartItemRequest(product_id=product.id, quantity=2)
        )
        assert res.total == Decimal("51.00")
        assert len(res.items) == 1
        assert res.items[0].subtotal == Decimal("51.00")

    async def test_add_item_insufficient_stock_raises_409(self):
        user_id = uuid.uuid4()
        product = _make_product(stock=1)
        repo = AsyncMock()
        repo.get_or_create_cart = AsyncMock(return_value=_make_cart(user_id))
        repo.get_product = AsyncMock(return_value=product)

        service = CartService(repo)
        with pytest.raises(ConflictError, match="Insufficient stock"):
            await service.add_item(
                user_id, CartItemRequest(product_id=product.id, quantity=3)
            )

    async def test_update_item_quantity_zero_removes_item(self):
        user_id = uuid.uuid4()
        product = _make_product(stock=5)
        cart = _make_cart(user_id)
        item = CartItem(
            id=uuid.uuid4(),
            cart_id=cart.id,
            product_id=product.id,
            quantity=2,
            product=product,
        )

        repo = AsyncMock()
        repo.session = MagicMock()
        repo.get_or_create_cart = AsyncMock(return_value=cart)
        repo.get_cart_item = AsyncMock(return_value=item)
        repo.remove_item = AsyncMock()
        repo.get_cart = AsyncMock(return_value=cart)

        service = CartService(repo)
        res = await service.update_item_quantity(user_id, product.id, 0)
        repo.remove_item.assert_awaited_once_with(item)
        assert res.total == Decimal("0")

    async def test_add_item_concurrent_insert_race_recovers_and_checks_stock(self):
        user_id = uuid.uuid4()
        product = _make_product(price="20.00", stock=5)
        cart = _make_cart(user_id, [])
        winning_item = CartItem(
            id=uuid.uuid4(),
            cart_id=cart.id,
            product_id=product.id,
            quantity=2,
            product=product,
        )
        updated_cart = _make_cart(user_id, [winning_item])

        repo = AsyncMock()
        repo.session = MagicMock()
        repo.session.rollback = AsyncMock()
        repo.get_or_create_cart = AsyncMock(return_value=cart)
        repo.get_product = AsyncMock(return_value=product)
        repo.get_cart_item = AsyncMock(side_effect=[None, winning_item])
        repo.add_item = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("uq_cart_product"))
        )
        repo.update_item_quantity = AsyncMock(
            side_effect=lambda item, qty: setattr(item, "quantity", qty)
        )
        repo.get_cart = AsyncMock(return_value=updated_cart)

        service = CartService(repo)
        res = await service.add_item(
            user_id, CartItemRequest(product_id=product.id, quantity=2)
        )
        repo.session.rollback.assert_awaited_once()
        repo.update_item_quantity.assert_awaited_once_with(winning_item, 4)
        assert res.total == Decimal("80.00")


class TestOrderService:
    async def test_create_order_from_cart_decimal_total_and_stock_decrement(
        self, mock_session, sample_user
    ):
        product = _make_product(price="19.99", stock=5)
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=uuid.uuid4(),
            product_id=product.id,
            quantity=3,
            product=product,
        )
        cart = _make_cart(sample_user.id, [cart_item])

        cart_result = MagicMock()
        cart_result.scalar_one_or_none.return_value = cart
        mock_session.execute = AsyncMock(return_value=cart_result)

        def _populate_id_on_add(obj):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

        mock_session.add = MagicMock(side_effect=_populate_id_on_add)

        repo = AsyncMock()
        repo.get_by_idempotency_key = AsyncMock(return_value=None)
        repo.get_product_for_update = AsyncMock(return_value=product)
        repo.add_order = MagicMock(side_effect=_populate_id_on_add)

        mock_queue = AsyncMock()
        with (
            patch(
                "app.api.v1.orders.service.cache_delete_pattern",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.v1.orders.service.get_job_queue",
                new_callable=AsyncMock,
                return_value=mock_queue,
            ),
        ):
            service = OrderService(mock_session, repo, sample_user)
            res = await service.create_order_from_cart(
                sample_user.id, CreateOrderRequest(idempotency_key="idem-1")
            )

        assert res.status == OrderStatus.CONFIRMED
        assert res.total_amount == Decimal("59.97")
        assert product.stock_quantity == 2
        mock_session.commit.assert_awaited_once()

    async def test_create_order_idempotency_race_returns_existing(
        self, mock_session, sample_user
    ):
        product = _make_product(price="10.00", stock=5)
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=uuid.uuid4(),
            product_id=product.id,
            quantity=1,
            product=product,
        )
        cart = _make_cart(sample_user.id, [cart_item])

        cart_result = MagicMock()
        cart_result.scalar_one_or_none.return_value = cart
        mock_session.execute = AsyncMock(return_value=cart_result)
        mock_session.commit = AsyncMock(
            side_effect=IntegrityError("INSERT", {}, Exception("duplicate key"))
        )

        existing_order = Order(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("10.00"),
            idempotency_key="race-key",
            items=[
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=Decimal("10.00"),
                    quantity=1,
                )
            ],
        )

        repo = AsyncMock()
        repo.get_by_idempotency_key = AsyncMock(
            side_effect=[None, existing_order]
        )
        repo.get_product_for_update = AsyncMock(return_value=product)
        repo.add_order = MagicMock()

        service = OrderService(mock_session, repo, sample_user)
        res = await service.create_order_from_cart(
            sample_user.id, CreateOrderRequest(idempotency_key="race-key")
        )
        assert res.id == existing_order.id
        mock_session.rollback.assert_awaited_once()

    async def test_cancel_order_restores_stock(self, mock_session, sample_user):
        product = _make_product(price="30.00", stock=2)
        order = Order(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("60.00"),
            idempotency_key="cancel-key",
            items=[
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=Decimal("30.00"),
                    quantity=2,
                )
            ],
        )

        repo = AsyncMock()
        repo.get_by_id_for_user_for_update = AsyncMock(return_value=order)
        repo.get_product_for_update = AsyncMock(return_value=product)

        with (
            patch(
                "app.api.v1.orders.service.cache_delete_pattern",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.v1.orders.service.get_job_queue",
                new_callable=AsyncMock,
                return_value=AsyncMock(),
            ),
        ):
            service = OrderService(mock_session, repo, sample_user)
            res = await service.cancel_order(sample_user.id, order.id)

        assert res.status == OrderStatus.CANCELED
        assert product.stock_quantity == 4

        with pytest.raises(ConflictError, match="already canceled"):
            await service.cancel_order(sample_user.id, order.id)

    async def test_get_order_not_found_raises_404(self, mock_session, sample_user):
        repo = AsyncMock()
        repo.get_by_id_for_user = AsyncMock(return_value=None)
        service = OrderService(mock_session, repo, sample_user)
        with pytest.raises(NotFoundError):
            await service.get_order(sample_user.id, uuid.uuid4())

    async def test_checkout_locks_products_in_deterministic_uuid_order(
        self, mock_session, sample_user
    ):
        p_high = _make_product(price="10.00", stock=5)
        p_low = _make_product(price="20.00", stock=5)
        p_high.id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        p_low.id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        # Put high UUID first in cart.items to verify deterministic sorting
        ci_high = CartItem(
            id=uuid.uuid4(),
            cart_id=uuid.uuid4(),
            product_id=p_high.id,
            quantity=1,
            product=p_high,
        )
        ci_low = CartItem(
            id=uuid.uuid4(),
            cart_id=uuid.uuid4(),
            product_id=p_low.id,
            quantity=1,
            product=p_low,
        )
        cart = _make_cart(sample_user.id, [ci_high, ci_low])

        cart_result = MagicMock()
        cart_result.scalar_one_or_none.return_value = cart
        mock_session.execute = AsyncMock(return_value=cart_result)

        locked_order: list[uuid.UUID] = []

        async def _lock_product(pid: uuid.UUID):
            locked_order.append(pid)
            return p_low if pid == p_low.id else p_high

        def _populate_id_on_add(obj):
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

        repo = AsyncMock()
        repo.get_by_idempotency_key = AsyncMock(return_value=None)
        repo.get_product_for_update = AsyncMock(side_effect=_lock_product)
        repo.add_order = MagicMock(side_effect=_populate_id_on_add)

        with (
            patch(
                "app.api.v1.orders.service.cache_delete_pattern",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.v1.orders.service.get_job_queue",
                new_callable=AsyncMock,
                return_value=AsyncMock(),
            ),
        ):
            service = OrderService(mock_session, repo, sample_user)
            await service.create_order_from_cart(
                sample_user.id, CreateOrderRequest(idempotency_key="deadlock-safe")
            )

        assert locked_order == [p_low.id, p_high.id]
        assert p_low.version == 2
        assert p_high.version == 2

    async def test_idempotent_replay_after_cart_lock_cleared_cart_returns_order(
        self, mock_session, sample_user
    ):
        empty_cart = _make_cart(sample_user.id, [])
        cart_result = MagicMock()
        cart_result.scalar_one_or_none.return_value = empty_cart
        mock_session.execute = AsyncMock(return_value=cart_result)

        existing_order = Order(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("25.00"),
            idempotency_key="after-lock-key",
            items=[],
        )
        repo = AsyncMock()
        repo.get_by_idempotency_key = AsyncMock(
            side_effect=[None, existing_order]
        )

        service = OrderService(mock_session, repo, sample_user)
        res = await service.create_order_from_cart(
            sample_user.id, CreateOrderRequest(idempotency_key="after-lock-key")
        )
        assert res.id == existing_order.id

