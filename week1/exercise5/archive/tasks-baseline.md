# EASY-CHATGPT — Task Breakdown (Baseline Implementation)

> First implementation pass — **no streaming, no vision**.
> Tooling: **Python 3.12.3**, **uv** (environment management), **Docker + docker compose**.

---

## Phase 0 — Project Scaffolding

### - [x] Task 0.1 · Create the directory structure

Create every directory and placeholder file so the project shape is visible from the start:

```
week1/exercise5/
├── backend/
│   ├── main.py
│   ├── Dockerfile
│   └── pyproject.toml      # managed by uv
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.md          # already exists
├── tasks.md                 # this file
└── README.md
```

### - [x] Task 0.2 · Initialise the backend Python project with `uv`

1. `cd week1/exercise5/backend`
2. Run `uv init` to create `pyproject.toml`.
3. Set `requires-python = ">=3.12"` in `pyproject.toml`.
4. Add the runtime dependencies:
   ```bash
   uv add fastapi "uvicorn[standard]" openai python-dotenv
   ```
5. Verify `uv run python -c "import fastapi; print(fastapi.__version__)"` works.

> **Note:** `uv` will create its own `.venv` inside `backend/`. This venv is **not** committed —
> it is reproduced from `pyproject.toml` + `uv.lock` inside the Docker build.

### - [x] Task 0.3 · Create `.env.example` and `.gitignore`

`.env.example` (committed — placeholder values only):
```dotenv
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

`.gitignore` (at `week1/exercise5/` level):
```gitignore
# Secrets
.env

# Python
__pycache__/
*.pyc
.venv/

# uv
backend/.venv/
```

---

## Phase 1 — Backend (FastAPI)

### - [x] Task 1.1 · Application bootstrap (`main.py`)

Create the FastAPI app with the following characteristics:

- Import configuration from environment variables using `os.environ` (they will be injected by Docker from the `.env` file, so `python-dotenv` is only a local-dev convenience).
- Required env vars: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME`.
- Instantiate the OpenAI client **once** at startup, using `base_url` and `api_key` from env vars.
- Mount the `frontend/` directory as static files so the HTML/CSS/JS is served by FastAPI itself (single-container approach — simpler for this exercise).
- Serve `index.html` at the root path `/`.

### - [x] Task 1.2 · In-memory conversation store

Implement a simple module-level conversation store:

- A Python `list` holding the conversation messages in the OpenAI format:
  ```python
  messages: list[dict] = []
  # Each dict: {"role": "user" | "assistant" | "system", "content": "..."}
  ```
- A variable to accumulate token usage:
  ```python
  token_usage: dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
  ```
- This is in-memory only (resets on server restart). Persistence is a future-weeks extra.

### - [x] Task 1.3 · `POST /api/chat` endpoint

Implement the main chat endpoint:

1. **Request body** (JSON):
   ```json
   { "message": "Hello, how are you?" }
   ```
2. **Processing:**
   - Append `{"role": "user", "content": message}` to the conversation list.
   - Call `client.chat.completions.create(model=MODEL_NAME, messages=messages)` — **non-streaming** (`stream=False`).
   - Extract the assistant's reply from `response.choices[0].message.content`.
   - Append `{"role": "assistant", "content": reply}` to the conversation list.
   - Update `token_usage` with `response.usage.prompt_tokens`, `response.usage.completion_tokens`, `response.usage.total_tokens`.
3. **Response body** (JSON):
   ```json
   {
     "reply": "I'm doing well, thanks for asking!",
     "usage": {
       "prompt_tokens": 25,
       "completion_tokens": 12,
       "total_tokens": 37
     }
   }
   ```
4. **Error handling:**
   - If the OpenAI call fails, return an HTTP 502 with a JSON error message.
   - If `message` is empty or missing, return HTTP 422 (FastAPI's default validation).

### - [x] Task 1.4 · `GET /api/context` endpoint

Return the full current state so the frontend can render the context view:

**Response body** (JSON):
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "token_usage": {
    "prompt_tokens": 25,
    "completion_tokens": 12,
    "total_tokens": 37
  }
}
```

### - [x] Task 1.5 · `POST /api/reset` endpoint

Add a convenience endpoint to clear the conversation:

- Empty the `messages` list.
- Reset `token_usage` to zeros.
- Return `{"status": "ok"}`.

### - [x] Task 1.6 · Static file serving & CORS

- Use `FastAPI`'s `StaticFiles` to mount the `frontend/` directory at `/static`.
- Add a root route `GET /` that returns `FileResponse` pointing to `frontend/index.html`.
- Add CORS middleware allowing all origins during development (required because the frontend is served from the same origin, but useful if testing from a different port).

### - [x] Task 1.7 · Local run smoke test

Before containerising, verify it works locally:

```bash
cd week1/exercise5/backend
cp ../.env.example ../.env   # then edit with real values
uv run uvicorn main:app --host 0.0.0.0 --port 6661 --reload
```

- Open `http://localhost:6661` → should see the chat page.
- Open `http://localhost:6661/api/context` → should return empty messages array.

