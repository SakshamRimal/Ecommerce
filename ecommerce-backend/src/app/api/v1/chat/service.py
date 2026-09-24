import structlog
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.ai.tools import TOOL_DEFINITIONS
from app.ai.tool_executor import ToolExecutor
from app.api.v1.chat.repository import ChatRepository
from app.models.chat import MessageRole

settings = get_settings()
logger = structlog.get_logger("chat_service")

SYSTEM_PROMPT = """You are a helpful shopping assistant for an online store.
Use the available tools to search the real product catalog and check stock —
never invent prices, product names, or availability. If you don't know something,
say so and offer to search for it. Keep responses concise and friendly."""


class ChatService:
    def __init__(self, repository: ChatRepository, tool_executor: ToolExecutor):
        self.repository = repository
        self.tool_executor = tool_executor
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def send_message(self, session_id, user_message: str) -> str:
        await self.repository.add_message(session_id, MessageRole.USER, user_message)

        history = await self.repository.get_recent_messages(
            session_id, limit=settings.chat_max_history_messages
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": m.role.value, "content": m.content} for m in history]

        # First call — GPT decides whether to use tools
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            max_tokens=settings.openai_max_tokens,
        )
        choice = response.choices[0]

        # Tool-calling loop — GPT can chain multiple tool calls before its final answer
        while choice.finish_reason == "tool_calls":
            messages.append(choice.message.model_dump(exclude_none=True))

            for tool_call in choice.message.tool_calls:
                import json
                args = json.loads(tool_call.function.arguments)
                logger.info("tool_call_executed", tool=tool_call.function.name, args=args)

                result = await self.tool_executor.execute(tool_call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                max_tokens=settings.openai_max_tokens,
            )
            choice = response.choices[0]

        final_text = choice.message.content or ""
        await self.repository.add_message(session_id, MessageRole.ASSISTANT, final_text)

        return final_text