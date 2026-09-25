import uuid 
from sqlalchemy import ForeignKey , Text , Enum as SAEnum
from sqlalchemy.orm import Mapped , mapped_column , relationship
from enum import Enum as PyEnum

from app.db.base import Base , TimestampMixin , UUIDPrimaryKeyMixin

class MessageRole(str , PyEnum):
    USER = "user" 
    ASSISTANT = "assistant"
    TOOL = "tool"
    
class ChatSession(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    __tablename__ = "chat_sessions"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id" , ondelete="CASCADE") , nullable=False
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session" , cascade="all, delete-orphan" , order_by="ChatMessage.created_at"
    )

class ChatMessage(Base , UUIDPrimaryKeyMixin , TimestampMixin):
    __tablename__ = "chat_messages"
    
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id" , ondelete="CASCADE") , nullable=False , index=True
    )
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text , nullable=False)
    session: Mapped["ChatSession"] = relationship(back_populates="messages")