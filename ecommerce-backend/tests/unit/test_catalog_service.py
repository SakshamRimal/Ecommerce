from decimal import Decimal
import uuid
from unittest.mock import AsyncMock, patch
import pytest

from app.api.v1.categories.schema import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    slugify,
)
from app.api.v1.categories.service import CategoryService
from app.api.v1.products.schema import ProductCreateRequest, ProductUpdateRequest
from app.api.v1.products.service import ProductService
from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.product import Product


def _sample_category(name: str = "Footwear", slug: str = "footwear") -> Category:
    return Category(id=uuid.uuid4(), name=name, slug=slug)


def _sample_product(category: Category | None = None) -> Product:
    cat = category or _sample_category()
    return Product(
        id=uuid.uuid4(),
        name="Trail Runner",
        description="Lightweight trail shoe",
        image_url="https://example.com/shoe.jpg",
        price=Decimal("89.90"),
        stock_quantity=12,
        category_id=cat.id,
        category=cat,
        version=1,
    )


class TestCategoryService:
    async def test_slugify(self):
        assert slugify("  Men's Running & Trail! ") == "men-s-running-trail"

    async def test_create_category_success(self):
        repo = AsyncMock()
        cat = _sample_category()
        repo.get_by_slug = AsyncMock(return_value=None)
        repo.create = AsyncMock(return_value=cat)

        service = CategoryService(repo)
        res = await service.create(CategoryCreateRequest(name="Footwear"))
        assert res.slug == "footwear"
        repo.create.assert_awaited_once_with(name="Footwear", slug="footwear")

    async def test_create_category_duplicate_slug_raises(self):
        repo = AsyncMock()
        repo.get_by_slug = AsyncMock(return_value=_sample_category())

        service = CategoryService(repo)
        with pytest.raises(ConflictError):
            await service.create(CategoryCreateRequest(name="Footwear"))

    async def test_update_category_regenerates_slug(self):
        repo = AsyncMock()
        cat = _sample_category()
        updated_cat = _sample_category(name="Trail Shoes", slug="trail-shoes")
        updated_cat.id = cat.id
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.get_by_slug = AsyncMock(return_value=None)
        repo.update = AsyncMock(return_value=updated_cat)

        service = CategoryService(repo)
        res = await service.update(
            cat.id, CategoryUpdateRequest(name="Trail Shoes")
        )
        assert res.name == "Trail Shoes"
        assert res.slug == "trail-shoes"
        repo.update.assert_awaited_once_with(
            cat, name="Trail Shoes", slug="trail-shoes"
        )

    async def test_update_category_conflict_with_other(self):
        repo = AsyncMock()
        cat = _sample_category()
        other = _sample_category(name="Shoes", slug="shoes")
        repo.get_by_id = AsyncMock(return_value=cat)
        repo.get_by_slug = AsyncMock(return_value=other)

        service = CategoryService(repo)
        with pytest.raises(ConflictError):
            await service.update(cat.id, CategoryUpdateRequest(name="Shoes"))

    async def test_get_and_delete_not_found(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        service = CategoryService(repo)

        with pytest.raises(NotFoundError):
            await service.get_by_id(uuid.uuid4())

        with pytest.raises(NotFoundError):
            await service.delete(uuid.uuid4())


class TestProductService:
    async def test_create_invalidates_cache_and_enqueues_jobs(self):
        product_repo = AsyncMock()
        category_repo = AsyncMock()
        cat = _sample_category()
        prod = _sample_product(cat)
        category_repo.get_by_id = AsyncMock(return_value=cat)
        product_repo.create = AsyncMock(return_value=prod)
        mock_queue = AsyncMock()

        with (
            patch(
                "app.api.v1.products.service.cache_delete_pattern",
                new_callable=AsyncMock,
            ) as mock_cache_del,
            patch(
                "app.api.v1.products.service.get_job_queue",
                new_callable=AsyncMock,
                return_value=mock_queue,
            ),
        ):
            service = ProductService(product_repo, category_repo)
            res = await service.create(
                ProductCreateRequest(
                    name="Trail Runner",
                    description="Lightweight trail shoe",
                    image_url="https://example.com/shoe.jpg",
                    price=Decimal("89.90"),
                    stock_quantity=12,
                    category_id=cat.id,
                )
            )

        assert res.id == prod.id
        assert res.image_url == "https://example.com/shoe.jpg"
        mock_cache_del.assert_awaited_once_with("product:list:*")
        assert mock_queue.enqueue_job.await_count == 2

    async def test_update_invalidates_cache_and_reindexes(self):
        product_repo = AsyncMock()
        category_repo = AsyncMock()
        cat = _sample_category()
        prod = _sample_product(cat)
        product_repo.get_by_id = AsyncMock(return_value=prod)
        product_repo.update = AsyncMock(return_value=prod)
        mock_queue = AsyncMock()

        with (
            patch(
                "app.api.v1.products.service.cache_delete_pattern",
                new_callable=AsyncMock,
            ) as mock_cache_del,
            patch(
                "app.api.v1.products.service.get_job_queue",
                new_callable=AsyncMock,
                return_value=mock_queue,
            ),
        ):
            service = ProductService(product_repo, category_repo)
            res = await service.update(
                prod.id, ProductUpdateRequest(name="Trail Runner v2")
            )

        assert res.id == prod.id
        mock_cache_del.assert_awaited_once_with("product:list:*")
        mock_queue.enqueue_job.assert_any_await("index_product_task", str(prod.id))
        mock_queue.enqueue_job.assert_any_await(
            "generate_product_embedding_task", str(prod.id)
        )

    async def test_list_products_uses_cache_when_available(self):
        product_repo = AsyncMock()
        category_repo = AsyncMock()
        cat = _sample_category()
        prod = _sample_product(cat)
        cached_payload = [
            {
                "id": str(prod.id),
                "name": prod.name,
                "description": prod.description,
                "image_url": prod.image_url,
                "price": "89.90",
                "stock_quantity": 12,
                "category": {
                    "id": str(cat.id),
                    "name": cat.name,
                    "slug": cat.slug,
                },
            }
        ]

        with patch(
            "app.api.v1.products.service.cache_get",
            new_callable=AsyncMock,
            return_value=cached_payload,
        ):
            service = ProductService(product_repo, category_repo)
            items = await service.list_products(limit=20, offset=0, category_id=None)

        assert len(items) == 1
        assert items[0].name == "Trail Runner"
        product_repo.list_products.assert_not_awaited()

