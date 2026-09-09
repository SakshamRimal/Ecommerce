import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CartItemRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, default=1)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    items: list[CartItemResponse]
    total: Decimal
