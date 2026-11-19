import datetime as dt
import uuid

from pydantic import BaseModel, Field

from app.models.chat import MessageRole


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000, description="The user's message to the chat assistant.")


class ChatResponse(BaseModel):
    reply: str = Field(description="The assistant's reply to the user's message.")


class ChatMessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: dt.datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
