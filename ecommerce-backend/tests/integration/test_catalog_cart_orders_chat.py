from decimal import Decimal
import datetime as dt
import uuid
from unittest.mock import AsyncMock
from httpx import AsyncClient

from app.main import app
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.order import OrderStatus
from app.models.chat import MessageRole
from app.api.v1.categories.controller import get_category_service
from app.api.v1.categories.schema import CategoryResponse
from app.api.v1.cart.controller import get_cart_service
from app.api.v1.cart.schema import CartResponse, CartItemResponse
from app.api.v1.orders.controller import get_order_service
from app.api.v1.orders.schema import OrderResponse, OrderItemResponse
from app.api.v1.search.controller import get_search_service
from app.api.v1.search.schema import SearchResponse
from app.api.v1.products.schema import ProductListResponse
from app.api.v1.chat.controller import get_chat_service
from app.api.v1.chat.schema import ChatMessageResponse


def _customer() -> User:
    return User(
        id=uuid.uuid4(),
        email="shopper@example.com",
        hashed_password="x",
        full_name="Shopper",
        is_active=True,
        role=UserRole.CUSTOMER,
    )


class TestCategoryEndpoints:
    async def test_get_category_detail_is_public(self, client: AsyncClient):
        cat_id = uuid.uuid4()
        mock_service = AsyncMock()
        mock_service.get_by_id = AsyncMock(
            return_value=CategoryResponse(
                id=cat_id, name="Footwear", slug="footwear"
            )
        )
        app.dependency_overrides[get_category_service] = lambda: mock_service
        try:
            resp = await client.get(f"/api/v1/categories/{cat_id}")
            assert resp.status_code == 200
            assert resp.json()["slug"] == "footwear"
        finally:
            app.dependency_overrides.pop(get_category_service, None)


class TestCartEndpoints:
    async def test_patch_cart_item_requires_only_quantity(self, client: AsyncClient):
        user = _customer()
        pid = uuid.uuid4()
        cart_resp = CartResponse(
            id=uuid.uuid4(),
            items=[
                CartItemResponse(
                    id=uuid.uuid4(),
                    product_id=pid,
                    product_name="Shoe",
                    unit_price=Decimal("50.00"),
                    quantity=3,
                    subtotal=Decimal("150.00"),
                )
            ],
            total=Decimal("150.00"),
        )
        mock_service = AsyncMock()
        mock_service.update_item_quantity = AsyncMock(return_value=cart_resp)
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_cart_service] = lambda: mock_service
        try:
            resp = await client.patch(
                f"/api/v1/cart/items/{pid}",
                json={"quantity": 3},
            )
            assert resp.status_code == 200
            assert resp.json()["total"] == "150.00"
            mock_service.update_item_quantity.assert_awaited_once_with(
                user.id, pid, 3
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_cart_service, None)


class TestOrderEndpoints:
    async def test_list_get_and_cancel_order(self, client: AsyncClient):
        user = _customer()
        oid = uuid.uuid4()
        pid = uuid.uuid4()
        order_resp = OrderResponse(
            id=oid,
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("89.90"),
            items=[
                OrderItemResponse(
                    product_id=pid,
                    product_name="Trail Shoe",
                    unit_price=Decimal("89.90"),
                    quantity=1,
                )
            ],
        )
        canceled_resp = OrderResponse(
            id=oid,
            status=OrderStatus.CANCELED,
            total_amount=Decimal("89.90"),
            items=order_resp.items,
        )

        mock_service = AsyncMock()
        mock_service.current_user = user
        mock_service.list_orders = AsyncMock(return_value=[order_resp])
        mock_service.get_order = AsyncMock(return_value=order_resp)
        mock_service.cancel_order = AsyncMock(return_value=canceled_resp)

        app.dependency_overrides[get_order_service] = lambda: mock_service
        try:
            list_res = await client.get("/api/v1/orders")
            assert list_res.status_code == 200
            assert len(list_res.json()) == 1

            detail_res = await client.get(f"/api/v1/orders/{oid}")
            assert detail_res.status_code == 200
            assert detail_res.json()["id"] == str(oid)

            cancel_res = await client.post(f"/api/v1/orders/{oid}/cancel")
            assert cancel_res.status_code == 200
            assert cancel_res.json()["status"] == "canceled"
        finally:
            app.dependency_overrides.pop(get_order_service, None)


class TestSearchAndChatEndpoints:
    async def test_search_with_filters_and_semantic_search(self, client: AsyncClient):
        cat = CategoryResponse(id=uuid.uuid4(), name="Gear", slug="gear")
        prod = ProductListResponse(
            id=uuid.uuid4(),
            name="Backpack",
            description="Waterproof pack",
            image_url=None,
            price=Decimal("75.00"),
            stock_quantity=8,
            category=cat,
        )
        mock_service = AsyncMock()
        mock_service.search_products = AsyncMock(
            return_value=SearchResponse(
                query="pack", total=1, results=[], limit=10, offset=0
            )
        )
        mock_service.semantic_search_products = AsyncMock(return_value=[prod])
        app.dependency_overrides[get_search_service] = lambda: mock_service
        try:
            r1 = await client.get(
                f"/api/v1/search/products?q=pack&min_price=20&max_price=100&category_id={cat.id}"
            )
            assert r1.status_code == 200

            r2 = await client.get(
                "/api/v1/search/products/semantic?q=hiking+in+the+rain"
            )
            assert r2.status_code == 200
            assert r2.json()[0]["name"] == "Backpack"
        finally:
            app.dependency_overrides.pop(get_search_service, None)

    async def test_chat_and_history_endpoints(self, client: AsyncClient):
        user = _customer()
        mock_service = AsyncMock()
        mock_service.send_message_for_user = AsyncMock(
            return_value="Try the Trail Runner!"
        )
        mock_service.get_history = AsyncMock(
            return_value=[
                ChatMessageResponse(
                    id=uuid.uuid4(),
                    role=MessageRole.USER,
                    content="Need running shoes",
                    created_at=dt.datetime.now(dt.timezone.utc),
                )
            ]
        )
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_chat_service] = lambda: mock_service
        try:
            chat_res = await client.post(
                "/api/v1/chat", json={"message": "Need running shoes"}
            )
            assert chat_res.status_code == 200
            assert chat_res.json()["reply"] == "Try the Trail Runner!"

            hist_res = await client.get("/api/v1/chat/history")
            assert hist_res.status_code == 200
            assert len(hist_res.json()["messages"]) == 1
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_chat_service, None)

