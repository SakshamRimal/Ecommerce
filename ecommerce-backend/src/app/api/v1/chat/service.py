import structlog 
from openai import AsyncOpenAI 
from app.core.config import get_settings 
from app.ai.tools import TOOL_DEFINATIONS
from app.ai.tool_executor import ToolExecutor
from app.api.v1.chat.repository import ChatRepository
from app.models.chat import MessageRole 

settings = get_settings()
logger = structlog.get_logger("chat_service")

SYSTEM_PROMPT = """
You are a helpful shopping assistant for an online store. Use the availabe tools to seatch the real products catalog and check stock 
never invent prices , product names or availability. If you dont know somethings , say so and offer to search for it. Keep responses concise and friendly
"""

class ChatService:
    def __init__(self , repository: ChatRepository , tool_executor: ToolExecutor):
        self.repository = repository 
        self.tool_executor = tool_executor
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def send_message(self , session_id , user_message: str) -> str:
        await self.repository.add_message(session_id , MessageRole.USER , user_message)
        
        history = await self.repository.get_recent_messages(
            session_id , limit=settings.chat_max_history_messages
        )
        messages = [{"role":"system"}]