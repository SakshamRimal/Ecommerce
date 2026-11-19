import uuid 
from decimal import Decimal 
from pydantic import BaseModel , Field , field_validator 

from app.api.v1.categories.schema import CategoryResponse

class ProductCreateRequest(BaseModel):
    name: str = Field(... , min_length=1 , max_length=255)
    description: str | None = Field(default=None , max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(ge=0, decimal_places=2)
    stock_quantity: int = Field(ge=0 , default = 0)
    category_id: uuid.UUID 
    
    @field_validator("name")
    @classmethod 
    def strip_name(cls , v: str) -> str:
        return v.strip()
    
class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v
    
class ProductResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: uuid.UUID
    name: str 
    description: str | None
    image_url: str | None = None
    price: Decimal
    stock_quantity: int
    category: CategoryResponse
    
class ProductListResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: uuid.UUID
    name: str
    description: str | None = None
    image_url: str | None = None
    price: Decimal
    stock_quantity: int
    category: CategoryResponse


class ProductImageUploadResponse(BaseModel):
    image_url: str
    bucket: str
    object_key: str
    content_type: str
    size_bytes: int
    

    
    