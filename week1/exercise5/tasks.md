# EASY-CHATGPT — Task Breakdown (Advanced Implementation)

> Second implementation pass — **Streaming Support via Server-Sent Events (SSE)**.
> This upgrades the proxy so the LLM answer types out token-by-token on the frontend.

---

## Phase 5 — Streaming Backend

### - [x] Task 5.1 · Add `sse-starlette` dependency
- Run `uv add sse-starlette` in the `backend/` directory.
- Verify `pyproject.toml` and `uv.lock` are updated.

### - [x] Task 5.2 · Streaming Chat Endpoint (`main.py`)
- Import `EventSourceResponse` from `sse-starlette`.
- Create a new endpoint `POST /api/chat/stream` (or update the existing `POST /api/chat`).
- The endpoint must:
  1. Append the user's message to the conversation store.
  2. Call `client.chat.completions.create` with `stream=True` and `stream_options={"include_usage": True}`.
  3. Return an `EventSourceResponse` powered by an async generator.
- Inside the generator:
  1. Iterate over the chunks returned by the OpenAI client.
  2. Yield each token to the client in JSON format.
  3. Accumulate the full string of the assistant's reply.
  4. Capture the token usage from the final chunk (if provided by the model).
  5. After the stream ends, append the accumulated assistant reply to the `messages` list and update `token_usage` in the global store.

---

## Phase 6 — Streaming Frontend

### - [x] Task 6.1 · Read the SSE stream (`app.js`)
- Update the `fetch` call in the chat form submission to hit the streaming endpoint.
- Instead of awaiting a single JSON response, use `response.body.getReader()` and a `TextDecoder`.
- Read the stream in a loop.
- Split the incoming text by `\n\n` to isolate individual Server-Sent Events.
- Parse the `data: ...` payload of each event.

### - [x] Task 6.2 · Incremental UI updates (`app.js`)
- Maintain an accumulated string of the assistant's reply in the JavaScript state.
- As each new token arrives, append it to the accumulated string.
- Call `marked.parse()` on the accumulated string and update the assistant's message bubble `innerHTML`.
- Wait until the stream completely finishes before running `hljs.highlightElement()` on code blocks (to avoid performance issues and glitches while code blocks are half-written).

### - [x] Task 6.3 · Finalise turn
- When the stream closes, call `refreshContext()` to fetch the updated context view (so the new messages array and the updated token counts are rendered).
- Scroll to the bottom of the chat as the text streams in.

---

## Phase 7 — Validation

### - [x] Task 7.1 · End-to-end Docker test
- Rebuild the container: `docker compose up --build -d`
- Ask a question that requires a long answer (e.g., "Write a short story about a brave toaster").
- Verify the text streams in smoothly token-by-token.
- Verify the Context Panel updates correctly with the full message and token counts after the stream completes.

---

## Task Summary

| # | Task | Covers |
|---|---|---|
| - [x] 5.1 | Add `sse-starlette` dependency | Dependencies |
| - [x] 5.2 | Streaming Chat Endpoint | Proxying the live stream |
| - [x] 6.1 | Read the SSE stream | Fetch Streams API |
| - [x] 6.2 | Incremental UI updates | UI typing effect |
| - [x] 6.3 | Finalise turn | Context view sync |
| - [x] 7.1 | End-to-end Docker test | E2E Verification |
