from fastapi import APIRouter, Query
from app.api.v1.search.service import SearchService
from app.api.v1.search.schema import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/products", response_model=SearchResponse)
async def search_products(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, le=50, ge=1),
):
    service = SearchService()
    return await service.search_products(query=q, limit=limit)