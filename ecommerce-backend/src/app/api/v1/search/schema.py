import uuid 
from decimal import Decimal
from pydantic import BaseModel 

class ProductSearchResult(BaseModel):
    id: uuid.UUID
    name: str 
    description: str | None = None
    category_name: str 
    price: Decimal
    stock_quantity: int
    score: float # Relevance score from Elasticsearch
    
class SearchResponse(BaseModel):
    query: str 
    total: int 
    results : list[ProductSearchResult]