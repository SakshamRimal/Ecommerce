import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

    async def test_health_returns_expected_fields(self, client: AsyncClient):
        resp = await client.get("/api/v1/health")
        data = resp.json()
        assert "status" in data
        assert "database" in data
        assert data["status"] in ("ok", "degraded")
        assert data["database"] in ("up", "down")

    async def test_health_is_get_only(self, client: AsyncClient):
        resp = await client.post("/api/v1/health")
        assert resp.status_code == 405
