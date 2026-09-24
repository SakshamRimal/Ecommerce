from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user
from app.models.user import User
from app.api.v1.chat.repository import ChatRepository
from app.api.v1.chat.service import ChatService
from app.api.v1.chat.schema import ChatRequest, ChatResponse
from app.api.v1.products.repository import ProductRepository
from app.api.v1.search.service import SearchService
from app.ai.tool_executor import ToolExecutor
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    tool_executor = ToolExecutor(SearchService(), ProductRepository(session))
    return ChatService(ChatRepository(session), tool_executor)


@router.post("", response_model=ChatResponse)

@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
    session=Depends(get_db_session),
):
    repository = ChatRepository(session)
    chat_session = await repository.get_or_create_session(current_user.id)
    reply = await service.send_message(chat_session.id, data.message)
    return ChatResponse(reply=reply)