from app.core.elasticsearch import get_es_client
from app.core.config import get_settings
from app.api.v1.search.schema import SearchResponse, ProductSearchResult
from app.ai.embeddings import generate_embedding
from app.api.v1.products.repository import ProductRepository
from app.api.v1.products.schema import ProductListResponse

settings = get_settings()


class SearchService:
    
    def __init__(self , product_repository: ProductRepository | None = None):
        self.product_repository = product_repository
        
    async def search_products(self, query: str, limit: int = 20) -> SearchResponse:
        es_client = get_es_client()

        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description"],  # name matches weighted 3x higher
                    "fuzziness": "AUTO",                    # typo tolerance
                }
            },
            "size": limit,
        }

        response = await es_client.search(
            index=settings.elasticsearch_products_index, body=body
        )

        hits = response["hits"]["hits"]
        results = [
            ProductSearchResult(
                id=hit["_source"]["id"],
                name=hit["_source"]["name"],
                description=hit["_source"]["description"],
                category_name=hit["_source"]["category_name"],
                price=hit["_source"]["price"],
                stock_quantity=hit["_source"]["stock_quantity"],
                score=hit["_score"],
            )
            for hit in hits
        ]

        return SearchResponse(
            query=query, total=response["hits"]["total"]["value"], results=results
        )
    
    async def semantic_search_products(self , query: str , limit: int = 10) -> list[ProductListResponse]:
        query_embedding = await generate_embedding(query)
        products = await self.product_repository.semantic_search(embedding=query_embedding , limit=limit)
        return [ProductListResponse.model_validate(product) for product in products]