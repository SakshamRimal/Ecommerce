import uuid
from decimal import Decimal

import structlog

from app.core.elasticsearch import get_es_client
from app.core.config import get_settings
from app.api.v1.search.schema import SearchResponse, ProductSearchResult
from app.ai.embeddings import generate_embedding
from app.api.v1.products.repository import ProductRepository
from app.api.v1.products.schema import ProductListResponse

settings = get_settings()
logger = structlog.get_logger("search_service")


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


class SearchService:

    def __init__(self, product_repository: ProductRepository | None = None):
        self.product_repository = product_repository

    async def search_products(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> SearchResponse:
        min_price = _to_decimal(min_price)
        max_price = _to_decimal(max_price)

        filters = []
        if min_price is not None:
            filters.append({"range": {"price": {"gte": float(min_price)}}})
        if max_price is not None:
            filters.append({"range": {"price": {"lte": float(max_price)}}})
        if category_id is not None:
            filters.append({"term": {"category_id": str(category_id)}})

        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "description"],
                                "fuzziness": "AUTO",
                            }
                        }
                    ],
                    "filter": filters,
                }
            },
            "from": offset,
            "size": limit,
        }

        try:
            es_client = get_es_client()
            response = await es_client.search(
                index=settings.elasticsearch_products_index, body=body
            )
        except Exception as exc:  # noqa: BLE001 - degrade instead of 500
            logger.warning("elasticsearch_search_failed", error=str(exc))
            return await self._fallback_search(
                query=query,
                limit=limit,
                offset=offset,
                min_price=min_price,
                max_price=max_price,
                category_id=category_id,
            )

        hits = response["hits"]["hits"]
        results = [
            ProductSearchResult(
                id=hit["_source"]["id"],
                name=hit["_source"]["name"],
                description=hit["_source"].get("description"),
                category_name=hit["_source"].get("category_name", ""),
                price=hit["_source"]["price"],
                stock_quantity=hit["_source"]["stock_quantity"],
                score=hit["_score"],
            )
            for hit in hits
        ]

        return SearchResponse(
            query=query,
            total=response["hits"]["total"]["value"],
            results=results,
            limit=limit,
            offset=offset,
        )

    async def _fallback_search(
        self,
        query: str,
        limit: int,
        offset: int,
        min_price: Decimal | None,
        max_price: Decimal | None,
        category_id: uuid.UUID | None,
    ) -> SearchResponse:
        """PostgreSQL keyword fallback when Elasticsearch is unavailable."""
        if self.product_repository is None:
            return SearchResponse(
                query=query, total=0, results=[], limit=limit, offset=offset
            )

        products = await self.product_repository.search_by_keyword(
            query=query,
            limit=limit,
            offset=offset,
            min_price=min_price,
            max_price=max_price,
            category_id=category_id,
        )
        results = [
            ProductSearchResult(
                id=product.id,
                name=product.name,
                description=product.description,
                category_name=product.category.name if product.category else "",
                price=product.price,
                stock_quantity=product.stock_quantity,
                score=0.0,
            )
            for product in products
        ]
        return SearchResponse(
            query=query,
            total=len(results),
            results=results,
            limit=limit,
            offset=offset,
        )

    async def semantic_search_products(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        min_price=None,
        max_price=None,
        category_id: uuid.UUID | None = None,
    ) -> list[ProductListResponse]:
        if self.product_repository is None:
            raise RuntimeError(
                "Semantic search requires a ProductRepository and a database session"
            )

        min_dec = _to_decimal(min_price)
        max_dec = _to_decimal(max_price)
        try:
            query_embedding = await generate_embedding(query)
            products = await self.product_repository.semantic_search(
                embedding=query_embedding,
                limit=limit,
                offset=offset,
                min_price=min_dec,
                max_price=max_dec,
                category_id=category_id,
            )
        except Exception as exc:  # noqa: BLE001 - degrade when pgvector/OpenAI unavailable
            logger.warning("semantic_search_fallback_to_keyword", error=str(exc))
            products = await self.product_repository.search_by_keyword(
                query=query,
                limit=limit,
                offset=offset,
                min_price=min_dec,
                max_price=max_dec,
                category_id=category_id,
            )
        return [ProductListResponse.model_validate(product) for product in products]
