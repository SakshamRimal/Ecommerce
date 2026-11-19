import uuid 
from app.api.v1.categories.repository import CategoryRepository
from app.api.v1.categories.schema import (
    CategoryCreateRequest , CategoryUpdateRequest , 
    CategoryResponse , slugify
)
from app.core.exceptions import NotFoundError , ConflictError 

class CategoryService:
    def __init__(self , repository: CategoryRepository):
        self.repository = repository
        
    async def create(self , data: CategoryCreateRequest) -> CategoryResponse:
        slug = slugify(data.name)
        existing = await self.repository.get_by_slug(slug)
        if existing:
            raise ConflictError(f"Category with slug '{slug}' already exists")
        
        category = await self.repository.create(name=data.name , slug=slug)
        return CategoryResponse.model_validate(category)
    
    async def list_all(self , limit: int = 50 , offset: int = 0) -> list[CategoryResponse]:
        categories = await self.repository.list_all(limit=limit , offset=offset)
        return [CategoryResponse.model_validate(category) for category in categories]
    
    async def get_by_id(self , category_id: uuid.UUID) -> CategoryResponse:
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id '{category_id}' not found")
        return CategoryResponse.model_validate(category)
    
    async def update(self , category_id: uuid.UUID , data: CategoryUpdateRequest) -> CategoryResponse:
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id '{category_id}' not found")
        
        if data.name is None:
            return CategoryResponse.model_validate(category)

        new_slug = slugify(data.name)
        existing = await self.repository.get_by_slug(new_slug)
        if existing and existing.id != category_id:
            raise ConflictError(f"Category with slug '{new_slug}' already exists")

        updated = await self.repository.update(
            category, name=data.name, slug=new_slug
        )
        return CategoryResponse.model_validate(updated)
    
    async def delete(self , category_id: uuid.UUID) -> None:
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category with id '{category_id}' not found")
        
        await self.repository.delete(category)
    
        
        