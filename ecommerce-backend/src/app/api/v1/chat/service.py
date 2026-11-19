from decimal import Decimal
import json
import re

import structlog
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.ai.tools import TOOL_DEFINITIONS
from app.ai.tool_executor import ToolExecutor
from app.api.v1.chat.repository import ChatRepository

settings = get_settings()
logger = structlog.get_logger("chat_service")

SYSTEM_PROMPT = """You are a helpful shopping assistant for an online store.
Use the available tools to search the real product catalog and check stock —
never invent prices, product names, or availability. Always display prices with
the currency prefix 'NRs' (e.g. NRs 119.99). If you don't know something,
say so and offer to search for it. Keep responses concise and friendly."""

GREETING_WORDS = {
    "hi",
    "hello",
    "hey",
    "hola",
    "namaste",
    "greetings",
    "yo",
    "sup",
    "good morning",
    "good afternoon",
    "good evening",
}

STOP_WORDS = {
    "what",
    "which",
    "where",
    "when",
    "show",
    "find",
    "tell",
    "more",
    "have",
    "has",
    "do",
    "you",
    "your",
    "the",
    "for",
    "with",
    "about",
    "some",
    "any",
    "can",
    "please",
    "help",
    "me",
    "looking",
    "want",
    "need",
    "buy",
    "get",
    "are",
    "is",
    "in",
    "on",
    "to",
    "of",
    "and",
    "or",
    "a",
    "an",
    "from",
    "under",
    "below",
    "less",
    "than",
    "max",
    "budget",
    "around",
    "nrs",
    "rs",
    "usd",
    "price",
    "cost",
    "stock",
    "available",
    "availability",
    "currently",
    "check",
    "its",
    "it",
    "whether",
    "complementary",
    "items",
    "item",
    "products",
    "product",
    "catalog",
    "gear",
    "recommend",
    "best",
    "top",
    "rated",
    "compare",
    "build",
    "clean",
    "productive",
    "gifts",
    "gift",
    "remote",
    "engineer",
    "deep",
    "focus",
    "lightweight",
    "equipment",
}


def _is_usable_key(key: str | None) -> bool:
    if not key:
        return False
    cleaned = key.strip()
    if not cleaned:
        return False
    placeholder_prefixes = ("your_", "sk-,", "replace_", "changeme")
    return not cleaned.lower().startswith(placeholder_prefixes)


