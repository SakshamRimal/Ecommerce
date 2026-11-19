from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.deps import get_current_user
from app.models.user import User
from app.api.v1.chat.repository import ChatRepository
from app.api.v1.chat.service import ChatService
from app.api.v1.chat.schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatMessageResponse,
)
from app.api.v1.products.repository import ProductRepository
from app.api.v1.search.service import SearchService
from app.ai.tool_executor import ToolExecutor
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    product_repository = ProductRepository(session)
    tool_executor = ToolExecutor(
        SearchService(product_repository), product_repository
    )
    return ChatService(ChatRepository(session), tool_executor)


@router.post("", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    reply = await service.send_message_for_user(current_user.id, data.message)
    return ChatResponse(reply=reply)


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    messages = await service.get_history(current_user.id, limit=limit)
    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(message) for message in messages]
    )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    await service.clear_history(current_user.id)
