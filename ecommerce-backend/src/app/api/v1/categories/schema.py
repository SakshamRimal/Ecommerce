import uuid 
import re 
from pydantic import BaseModel, Field, field_validator , ConfigDict 

class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2 , max_length=100)
    
    @field_validator("name")
    @classmethod 
    def name_must_be_clean(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty or whitespace")
        return v 
    
class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def name_must_be_clean(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Name must not be empty or whitespace")
        return v
    
class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID 
    name: str 
    slug: str 
    
    
def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug
    
        
    
