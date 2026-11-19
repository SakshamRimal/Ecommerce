# 12 — AI Chat

## Endpoint

`POST /api/v1/chat` — bearer required, `10/minute`

```json
{ "message": "I need a gift for someone who loves coffee" }
```

```json
{ "reply": "Here are a few ideas…" }
```

One request = one assistant turn. There is no streaming, history retrieval,
session list, or delete endpoint.

## Components

| Component | File | Role |
|---|---|---|
| Controller | `api/v1/chat/controller.py` | auth, rate limit, DI |
| Service | `api/v1/chat/service.py` | OpenAI loop, system prompt |
| Repository | `api/v1/chat/repository.py` | sessions/messages |
| Tool schemas | `ai/tools.py` | function definitions |
| Tool executor | `ai/tool_executor.py` | dispatch to backend |
| Embeddings | `ai/embeddings.py` | vectors |
| Models | `models/chat.py` | `ChatSession`, `ChatMessage` |

## Session model

- `ChatRepository.get_or_create_session(user_id)` selects the **latest** session
  by `created_at DESC`, or creates one.
- All messages for a user accumulate in that session.
- The service reads the last `CHAT_MAX_HISTORY_MESSAGES` (20) in chronological
  order.
- User and assistant messages are persisted; tool messages are **not** persisted.
- Every `add_message` commits immediately.

## Prompt

```
You are a helpful shopping assistant for an online store.
Use the available tools to search the real product catalog and check stock —
never invent prices, product names, or availability. If you don't know something,
say so and offer to search for it. Keep responses concise and friendly.
```

## Tool-calling loop

```python
messages = [system] + history
response = await client.chat.completions.create(
    model=settings.openai_model,
    messages=messages,
    tools=TOOL_DEFINITIONS,
    max_tokens=settings.openai_max_tokens,
)
choice = response.choices[0]

while choice.finish_reason == "tool_calls":
    messages.append(choice.message.model_dump(exclude_none=True))
    for call in choice.message.tool_calls:
        args = json.loads(call.function.arguments)
        result = await executor.execute(call.function.name, args)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    response = await client.chat.completions.create(...)
    choice = response.choices[0]

final = choice.message.content or ""
await repository.add_message(session_id, MessageRole.ASSISTANT, final)
return final
```

There is **no iteration cap**; a misbehaving model could loop until the request
times out or tokens run out.

## Tools

| Tool | Arguments | Backend | Returns |
|---|---|---|---|
| `search_products` | `query`, optional `min_price`, `max_price` | ES search | up to 5 `{id,name,price,stock}` |
| `get_product_details` | `product_id` | DB lookup | full product + category |
| `check_stock` | `product_id` | DB lookup | `{product_id, stock_quantity}` |
| `semantic_search_products` | `query` | embedding + pgvector | up to 5 `{id,name,price,stock}` |

### Known tool bugs

1. `check_stock` uses the key `"paramters"` instead of `"parameters"`. Depending
   on the OpenAI API version this can make the tool schema invalid or prevent the
   model from calling it reliably.
2. `search_products` advertises `max_price`, but `ToolExecutor` only applies
   `min_price`.
3. Price filtering happens **after** ES returns 5 results, so the model may see
   fewer than 5 even when more matches exist.
4. `semantic_search_products` receives `SearchService()` with
   `product_repository=None` from the chat controller, so it will fail at
   `self.product_repository.semantic_search(...)`. The controller should pass
   `ProductRepository(session)` into `SearchService`.
5. `get_product_details` passes a raw string to `uuid.UUID(...)` without a
   try/except; a malformed tool argument raises and aborts the turn.
6. The final text is not stored if the loop raises; the user message is already
   committed.

## Configuration

| Variable | Default |
|---|---|
| `OPENAI_API_KEY` | required |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | `800` |
| `CHAT_MAX_HISTORY_MESSAGES` | `20` |

## Cost/latency controls

- `max_tokens=800`.
- History window 20 messages.
- Rate limit 10/min per IP.
- Up to 5 results per tool call.

Not present:
- Per-user quota.
- Prompt/token accounting.
- Caching of repeated questions.
- Guardrails for prompt injection or off-topic use.
- Streaming.

## Recommended improvements

1. Fix the `check_stock` schema key and remove or implement `max_price`.
2. Pass a real `ProductRepository` into `SearchService`.
3. Add a max tool-iteration guard (e.g. 5).
4. Wrap tool execution in try/except and return a JSON error to the model.
5. Add `GET /chat/history` and `POST /chat/sessions`.
6. Persist tool calls/results for auditability.
7. Add per-user quotas and a circuit breaker for OpenAI failures.
8. Consider semantic search directly in the first tool call to reduce round
   trips.