---

## Phase 2 — Frontend (Vanilla JS + HTML + CSS)

### - [x] Task 2.1 · HTML layout (`index.html`)

Create a single-page layout with two main panels:

1. **Chat panel** (left / main area):
   - A scrollable message container showing the conversation.
   - An input area at the bottom: a `<textarea>` (or `<input>`) + a "Send" button.
2. **Context view panel** (right sidebar or toggleable drawer):
   - A section showing the raw messages array (formatted as JSON or a styled list).
   - A token-usage summary showing prompt tokens, completion tokens, and total tokens.
   - A "Reset" button to clear the conversation.

Include the following in `<head>`:
- Link to `style.css`.
- A CDN link for **marked.js** (lightweight Markdown-to-HTML library) — this is a library, not a framework, and satisfies the "vanilla JS" constraint.
- A CDN link for **highlight.js** (for code-block syntax highlighting inside rendered Markdown) — optional but improves quality.
- `<script src="app.js" defer></script>`.

### - [x] Task 2.2 · CSS styling (`style.css`)

Implement a clean, functional chat UI:

- Use CSS custom properties (variables) for colour palette — dark theme preferred.
- Chat messages styled differently for user vs. assistant (e.g. alignment, background colour).
- The context panel should have a monospace font for the JSON/message dump.
- The token-usage section should be visually distinct (e.g. a small summary bar with counts).
- The layout should be responsive enough to work on a laptop screen (~1280px+). Full mobile responsiveness is not required.
- Rendered Markdown inside assistant messages should look good: proper code block backgrounds, list indentation, heading sizes.

### - [x] Task 2.3 · JavaScript logic (`app.js`)

Implement the following in plain JavaScript (no modules, no build step):

#### 2.3.1 · Send a message
- On "Send" button click (or Enter key press), read the input value.
- If empty, do nothing.
- Show the user's message immediately in the chat panel.
- Send a `POST` request to `/api/chat` with `{ "message": "..." }`.
- While waiting for the response, show a loading indicator (e.g. "..." or a spinner) in the assistant's message bubble.
- On response, render the assistant's reply as Markdown (using `marked.parse()`), replacing the loading indicator.
- Update the token-usage display with the values from the response.
- Clear the input field.
- Scroll the chat to the bottom.

#### 2.3.2 · Update the context view
- After each successful `/api/chat` response, fetch `GET /api/context`.
- Render the messages array in the context panel. Each message should show its `role` and `content` clearly.
- Update the token counters.

#### 2.3.3 · Reset conversation
- On "Reset" button click, send `POST /api/reset`.
- Clear the chat panel.
- Clear the context panel.
- Reset the token counters to zero.

#### 2.3.4 · Markdown rendering
- Use `marked.js` to convert the assistant's raw Markdown to HTML.
- Optionally integrate `highlight.js` for code-block syntax highlighting by setting `marked`'s `highlight` option.
- Sanitise the output if needed (marked has a `sanitize` option, or use DOMPurify).

#### 2.3.5 · Error handling
- If `/api/chat` returns an error (non-2xx), display the error message in the chat as a styled error bubble.
- If the network request itself fails (server down), show a "Could not reach the server" message.

### - [x] Task 2.4 · Frontend smoke test

With the backend running locally (Task 1.7):

1. Open `http://localhost:6661`.
2. Send a message → verify the reply appears as formatted Markdown.
3. Check the context panel updates with messages and token counts.
4. Send a second message → verify the context grows (multi-turn).
5. Click Reset → verify everything clears.

---

## Phase 3 — Docker & docker-compose

### - [x] Task 3.1 · Backend `Dockerfile`

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps)
RUN uv sync --frozen --no-dev

# Copy application code
COPY main.py .

# Copy frontend (served by FastAPI as static files)
COPY ../frontend ./frontend

# Expose the port
EXPOSE 6661

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6661"]
```

> **Note:** Since the frontend is served by FastAPI (not a separate server), we copy the
> `frontend/` directory into the backend container. The `docker-compose.yml` build context
> will be set to `week1/exercise5/` so relative paths work — the `Dockerfile` will need
> to be adjusted accordingly (see Task 3.2).

### - [x] Task 3.2 · `docker-compose.yml`

Create `week1/exercise5/docker-compose.yml`:

```yaml
services:
  app:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "6661:6661"
    env_file:
      - .env
    restart: unless-stopped
