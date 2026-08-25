from sqlalchemy import String 
from sqlalchemy.orm import Mapped , mapped_column , relationship

from app.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin

class Category(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(255) , unique=True , index=True , nullable=False)
    slug: Mapped[str] = mapped_column(String(255) , unique=True , index=True , nullable=False)
    
    products: Mapped[list["Product"]] = relationship(back_populates="category" , cascade="all, delete-orphan")