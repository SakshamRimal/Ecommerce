from app.api.v1.health.schema import HealthRepository
from app.api.v1.health.schema import HealthCheckResponse

class HealthService:
    def __init__(self , repository:HealthRepository):
        self.repository = repository
        
    async def get_health(self) -> HealthCheckResponse:
        
        try:
            db_ok = await self.repository.check_database()
        except Exception as e:
            db_ok = False
            
        return HealthCheckResponse(
            status="ok" if db_ok else "degraded",
            database="up" if db_ok else "down",
        )
        
    
        