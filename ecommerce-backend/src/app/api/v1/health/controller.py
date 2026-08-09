from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.api.v1.health.repository import HealthRepository
from app.api.v1.health.service import HealthService
from app.api.v1.health.schema import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


def get_health_service(session: AsyncSession = Depends(get_db_session)) -> HealthService:
    repository = HealthRepository(session)
    return HealthService(repository)


@router.get("", response_model=HealthResponse)
async def health_check(service: HealthService = Depends(get_health_service)):
    return await service.get_health()