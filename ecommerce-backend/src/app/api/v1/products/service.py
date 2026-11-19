import uuid
from app.api.v1.products.repository import ProductRepository
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.products.schema import (
    ProductCreateRequest, ProductUpdateRequest,
    ProductResponse, ProductListResponse,
)
from app.core.exceptions import NotFoundError
from app.core.cache import cache_get, cache_set, cache_delete_pattern
from app.core.job_queue import get_job_queue


class ProductService:
    def __init__(self, repository: ProductRepository, category_repository: CategoryRepository):
        self.repository = repository
        self.category_repository = category_repository

    async def create(self, data: ProductCreateRequest) -> ProductResponse:
        category = await self.category_repository.get_by_id(data.category_id)
        if not category:
            raise NotFoundError(f"Category with id '{data.category_id}' not found")

        product = await self.repository.create(
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            price=data.price,
            stock_quantity=data.stock_quantity,
            category_id=data.category_id,
        )

        # Invalidate cached listings — a new product means old cached pages are stale
        await cache_delete_pattern("product:list:*")
        
        # enqueue background indexing - API response immediately , doesnt wait for ES 
        queue = await get_job_queue()
        await queue.enqueue_job("index_product_task", str(product.id))
        await queue.enqueue_job("generate_product_embedding_task", str(product.id))

        return ProductResponse.model_validate(product)

    async def list_products(
        self, limit: int, offset: int, category_id: uuid.UUID | None
    ) -> list[ProductListResponse]:
        cache_key = f"product:list:v2:{limit}:{offset}:{category_id}"

        cached = await cache_get(cache_key)
        if cached is not None:
            return [ProductListResponse.model_validate(product) for product in cached]

        products = await self.repository.list_products(
            limit=limit, offset=offset, category_id=category_id
        )
        response = [ProductListResponse.model_validate(product) for product in products]

        # Populate the cache with the JSON-safe form so the NEXT request is a hit
        await cache_set(cache_key, [item.model_dump(mode="json") for item in response])

        return response

    async def get_by_id(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")
        return ProductResponse.model_validate(product)

    async def update(self, product_id: uuid.UUID, data: ProductUpdateRequest) -> ProductResponse:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")

        if data.category_id is not None:
            category = await self.category_repository.get_by_id(data.category_id)
            if not category:
                raise NotFoundError(f"Category with id '{data.category_id}' not found")

        updated = await self.repository.update(
            product,
            expected_version=product.version,
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            price=data.price,
            stock_quantity=data.stock_quantity,
            category_id=data.category_id,
        )

        # This product's data changed — invalidate list caches so stale prices/names don't linger
        await cache_delete_pattern("product:list:*")

        # Keep the search index and semantic vector in sync with the catalog.
        queue = await get_job_queue()
        await queue.enqueue_job("index_product_task", str(updated.id))
        await queue.enqueue_job("generate_product_embedding_task", str(updated.id))

        return ProductResponse.model_validate(updated)

    async def delete(self, product_id: uuid.UUID) -> None:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")

        await self.repository.delete(product)

        # Deleted product must not keep showing up in cached listings
        await cache_delete_pattern("product:list:*")

        # Remove from Elasticsearch index
        queue = await get_job_queue()
        await queue.enqueue_job("delete_product_from_index_task", str(product.id))