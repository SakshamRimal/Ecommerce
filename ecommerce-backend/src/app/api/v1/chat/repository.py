import uuid 
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession , ChatMessage , MessageRole

class ChatRepository:
    def __init__(self , session: AsyncSession):
        self.session = session 
        
    async def get_or_create_session(self , user_id: uuid.UUID) -> ChatSession:
        stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc())
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            return existing
        
        new_session = ChatSession(user_id=user_id)
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session
    
    async def add_message(self , session_id: uuid.UUID , role: MessageRole , content: str) -> None:
        message = ChatMessage(session_id=session_id , role=role , content=content)
        self.session.add(message)
        await self.session.commit()
    
    async def get_recent_messages(self , session_id: uuid.UUID , limit: int = 10) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))  # Return messages in chronological order
        