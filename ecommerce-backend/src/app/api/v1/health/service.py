from app.api.v1.health.repository import HealthRepository
from app.api.v1.health.schema import HealthResponse


class HealthService:
    def __init__(self, repository: HealthRepository):
        self.repository = repository

    async def get_health(self) -> HealthResponse:
        try:
            db_ok = await self.repository.check_database_connection()
        except Exception:
            db_ok = False

        return HealthResponse(
            status="ok" if db_ok else "degraded",
            database="up" if db_ok else "down",
        )