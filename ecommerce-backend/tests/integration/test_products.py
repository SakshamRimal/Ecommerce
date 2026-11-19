import uuid
from unittest.mock import AsyncMock
from httpx import AsyncClient
from app.main import app
from app.api.v1.products.service import ProductService
from app.api.v1.products.controller import get_product_service
from app.api.v1.products.schema import ProductResponse
from app.core.deps import get_current_user
from app.models.user import User, UserRole


def make_mock_product_service() -> AsyncMock:
    return AsyncMock(spec=ProductService)


class TestListProducts:
    async def test_list_returns_200(self, client: AsyncClient):
        mock_service = make_mock_product_service()
        mock_service.list_products = AsyncMock(return_value=[])
        app.dependency_overrides[get_product_service] = lambda: mock_service

        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        app.dependency_overrides.pop(get_product_service, None)

    async def test_list_returns_list(self, client: AsyncClient):
        mock_service = make_mock_product_service()
        mock_service.list_products = AsyncMock(return_value=[])
        app.dependency_overrides[get_product_service] = lambda: mock_service

        resp = await client.get("/api/v1/products?limit=10&offset=0")
        data = resp.json()
        assert isinstance(data, list)
        app.dependency_overrides.pop(get_product_service, None)


class TestGetProduct:
    async def test_get_nonexistent_returns_404(self, client: AsyncClient):
        from app.core.exceptions import NotFoundError

        mock_service = make_mock_product_service()
        mock_service.get_by_id = AsyncMock(
            side_effect=NotFoundError("Product not found")
        )
        app.dependency_overrides[get_product_service] = lambda: mock_service

        resp = await client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert resp.status_code == 404
        app.dependency_overrides.pop(get_product_service, None)

    async def test_get_invalid_uuid_returns_422(self, client: AsyncClient):
        resp = await client.get("/api/v1/products/not-a-uuid")
        assert resp.status_code == 422


class TestCreateProduct:
    async def test_create_requires_admin(self, client: AsyncClient):
        user = User(
            id=uuid.uuid4(),
            email="customer@example.com",
            hashed_password="x",
            full_name="Customer",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        app.dependency_overrides[get_current_user] = lambda: user

        resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Test Product",
                "description": "A test product",
                "price": 29.99,
                "stock_quantity": 10,
                "category_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 403
        app.dependency_overrides.pop(get_current_user, None)

    async def test_create_validation_error(self, client: AsyncClient):
        admin = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            hashed_password="x",
            full_name="Admin",
            is_active=True,
            role=UserRole.ADMIN,
        )
        app.dependency_overrides[get_current_user] = lambda: admin

        resp = await client.post(
            "/api/v1/products",
            json={"name": ""},
        )
        assert resp.status_code == 422
        app.dependency_overrides.pop(get_current_user, None)

    async def test_create_success_as_admin(self, client: AsyncClient):
        from app.api.v1.categories.schema import CategoryResponse

        admin = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            hashed_password="x",
            full_name="Admin",
            is_active=True,
            role=UserRole.ADMIN,
        )
        app.dependency_overrides[get_current_user] = lambda: admin

        mock_service = make_mock_product_service()
        product_data = ProductResponse(
            id=uuid.uuid4(),
            name="New Product",
            description="Desc",
            price=19.99,
            stock_quantity=5,
            category=CategoryResponse(
                id=uuid.uuid4(), name="Electronics", slug="electronics"
            ),
        )
        mock_service.create = AsyncMock(return_value=product_data)
        app.dependency_overrides[get_product_service] = lambda: mock_service

        resp = await client.post(
            "/api/v1/products",
            json={
                "name": "New Product",
                "description": "Desc",
                "price": 19.99,
                "stock_quantity": 5,
                "category_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 201
        app.dependency_overrides.pop(get_product_service, None)
        app.dependency_overrides.pop(get_current_user, None)


class TestDeleteProduct:
    async def test_delete_requires_admin(self, client: AsyncClient):
        user = User(
            id=uuid.uuid4(),
            email="customer@example.com",
            hashed_password="x",
            full_name="Customer",
            is_active=True,
            role=UserRole.CUSTOMER,
        )
        app.dependency_overrides[get_current_user] = lambda: user

        resp = await client.delete(f"/api/v1/products/{uuid.uuid4()}")
        assert resp.status_code == 403
        app.dependency_overrides.pop(get_current_user, None)
