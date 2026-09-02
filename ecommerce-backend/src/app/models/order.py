import uuid 
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey , String , Enum , Numeric , String 
from sqlalchemy.orm import Mapped , mapped_column , relationship

from app.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin

class OrderStatus(str , PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    
class Order(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    __tablename__ = "orders"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id") , nullable=False , index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus , name="order_status") , default=OrderStatus.PENDING , nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Numeric(10 , 2) , nullable=False)
    
    #idempotemncy prevents duplicate order creation in case of network issues or retries
    idempotency_key: Mapped[str] = mapped_column(String(255) , unique=True , nullable=False , index=True)
    
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship()
    
class OrderItem(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    __tablename__ = "order_items"
    
    order_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id" , ondelete="CASCADE") , nullable=False , index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id" , ondelete="CASCADE") , nullable=False 
    )
    
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id" , ondelete="RESTRICT") , nullable=False
    )
    unit_price: Mapped[float] = mapped_column(Numeric(10 , 2) , nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    
    order: Mapped["Order"] = relationship(back_populates="items")
    