class ChatService:
    def __init__(self, repository: ChatRepository, tool_executor: ToolExecutor):
        self.repository = repository
        self.tool_executor = tool_executor
        self.client = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder")
        self.providers = self._build_llm_providers()

    @staticmethod
    def _build_llm_providers() -> list[dict]:
        """Build ordered LLM fallback chain:
        1. Gemini Free (https://generativelanguage.googleapis.com/v1beta/openai/)
        2. Grok / Groq Free (https://api.x.ai/v1 or https://api.groq.com/openai/v1)
        3. OpenAI Fallback (https://api.openai.com/v1)
        """
        cfg = get_settings()
        chain: list[dict] = []

        # 1. Primary: Gemini Free tier
        if _is_usable_key(cfg.gemini_api_key):
            gemini_model = (
                "gemini-2.5-flash"
                if cfg.gemini_model in {"gemini-2.0-flash", "gemini-1.5-flash"}
                else cfg.gemini_model
            )
            chain.append(
                {
                    "name": "gemini",
                    "model": gemini_model,
                    "client": AsyncOpenAI(
                        api_key=cfg.gemini_api_key.strip(),
                        base_url=cfg.gemini_base_url,
                    ),
                }
            )

        # 2. First Fallback: Grok (xAI) or Groq Free tier
        grok_key = (cfg.grok_api_key or cfg.groq_api_key or "").strip()
        if _is_usable_key(grok_key):
            if cfg.grok_base_url:
                base_url = cfg.grok_base_url
            elif grok_key.startswith("xai-"):
                base_url = "https://api.x.ai/v1"
            else:
                base_url = "https://api.groq.com/openai/v1"

            if grok_key.startswith("xai-") and cfg.grok_model in {
                "llama-3.3-70b-versatile",
                "openai/gpt-oss-120b",
            }:
                model = "grok-2-latest"
            elif cfg.grok_model == "llama-3.3-70b-versatile":
                model = "openai/gpt-oss-120b"
            else:
                model = cfg.grok_model
            chain.append(
                {
                    "name": "grok",
                    "model": model,
                    "client": AsyncOpenAI(api_key=grok_key, base_url=base_url),
                }
            )

        # 3. Final LLM Fallback: OpenAI
        if _is_usable_key(cfg.openai_api_key):
            chain.append(
                {
                    "name": "openai",
                    "model": cfg.openai_model,
                    "client": AsyncOpenAI(api_key=cfg.openai_api_key.strip()),
                }
            )

        return chain

    async def _complete(self, messages: list[dict]):
        """Try Gemini first; on quota/error fall back to Grok, then OpenAI."""
        providers = self.providers or [
            {
                "name": "openai",
                "model": settings.openai_model,
                "client": self.client,
            }
        ]
        last_exc: Exception | None = None

        for idx, provider in enumerate(providers):
            provider_name = provider["name"]
            model_name = provider["model"]
            llm_client: AsyncOpenAI = provider["client"]
            try:
                response = await llm_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    max_tokens=settings.openai_max_tokens,
                )
                logger.info(
                    "llm_completion_succeeded",
                    provider=provider_name,
                    model=model_name,
                )
                return response
            except Exception as exc:  # noqa: BLE001 - fall back to next provider
                last_exc = exc
                next_provider = (
                    providers[idx + 1]["name"]
                    if idx + 1 < len(providers)
                    else "local_catalog_concierge"
                )
                logger.warning(
                    "llm_provider_quota_or_error_fallback",
                    failed_provider=provider_name,
                    failed_model=model_name,
                    fallback_to=next_provider,
                    error=str(exc),
                )

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("No LLM providers configured")

    @staticmethod
    def _parse_arguments(raw: str | None) -> dict:
        try:
            parsed = json.loads(raw or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    async def _local_concierge_reply(self, user_message: str) -> str:
        """Smart local catalog concierge used when OpenAI API is unreachable or out of quota."""
        cleaned = user_message.strip()
        lower = cleaned.lower().rstrip("!.?,")

        product_repo = getattr(self.tool_executor, "product_repository", None)
        all_products = (
            await product_repo.list_products(limit=200, offset=0)
            if product_repo is not None
            else []
        )

        # 1. Pure greeting or help prompt
        if lower in GREETING_WORDS or lower in {"help", "what can you do", "who are you"}:
            if not all_products:
                return (
                    "Hello! Welcome to Commercify. I'm your AI Shopping Concierge. "
                    "Our catalog is currently empty, so once an administrator adds products, "
                    "I can help you search by keyword, filter by budget, and verify real-time stock!"
                )
            categories = sorted(
                {p.category.name for p in all_products if getattr(p, "category", None)}
            )
            cat_text = (
                f" across categories like **{', '.join(categories)}**"
                if categories
                else ""
            )
            return (
                f"Hello! Welcome to Commercify. I'm your AI Shopping Concierge.\n\n"
                f"We currently have **{len(all_products)} product(s)** in our live catalog{cat_text}. "
                f"You can ask me to:\n"
                f"• Show all available products or browse by category\n"
                f"• Find items within a budget (e.g., *\"under NRs 200\"*)\n"
                f"• Check live warehouse stock and pricing for a specific product\n\n"
                f"What are you looking for today?"
            )

        # 2. Thank you / goodbye
        if any(phrase in lower for phrase in ("thank", "thanks", "bye", "goodbye")):
            return "You're very welcome! Let me know anytime if you'd like to check products, prices, or stock."

        if not all_products:
            return (
                "I checked our live catalog, and there are currently no products listed yet. "
                "Please check back soon or add products via the Admin Console!"
            )

        # 3. Extract optional budget / price constraint (e.g. "under NRs 150", "below 200")
        max_price: Decimal | None = None
        budget_match = re.search(
            r"(?:under|below|less than|max|budget|around)\s*(?:nrs\.?|rs\.?|\$)?\s*(\d+(?:\.\d{1,2})?)",
            lower,
        )
        if budget_match:
            max_price = Decimal(budget_match.group(1))

        # 4. Check for an exact product name mention first (e.g. "Tell me about the Nike Air Max")
        exact_matches = [
            p
            for p in all_products
            if p.name.lower() in lower
            and (max_price is None or Decimal(str(p.price)) <= max_price)
        ]
        if len(exact_matches) == 1 and "compare" not in lower:
            matched = [(100, 100, exact_matches[0])]
        else:
            cleaned_without_price = re.sub(
                r"(?:nrs\.?|rs\.?|\$)\s*\d+(?:\.\d{1,2})?", " ", lower
            )
            tokens = [
                w
                for w in re.findall(r"[a-z0-9]+", cleaned_without_price)
                if w not in STOP_WORDS and len(w) >= 2 and not w.isdigit()
            ]

            matched = []
            if tokens:
                for p in all_products:
                    if max_price is not None and Decimal(str(p.price)) > max_price:
                        continue
                    name_low = p.name.lower()
                    cat_low = p.category.name.lower() if getattr(p, "category", None) else ""
                    desc_low = (p.description or "").lower()
                    name_words = set(re.findall(r"[a-z0-9]+", name_low))
                    cat_words = set(re.findall(r"[a-z0-9]+", cat_low))
                    # Weight whole-word product name matches highest
                    name_hits = sum(
                        4 if t in name_words else (2 if t in name_low else 0)
                        for t in tokens
                    )
                    cat_hits = sum(
                        3 if t in cat_words else (1 if t in cat_low else 0)
                        for t in tokens
                    )
                    desc_hits = sum(1 for t in tokens if t in desc_low)
                    score = name_hits + cat_hits + desc_hits
                    if score > 0:
                        matched.append((score, name_hits, p))

                matched.sort(key=lambda item: (item[0], item[1]), reverse=True)

        if matched:
            top_score, top_name_hits, top_prod = matched[0]
            # If one product strongly matches by name (e.g. "Nike Air Max"), show full details
            is_single_focus = (
                len(matched) == 1
                or (
                    top_name_hits >= 6
                    and "compare" not in lower
                    and top_score > matched[1][0] + 2
                )
            )
            if is_single_focus:
                p = top_prod
                stock_msg = (
                    f"In stock (**{p.stock_quantity} unit(s) ready to ship**)"
                    if p.stock_quantity > 0
                    else "Currently **out of stock**"
                )
                desc = f"\n\n**Overview:** {p.description}" if p.description else ""
                related = [
                    r
                    for r in all_products
                    if r.id != p.id
                    and getattr(r, "category_id", None) == getattr(p, "category_id", None)
                ][:2]
                related_text = ""
                if related:
                    rel_lines = [
                        f"• **{r.name}** — NRs {Decimal(str(r.price)):.2f} ({r.stock_quantity} in stock)"
                        for r in related
                    ]
                    related_text = "\n\n**Complementary items in this category:**\n" + "\n".join(rel_lines)
                return (
                    f"Here are the live details for **{p.name}**:\n\n"
                    f"• **Price:** NRs {Decimal(str(p.price)):.2f}\n"
                    f"• **Category:** {p.category.name if getattr(p, 'category', None) else 'General'}\n"
                    f"• **Warehouse Stock:** {stock_msg}"
                    f"{desc}"
                    f"{related_text}"
                )

            top = [p for _, _, p in matched[:5]]
            budget_note = f" under **NRs {max_price:.2f}**" if max_price is not None else ""
            lines = [
                f"• **{p.name}** — **NRs {Decimal(str(p.price)):.2f}** "
                f"({p.stock_quantity} in stock{f', {p.category.name}' if getattr(p, 'category', None) else ''})"
                + (f"\n  *{p.description}*" if p.description else "")
                for p in top
            ]
            return (
                f"Here are the best matching products{budget_note} from our live catalog:\n\n"
                + "\n".join(lines)
                + "\n\nWould you like full specs or stock verification on any of these?"
            )

        # 5. Catalog overview, recommendations, or budget-only query (e.g. "Gifts under NRs 200", "What is in stock?")
        candidates = [
            p
            for p in all_products
            if max_price is None or Decimal(str(p.price)) <= max_price
        ]
        if not candidates:
            return f"We don't currently have any products under **NRs {max_price:.2f}** in stock."

        if max_price is not None or any(
            phrase in lower
            for phrase in (
                "all product",
                "what product",
                "what do you have",
                "what do you sell",
                "show me",
                "list",
                "in stock",
                "available",
                "catalog",
                "recommend",
                "best",
                "top",
                "compare",
                "gift",
                "setup",
            )
        ):
            heading = (
                f"Here are our top in-stock recommendations under **NRs {max_price:.2f}**:"
                if max_price is not None
                else "Here are our top featured products currently available in stock:"
            )
            lines = [
                f"• **{p.name}** — **NRs {Decimal(str(p.price)):.2f}** "
                f"({p.stock_quantity} in stock{f', {p.category.name}' if getattr(p, 'category', None) else ''})"
                for p in candidates[:8]
            ]
            return (
                f"{heading}\n\n"
                + "\n".join(lines)
                + "\n\nAsk me about any product by name for full specs and complementary items!"
            )

        # 6. No keyword match — be transparent and show available catalog items
        sample_lines = [
            f"• **{p.name}** (NRs {Decimal(str(p.price)):.2f}) — {p.stock_quantity} in stock"
            for p in all_products[:6]
        ]
        return (
            f"I couldn't find an exact match for *\"{cleaned}\"* in our catalog right now.\n\n"
            f"Here are some popular items we currently have in stock:\n"
            + "\n".join(sample_lines)
            + "\n\nFeel free to ask about any of these!"
        )

    async def send_message(self, session_id, user_message: str) -> str:
        history = await self.repository.get_recent_messages(
            session_id, limit=settings.chat_max_history_messages
        )
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": m.role.value, "content": m.content} for m in history]
        messages.append({"role": "user", "content": user_message})

        final_text = ""
        try:
            for _ in range(settings.chat_max_tool_iterations + 1):
                response = await self._complete(messages)
                choice = response.choices[0]

                if choice.finish_reason != "tool_calls":
                    final_text = choice.message.content or ""
                    break

                messages.append(choice.message.model_dump(exclude_none=True))

                for tool_call in choice.message.tool_calls or []:
                    args = self._parse_arguments(tool_call.function.arguments)
                    logger.info(
                        "tool_call_executed",
                        tool=tool_call.function.name,
                        args=args,
                    )
                    result = await self.tool_executor.execute(
                        tool_call.function.name, args
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
            else:
                logger.warning("chat_tool_loop_capped", session_id=str(session_id))
                final_text = (
                    "I'm sorry — I couldn't finish that request. "
                    "Could you rephrase or narrow it down?"
                )
        except Exception as exc:  # noqa: BLE001 - fallback when OpenAI quota/network fails
            logger.warning("openai_chat_fallback", error=str(exc))
            final_text = await self._local_concierge_reply(user_message)

        if not final_text:
            final_text = (
                "I'm sorry — I couldn't complete that request. Please try again."
            )

        await self.repository.add_exchange(session_id, user_message, final_text)
        return final_text

    async def send_message_for_user(self, user_id, user_message: str) -> str:
        session = await self.repository.get_or_create_session(user_id)
        return await self.send_message(session.id, user_message)

    async def get_history(self, user_id, limit: int = 50) -> list:
        session = await self.repository.get_or_create_session(user_id)
        return await self.repository.get_recent_messages(session.id, limit=limit)

    async def clear_history(self, user_id) -> None:
        await self.repository.create_new_session(user_id)
