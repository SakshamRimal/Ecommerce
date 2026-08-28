from sqlalchemy import String , Boolean , Enum
from sqlalchemy.orm import Mapped , mapped_column , relationship 
from enum import Enum as PyEnum

from app.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin

class UserRole(str, PyEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    
class User(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255) , unique=True , index=True , nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255) , nullable=False)
    full_name: Mapped[str] = mapped_column(String(255) , nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean , default=True , nullable=False)
    
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER, nullable=False
    )
    
    carts: Mapped[list["Cart"]] = relationship(back_populates="user" , cascade="all, delete-orphan")
    
    