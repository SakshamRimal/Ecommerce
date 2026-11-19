import uuid 
from decimal import Decimal 
from pydantic import BaseModel , ConfigDict 

from app.models.order import OrderStatus

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    items: list[OrderItemResponse]
    

class CreateOrderRequest(BaseModel):
    idempotency_key: str
    
    