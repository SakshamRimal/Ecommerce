from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.core.storage import (
    ALLOWED_IMAGE_CONTENT_TYPES,
    LOCAL_FALLBACK_DIR,
    MAX_IMAGE_SIZE_BYTES,
    upload_image_to_minio,
)
from app.api.v1.products.repository import ProductRepository
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.products.service import ProductService
from app.api.v1.products.schema import (
    ProductCreateRequest,
    ProductImageUploadResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)

router = APIRouter(prefix="/products" , tags=["Products"])

def get_product_service(session:AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(ProductRepository(session) , CategoryRepository(session))


@router.post(
    "/upload-image",
    response_model=ProductImageUploadResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def upload_product_image(file: UploadFile = File(...)):
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ConflictError(
            "Unsupported image type. Upload JPEG, PNG, WEBP, GIF, or AVIF."
        )
    content = await file.read()
    if not content:
        raise ConflictError("Uploaded image file is empty")
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise ConflictError("Image file size exceeds the 10 MB limit")

    image_url, bucket, object_key = await upload_image_to_minio(
        filename=file.filename,
        content=content,
        content_type=content_type,
    )
    return ProductImageUploadResponse(
        image_url=image_url,
        bucket=bucket,
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(content),
    )


@router.get("/media/{object_key}")
async def get_uploaded_product_media(object_key: str):
    safe_name = Path(object_key).name
    target = LOCAL_FALLBACK_DIR / safe_name
    if not target.is_file():
        raise NotFoundError(f"Media '{safe_name}' not found")
    return FileResponse(target)


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