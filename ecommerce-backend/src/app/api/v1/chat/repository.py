import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, ChatMessage, MessageRole


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_session(self, user_id: uuid.UUID) -> ChatSession:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        if existing:
            return existing

        new_session = ChatSession(user_id=user_id)
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session

    async def create_new_session(self, user_id: uuid.UUID) -> ChatSession:
        """Start a brand-new conversation session and clear old messages for this user."""
        stmt = select(ChatSession.id).where(ChatSession.user_id == user_id)
        result = await self.session.execute(stmt)
        session_ids = list(result.scalars().all())
        if session_ids:
            await self.session.execute(
                delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids))
            )
            await self.session.execute(
                delete(ChatSession).where(ChatSession.id.in_(session_ids))
            )

        new_session = ChatSession(user_id=user_id)
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session

    async def add_message(
        self, session_id: uuid.UUID, role: MessageRole, content: str
    ) -> None:
        message = ChatMessage(session_id=session_id, role=role, content=content)
        self.session.add(message)
        await self.session.commit()

    async def add_exchange(
        self, session_id: uuid.UUID, user_message: str, assistant_message: str
    ) -> None:
        """Persist the user message and the assistant reply in one transaction.

        Only called after a successful model turn so a failed OpenAI call cannot
        leave an orphaned user message behind.
        """
        self.session.add(
            ChatMessage(
                session_id=session_id, role=MessageRole.USER, content=user_message
            )
        )
        self.session.add(
            ChatMessage(
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=assistant_message,
            )
        )
        await self.session.commit()

    async def get_recent_messages(
        self, session_id: uuid.UUID, limit: int = 10
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))