```

Key decisions:
- **Single service** — the backend serves both the API and the static frontend files.
- **Build context** is the exercise root (`.`) so the Dockerfile can `COPY` both `backend/` and `frontend/`.
- **`env_file: .env`** injects the LLM configuration into the container.
- **Port `6661`** is mapped host → container (exercise says pick a `666x` port).

### - [x] Task 3.3 · Adjust the Dockerfile for the build context

Since the build context is the exercise root (not `backend/`), update the `Dockerfile` paths:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first (layer caching)
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy backend code
COPY backend/main.py .

# Copy frontend
COPY frontend/ ./frontend/

EXPOSE 6661

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6661"]
```

### - [x] Task 3.4 · Docker build & run test

```bash
cd week1/exercise5
docker compose up --build
```

Verify:
- Container builds without errors.
- `http://localhost:6661` serves the chat UI.
- A message can be sent and a reply received.
- The context view updates.

### - [x] Task 3.5 · Clean-machine test

Simulate what a teammate would do:

```bash
# From a clean state
cd week1/exercise5
cp .env.example .env
# Edit .env with real values
docker compose up --build
# Open http://localhost:6661 → should just work
```

---

## Phase 4 — Documentation

### - [x] Task 4.1 · `README.md`

Write a `README.md` at `week1/exercise5/README.md` containing:

1. **Project title and one-line description.**
2. **Prerequisites:** Docker, docker compose.
3. **Quick start:**
   ```bash
   cp .env.example .env
   # Edit .env with your API key and model settings
   docker compose up --build
   # Open http://localhost:6661
   ```
4. **Configuration:** Table explaining each `.env` variable:
   | Variable | Description | Example |
   |---|---|---|
   | `OPENAI_API_KEY` | Your API key | `sk-...` |
   | `OPENAI_BASE_URL` | OpenAI-compatible endpoint | `https://api.openai.com/v1` |
   | `MODEL_NAME` | Model identifier to use | `gpt-4o-mini` |
5. **Local development** (without Docker):
   ```bash
   cd backend
   uv sync
   uv run uvicorn main:app --host 0.0.0.0 --port 6661 --reload
   ```
6. **Project structure** — brief description of each file.

### - [x] Task 4.2 · Verify `.gitignore` completeness

Ensure the following are excluded:
```gitignore
.env
__pycache__/
*.pyc
.venv/
backend/.venv/
```

---

## Task Summary & Order of Execution

| # | Task | Depends on | Covers |
|---|---|---|---|
| - [x] 0.1 | Create directory structure | — | Scaffolding |
| - [x] 0.2 | Init backend with `uv` | 0.1 | Scaffolding |
| - [x] 0.3 | `.env.example` + `.gitignore` | 0.1 | Config |
| - [x] 1.1 | FastAPI app bootstrap | 0.2 | FR-B5 |
| - [x] 1.2 | In-memory conversation store | 1.1 | FR-B2, FR-F4 |
| - [x] 1.3 | `POST /api/chat` endpoint | 1.2 | FR-B1, FR-B2, FR-B3 |
| - [x] 1.4 | `GET /api/context` endpoint | 1.2 | FR-B4, FR-F3 |
| - [x] 1.5 | `POST /api/reset` endpoint | 1.2 | Convenience |
| - [x] 1.6 | Static file serving + CORS | 1.1 | FR-F1 |
| - [x] 1.7 | Local smoke test | 1.1–1.6 | Verification |
| - [x] 2.1 | HTML layout | 0.1 | FR-F1, FR-F3 |
| - [x] 2.2 | CSS styling | 2.1 | FR-F1 |
| - [x] 2.3 | JavaScript logic | 2.1 | FR-F1, FR-F2, FR-F3, FR-F4 |
| - [x] 2.4 | Frontend smoke test | 1.7, 2.3 | Verification |
| - [x] 3.1 | Backend Dockerfile | 1.7 | FR-I1 |
| - [x] 3.2 | docker-compose.yml | 3.1 | FR-I1, FR-I2 |
| - [x] 3.3 | Adjust Dockerfile paths | 3.1, 3.2 | FR-I1 |
| - [x] 3.4 | Docker build & run test | 3.3 | FR-I1, NFR-1 |
| - [x] 3.5 | Clean-machine test | 3.4 | NFR-1 |
| - [x] 4.1 | README.md | 3.4 | FR-I5 |
| - [x] 4.2 | Verify .gitignore | 0.3 | FR-I4 |
