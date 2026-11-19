import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.search.service import SearchService
from app.api.v1.search.schema import SearchResponse
from app.api.v1.products.repository import ProductRepository
from app.api.v1.products.schema import ProductListResponse
from app.db.session import get_db_session

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(
    session: AsyncSession = Depends(get_db_session),
) -> SearchService:
    return SearchService(ProductRepository(session))


@router.get("/products", response_model=SearchResponse)
async def search_products(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    category_id: uuid.UUID | None = Query(default=None),
    service: SearchService = Depends(get_search_service),
):
    """Keyword/product search backed by Elasticsearch (PostgreSQL fallback)."""
    return await service.search_products(
        query=q,
        limit=limit,
        offset=offset,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
    )


@router.get("/products/semantic", response_model=list[ProductListResponse])
async def semantic_search_products(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=10, le=50, ge=1),
    offset: int = Query(default=0, ge=0),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    category_id: uuid.UUID | None = Query(default=None),
    service: SearchService = Depends(get_search_service),
):
    """Meaning-based product search backed by pgvector embeddings."""
    return await service.semantic_search_products(
        query=q,
        limit=limit,
        offset=offset,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
    )
