---
name: AI Shopping Assistant (Chat)
description: Use when changing the OpenAI chat endpoint, tool definitions, tool execution, chat history persistence, or embeddings.
---

# AI Shopping Assistant

## When to use

- `POST /api/v1/chat`.
- OpenAI system prompt, model, token limits.
- Tool/function definitions and `ToolExecutor`.
- Chat session/message persistence.
- Product embeddings.

## Files

| Concern | File |
|---|---|
| Route | `src/app/api/v1/chat/controller.py` |
| Logic | `src/app/api/v1/chat/service.py` |
| Persistence | `src/app/api/v1/chat/repository.py` |
| Schemas | `src/app/api/v1/chat/schema.py` |
| Tool schemas | `src/app/ai/tools.py` |
| Tool dispatch | `src/app/ai/tool_executor.py` |
| Embeddings | `src/app/ai/embeddings.py` |
| Models | `src/app/models/chat.py` |
| Config | `app.core.config` (`OPENAI_*`, `CHAT_MAX_HISTORY_MESSAGES`) |

## Endpoint

`POST /chat` (authenticated, `10/minute` per IP) body `{message: 1..1000}` →
`{reply}`. There is no history GET, session list, streaming, or delete.

## Flow

1. Get or create the user's **latest** chat session.
2. Persist the user message.
3. Load the last `CHAT_MAX_HISTORY_MESSAGES` (default 20) messages in
   chronological order and prepend the system prompt.
4. Call OpenAI with `TOOL_DEFINITIONS`.
5. While `finish_reason == "tool_calls"`, append the assistant tool-call message,
   execute each tool, append tool results, and call the model again.
6. Persist and return the final assistant text.

## Tools

| Tool | Backed by |
|---|---|
| `search_products` | `SearchService.search_products` (ES) |
| `get_product_details` | `ProductRepository.get_by_id` |
| `check_stock` | `ProductRepository.get_by_id` |
| `semantic_search_products` | `SearchService.semantic_search_products` (pgvector) |

## Rules

1. The assistant must never invent prices/stock; all facts come from tools.
2. Persist both user and assistant messages.
3. Keep the tool loop bounded (add a max-iteration guard).
4. Tools return JSON strings.
5. Do not log full prompts or secrets; log tool name + args is acceptable but
   avoid PII.

## Gotchas

- `check_stock` in `tools.py` uses the key `"paramters"` instead of
  `"parameters"` — the model may not be able to call it reliably.
- `search_products` advertises `max_price` but `ToolExecutor` ignores it.
- `search_products` filters only `min_price`, and does so after ES already
  limited to 5 results.
- The tool loop has no iteration cap; a misbehaving model could loop.
- `ChatRepository.add_message` commits per message, so a failed model call can
  leave a user message without a reply.
- One session per user is reused forever; message history grows until trimmed by
  the 20-message window.
- `get_or_create_session` orders by `created_at DESC`; `updated_at` is not used.
- Chat requires `OPENAI_API_KEY`; a missing/empty key fails at call time.

## Verify

```bash
uv run pytest tests/unit -q
# manual: POST /api/v1/chat with a bearer token and a real OpenAI key
```

## Related

- `docs/12-ai-chat.md`
- `docs/11-search.md`
- `docs/18-known-issues.md`
