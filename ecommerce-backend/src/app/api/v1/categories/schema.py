import uuid 
import re 
from pydantic import BaseModel , Field , ConfigDict , field_validator , EmailStr , constr


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2 . max_)