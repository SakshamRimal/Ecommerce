import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app


class TestRouteRegistration:
    """Verify all expected routes are registered and responding."""

    async def test_openapi_schema_available(self, client: AsyncClient):
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200

    async def test_docs_available(self, client: AsyncClient):
        resp = await client.get("/docs")
        assert resp.status_code == 200

    async def test_health_route_exists(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code != 404

    async def test_auth_register_route_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code != 404

    async def test_auth_login_route_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={})
        assert resp.status_code != 404

    async def test_auth_refresh_route_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code != 404

    async def test_auth_me_route_exists(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    async def test_product_list_route_exists(self, client: AsyncClient):
        mock_service = AsyncMock()
        mock_service.list_products = AsyncMock(return_value=[])
        from app.api.v1.products.controller import get_product_service
        app.dependency_overrides[get_product_service] = lambda: mock_service

        resp = await client.get("/api/v1/products")
        assert resp.status_code == 200
        app.dependency_overrides.pop(get_product_service, None)

    async def test_product_create_route_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/products", json={})
        assert resp.status_code != 404

    async def test_category_list_route_exists(self, client: AsyncClient):
        from app.api.v1.categories.controller import get_category_service
        from app.api.v1.categories.service import CategoryService
        mock_service = AsyncMock(spec=CategoryService)
        mock_service.list_all = AsyncMock(return_value=[])
        app.dependency_overrides[get_category_service] = lambda: mock_service

        resp = await client.get("/api/v1/categories")
        assert resp.status_code == 200
        app.dependency_overrides.pop(get_category_service, None)

    async def test_cart_route_exists(self, client: AsyncClient):
        resp = await client.get("/api/v1/cart")
        assert resp.status_code in (401, 403, 200)

    async def test_order_route_exists(self, client: AsyncClient):
        resp = await client.post("/api/v1/orders", json={})
        assert resp.status_code != 404

    async def test_search_route_exists(self, client: AsyncClient):
        from app.api.v1.search.service import SearchService
        from app.api.v1.search.schema import SearchResponse
        mock_service = AsyncMock()
        mock_service.search_products = AsyncMock(
            return_value=SearchResponse(query="test", total=0, results=[])
        )
        with patch.object(SearchService, "search_products", mock_service.search_products):
            resp = await client.get("/api/v1/search/products?q=test")
        assert resp.status_code == 200

    async def test_unknown_route_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/nonexistent")
        assert resp.status_code == 404

    async def test_all_routes_in_openapi(self, client: AsyncClient):
        resp = await client.get("/openapi.json")
        paths = resp.json()["paths"]
        expected = [
            "/api/v1/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/me",
            "/api/v1/products",
            "/api/v1/products/{product_id}",
            "/api/v1/categories",
            "/api/v1/categories/{category_id}",
            "/api/v1/cart",
            "/api/v1/cart/items",
            "/api/v1/cart/items/{product_id}",
            "/api/v1/orders",
            "/api/v1/search/products",
        ]
        for path in expected:
            assert path in paths, f"Missing route: {path}"
