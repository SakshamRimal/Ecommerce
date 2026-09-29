import pytest
from unittest.mock import AsyncMock
from app.api.v1.health.service import HealthService
from app.api.v1.health.repository import HealthCheckRepository


class TestHealthService:
    async def test_healthy_when_db_up(self, mock_health_repository):
        service = HealthService(mock_health_repository)
        result = await service.get_health()
        assert result.status == "ok"
        assert result.database == "up"

    async def test_degraded_when_db_down(self):
        repo = AsyncMock()
        repo.check_database = AsyncMock(return_value=False)
        service = HealthService(repo)
        result = await service.get_health()
        assert result.status == "degraded"
        assert result.database == "down"

    async def test_degraded_when_db_raises_exception(self):
        repo = AsyncMock()
        repo.check_database = AsyncMock(side_effect=ConnectionError("db down"))
        service = HealthService(repo)
        result = await service.get_health()
        assert result.status == "degraded"
        assert result.database == "down"

    async def test_repository_check_database_returns_bool(self):
        repo = AsyncMock(spec=HealthCheckRepository)
        repo.check_database = AsyncMock(return_value=True)
        service = HealthService(repo)
        result = await service.get_health()
        assert isinstance(result.database, str)
