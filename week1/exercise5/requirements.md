# EASY-CHATGPT — Requirements
> Derived from **Week 1 · Exercise 5** guidelines.

---

## 1. Project Overview

Build a small but real chatbot server called **EASY-CHATGPT**.  
The project must be deliverable as a Docker-composable stack that anyone can clone, configure via `.env`, and run with a single command.

---

## 2. Architecture

| Layer | Technology | Notes |
|---|---|---|
| Backend | **FastAPI** (Python) | Acts as a proxy between the frontend and the LLM |
| Frontend | **Vanilla JS + HTML + CSS** | No frameworks (no React, Svelte, TypeScript) |
| LLM Access | OpenAI-compatible API | Base URL, API key, and model name configured via `.env` only |
| Containerisation | **Docker + docker-compose** | Single `docker compose up` to start everything |

**Key constraint:** The frontend never calls the LLM directly. All requests go through FastAPI.

---

## 3. Functional Requirements

### 3.1 Backend (FastAPI)

- **FR-B1** — Expose a REST endpoint that receives a chat message from the frontend.
- **FR-B2** — Forward the message (with conversation history) to the LLM using the OpenAI-compatible API.
- **FR-B3** — Return the LLM response to the frontend.
- **FR-B4** — Expose the current conversation context (messages sent to the model) and token usage via a dedicated endpoint, so the frontend can display them.
- **FR-B5** — All LLM configuration (`base_url`, `api_key`, `model`) must be read from environment variables / `.env` — **never hardcoded**.

### 3.2 Frontend (Vanilla JS + HTML + CSS)

- **FR-F1** — Render a chat window where the user can type messages and receive replies.
- **FR-F2** — Render model replies as **Markdown** (code blocks, lists, headings must be formatted, not raw text).
- **FR-F3** — Display a **context view** panel showing:
  - The full list of messages currently sent to the model (the growing context window).
  - Token usage returned by the LLM after each turn.
- **FR-F4** — Support **multi-turn conversation** (the full conversation history is sent to the model on each request).

### 3.3 Infrastructure

- **FR-I1** — The application must start with `docker compose up` with no extra manual steps.
- **FR-I2** — The service must be served on a port in the `666x` range (e.g. `6661`).
- **FR-I3** — A `.env` file (gitignored) holds all configuration. A `.env.example` with placeholder values must be committed.
- **FR-I4** — `.env` must be listed in `.gitignore` — secrets are never committed.
- **FR-I5** — A `README.md` must explain how to clone, configure `.env`, and run with Docker.

---

## 4. Implementation Versions (Incremental)

### Baseline (required)
- No streaming.
- FastAPI waits for the full LLM response before returning it to the frontend.
- The chat window shows the complete answer when it arrives.

### Advanced (required)
- **Streaming via Server-Sent Events (SSE)**.
- FastAPI streams the LLM response token by token and proxies the stream to the frontend.
- The chat window displays tokens as they arrive (typewriter effect).

### Best (optional)
- **Vision support**.
- If the configured model is vision-capable, allow the user to attach an image to a message and include it in the API request.

---

## 5. Optional Extras (for future weeks)

- User accounts / authentication.
- Persistent chat history (SQLite or plain JSON).

---

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Must run on a teammate's machine after clone → `.env` edit → `docker compose up` with no extra steps. |
| NFR-2 | No hardcoded secrets or model configuration anywhere in the codebase. |
| NFR-3 | No JavaScript frameworks — frontend is pure HTML/CSS/JS. |
| NFR-4 | Markdown rendering in the chat must handle at minimum: headings, bullet lists, numbered lists, bold/italic, and fenced code blocks. |

---

## 7. Deliverables

| # | Item |
|---|---|
| 1 | Working project under `week1/exercise5/` in the course repo |
| 2 | `docker-compose.yml` at the project root |
| 3 | `README.md` with run instructions |
| 4 | `.env.example` committed; `.env` gitignored |
| 5 | PDF submitted to Moodle (W1-Ex5) with: full name(s), repo link, screenshot of the running app (chat + context view), model used and why, one thing the agent got wrong and how it was fixed, one sentence on what you'd want next |

---

## 8. Project File Structure (suggested)

```
week1/exercise5/
├── backend/
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 9. Key Python Dependencies (Backend)

```
fastapi
uvicorn[standard]
openai          # OpenAI-compatible client
python-dotenv
httpx           # for async HTTP if needed
sse-starlette   # for SSE streaming (Advanced version)
```

---

## 10. Acceptance Criteria

- [ ] A multi-turn conversation can be held in the browser.
- [ ] The context view grows turn by turn and token counts are visible.
- [ ] A teammate can clone → set `.env` → `docker compose up` and reach the app on the first try.
- [ ] (Advanced) Tokens stream to the browser one by one.
- [ ] (Best) An image can be attached to a message and processed by a vision model.
