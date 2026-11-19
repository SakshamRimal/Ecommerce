import uuid 
from fastapi import APIRouter , Depends , Query 
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session 
from app.core.deps import require_admin 
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.categories.service import CategoryService
from app.api.v1.categories.schema import(
    CategoryCreateRequest , CategoryUpdateRequest , 
    CategoryResponse
)

router = APIRouter(prefix="/categories" , tags=["Categories"])

def get_category_service(session: AsyncSession = Depends(get_db_session)) -> CategoryService:
    return CategoryService(repository=CategoryRepository(session=session))

@router.post("", response_model=CategoryResponse , status_code=201 , dependencies=[Depends(require_admin)])
async def create_category(
    data: CategoryCreateRequest, 
    service: CategoryService = Depends(get_category_service)
):
    return await service.create(data=data)

@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    limit: int = Query(default=50 , ge=1 , le=100) ,
    offset: int = Query(default=0 , ge=0) ,
    service: CategoryService = Depends(get_category_service)
):
    return await service.list_all(limit=limit , offset=offset)

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID , 
    service: CategoryService = Depends(get_category_service)
):
    return await service.get_by_id(category_id=category_id)

@router.patch("/{category_id}", response_model = CategoryResponse , dependencies=[Depends(require_admin)])
async def update_category(
    category_id: uuid.UUID , 
    data: CategoryUpdateRequest , 
    service: CategoryService = Depends(get_category_service)
):
    return await service.update(category_id=category_id , data=data)

@router.delete("/{category_id}" , status_code=204 , dependencies=[Depends(require_admin)])
async def delete_category(
    category_id: uuid.UUID , 
    service: CategoryService = Depends(get_category_service)
):
    await service.delete(category_id=category_id)
    return None
