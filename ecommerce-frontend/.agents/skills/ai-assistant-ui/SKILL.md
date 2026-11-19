---
name: AI Assistant UI
description: Use when building the shopping assistant chat panel, message list, composer, or handling chat errors and rate limits.
---

# AI Assistant UI

## When to use

- Chat panel / assistant drawer.
- Message input and transcript.
- Handling OpenAI/rate-limit failures.

## Endpoint

`POST /chat` (auth required, **10 requests/minute**)

```ts
// request
{ message: string } // 1..1000 chars
// response
{ reply: string }
```

There is **no** history endpoint, streaming, session selection, or delete. The
backend reuses the user's latest session and keeps the last 20 messages of
context internally.

## UX design

1. Client keeps the visible transcript in local state (the server persists it but
   cannot return it).
2. Show an optimistic user bubble, then a typing indicator.
3. Disable the composer while a request is pending.
4. On success, append the assistant reply.
5. On 429, show "Too many messages — try again in a minute" and a cooldown.
6. On 401, refresh/redirect to login.
7. On 5xx/OpenAI failure, show a retry action without losing the draft.
8. On page reload, the visible transcript is lost (no history API). Warn or
   store a local draft if needed.
9. Limit input to 1000 chars with a counter.
10. Render replies as plain text/Markdown safely (sanitize).

## Suggested component state

```ts
type Message = { id: string; role: "user" | "assistant"; text: string };
type ChatState = {
  messages: Message[];
  draft: string;
  pending: boolean;
  cooldownUntil?: number;
};
```

## Rules

1. Never auto-send on mount; it costs tokens and hits rate limits.
2. Do not claim the assistant has access to the user's cart/orders — tools are
   read-only catalog search/stock today.
3. Do not render raw HTML from the model.
4. Do not log message contents to analytics without consent.
5. Respect the 10/min limit globally per user/IP.
6. Surface the privacy implication: messages are sent to OpenAI.

## Accessibility

- `role="log"` with `aria-live="polite"` for new messages.
- Composer is a labelled `<textarea>`; Enter sends, Shift+Enter newline.
- Focus moves to the transcript on new replies, not away from the composer.
- Full keyboard operability; visible focus.

## Gaps

| Missing | Workaround |
|---|---|
| Streaming | spinner + full reply |
| History | local-only transcript |
| Session management | single implicit session |
| Cart mutations via chat | not supported |
| Citations | show tool-derived product links if you add them server-side |

## Related

- `../../../docs/05-pages-and-routes.md`
- `../../../../ecommerce-backend/docs/12-ai-chat.md`
