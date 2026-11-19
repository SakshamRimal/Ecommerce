from __future__ import annotations

from typing import TYPE_CHECKING
import uuid
from sqlalchemy import Index, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlmodel import Numeric
from pgvector.sqlalchemy import VECTOR

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category

class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_id_name", "category_id", "name"),
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped["Category"] = relationship(back_populates="products")

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(1536), nullable=True)  # text-embedding-3-small = 1536 dims
    