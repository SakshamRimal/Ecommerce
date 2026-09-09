import uuid 
from fastapi import APIRouter , Depends , Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import require_admin
from app.api.v1.products.repository import ProductRepository
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.products.service import ProductService
from app.api.v1.products.schema import (
    ProductCreateRequest , ProductUpdateRequest ,
    ProductResponse , ProductListResponse
)

router = APIRouter(prefix="/products" , tags=["Products"])

def get_product_service(session:AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(ProductRepository(session) , CategoryRepository(session))


@router.post("",response_model=ProductResponse , status_code=201 , dependencies=[Depends(require_admin)])
async def create_product(
    data: ProductCreateRequest,
    service: ProductService = Depends(get_product_service),
):
    return await service.create(data)

@router.get("" ,response_model=list[ProductListResponse])
async def list_products(
    limit: int = Query(default=20 , le=100 , ge=1),
    offset: int = Query(default=0 , ge=0),
    category_id: uuid.UUID | None = Query(default = None),
    service: ProductService = Depends(get_product_service)
):
    return await service.list_products(limit=limit ,offset=offset , category_id=category_id)

@router.get("/{product_id}" , response_model = ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
):
    return await service.get_by_id(product_id)

@router.patch("/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_admin)])
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdateRequest,
    service: ProductService = Depends(get_product_service),
):
    return await service.update(product_id , data)

@router.delete("/{product_id}" , status_code=204 , dependencies=[Depends(require_admin)])
async def delete_product(
    product_id: uuid.UUID , 
    service: ProductService = Depends(get_product_service),
):
    await service.delete(product_id)