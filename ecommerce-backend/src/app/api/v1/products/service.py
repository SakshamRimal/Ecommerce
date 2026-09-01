import uuid 
from app.api.v1.products.repository import ProductRepository
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.products.schema import (
    ProductCreateRequest , ProductUpdateRequest ,
    ProductResponse , ProductListResponse,)
from app.core.exceptions import NotFoundError

class ProductService:
    def __init__(self , repository: ProductRepository , category_repository: CategoryRepository):
        self.repository = repository
        self.category_repository = category_repository
        
    async def create(self , data: ProductCreateRequest) -> ProductResponse:
        category = await self.category_repository.get_by_id(data.category_id)
        if not category:
            raise NotFoundError(f"Category with id '{data.category_id}' not found")
        
        product = await self.repository.create(
            name=data.name , 
            description=data.description , 
            price=data.price , 
            stock_quantity=data.stock_quantity , 
            category=category
        )
        return ProductResponse.model_validate(product)
    
    async def list_products(
        self , limit: int , offset: int , category_id: uuid.UUID | None 
    ) -> list[ProductListResponse]:
        products = await self.repository.list_products(
            limit=limit , offset=offset , category_id=category_id
        )
        return [ProductListResponse.model_validate(product) for product in products]
    
    async def get_by_id(self , product_id: uuid.UUID) -> ProductResponse:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")
        return ProductResponse.model_validate(product)
    
    async def update(self, product_id: uuid.UUID , data: ProductUpdateRequest) -> ProductResponse:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")
        
        if data.category_id is not None:
            category = await self.category_repository.get_by_id(data.category_id)
            if not category:
                raise NotFoundError(f"Category with id '{data.category_id}' not found")
            
        updated = await self.repository.update(
            product , 
            name=data.name , 
            description=data.description , 
            price=data.price , 
            stock_quantity=data.stock_quantity , 
            category_id=data.category_id
        )
        return ProductResponse.model_validate(updated)
    
    async def delete(self , product_id: uuid.UUID) -> None:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with id '{product_id}' not found")
        
        await self.repository.delete(product)