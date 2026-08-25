from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid 
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """All ORM models inherit from this base class."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns to a model."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key to any model that inherits from this mixin."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
"""
Why UUID instead of auto-increment integers for the primary key?

Integers leak information (/products/1042 tells competitors roughly how many products you have, and lets people guess other IDs by incrementing).
UUIDs can be generated client-side or in distributed systems without coordinating with the DB, which matters once you scale beyond one server.
Trade-off: UUIDs are 16 bytes vs 4-8 for integers, and slightly worse for index locality. For an e-commerce catalog, this trade-off is well worth it. (You'll see both approaches in the wild — this is a judgment call, not a hard rule.)


"""
