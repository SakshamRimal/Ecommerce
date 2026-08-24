from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.api.v1.health.service import HealthService
from app.api.v1.health.repository import HealthCheckRepository
from app.api.v1.health.schema import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health Check"])

def get_health_service(session: AsyncSession = Depends(get_db_session)) -> HealthService:
    """Dependency that provides a HealthService instance."""
    repository = HealthCheckRepository(session)
    return HealthService(repository)

@router.get("",response_model=HealthCheckResponse)
async def health_check(service: HealthService = Depends(get_health_service)):
    """Endpoint to check the health of the application."""
    return await service.get_health()

"""
Notice: the controller never touches SQL or business rules — it just wires dependencies and delegates. This is FastAPI's dependency injection doing the CSR wiring for you.
"""
