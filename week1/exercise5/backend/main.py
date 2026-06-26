"""
EASY-CHATGPT — FastAPI backend.

Acts as a proxy between the vanilla-JS frontend and an OpenAI-compatible LLM.
All LLM configuration is read from environment variables (injected by Docker
via .env, or loaded locally with python-dotenv for development).
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load .env file when running locally (Docker injects env vars directly).
# The .env is expected one level up from backend/ (at the exercise5/ root).
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")

if not OPENAI_API_KEY:
    logging.warning(
        "OPENAI_API_KEY is not set. LLM calls will fail until a valid key is provided."
    )

# ---------------------------------------------------------------------------
# OpenAI client (instantiated once)
# ---------------------------------------------------------------------------

client = OpenAI(
    api_key=OPENAI_API_KEY or "sk-not-configured",
    base_url=OPENAI_BASE_URL,
)

# ---------------------------------------------------------------------------
# In-memory conversation store (Task 1.2)
# ---------------------------------------------------------------------------

messages: list[dict] = []

token_usage: dict = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
}

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="EASY-CHATGPT",
    description="A simple chatbot server that proxies an OpenAI-compatible LLM.",
    version="0.1.0",
)

# CORS — allow all origins during development (Task 1.6)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str = Field(..., min_length=1, description="The user's message text")


class UsageInfo(BaseModel):
    """Token usage returned by the LLM."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Response sent back to the frontend after an LLM call."""
    reply: str
    usage: UsageInfo


class ContextResponse(BaseModel):
    """Full conversation context and accumulated token usage."""
    messages: list[dict]
    token_usage: UsageInfo


class ResetResponse(BaseModel):
    """Acknowledgement after clearing the conversation."""
    status: str

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Receive a user message, forward the full conversation to the LLM,
    and return the assistant's reply with token usage.  (Task 1.3)
    """
    # Append the user message to the conversation history
    messages.append({"role": "user", "content": request.message})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=False,
        )
    except OpenAIError as exc:
        # Roll back the user message so the conversation stays consistent
        messages.pop()
        raise HTTPException(
            status_code=502,
            detail=f"LLM request failed: {exc}",
        ) from exc

    # Extract the assistant's reply
    reply = response.choices[0].message.content or ""

    # Append the assistant reply to the conversation history
    messages.append({"role": "assistant", "content": reply})

    # Update accumulated token usage
    if response.usage:
        token_usage["prompt_tokens"] += response.usage.prompt_tokens
        token_usage["completion_tokens"] += response.usage.completion_tokens
        token_usage["total_tokens"] += response.usage.total_tokens

    return ChatResponse(
        reply=reply,
        usage=UsageInfo(
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"],
        ),
    )


@app.get("/api/context", response_model=ContextResponse)
async def get_context():
    """
    Return the full conversation history and accumulated token usage
    so the frontend can render the context view.  (Task 1.4)
    """
    return ContextResponse(
        messages=messages,
        token_usage=UsageInfo(**token_usage),
    )


@app.post("/api/reset", response_model=ResetResponse)
async def reset():
    """
    Clear the conversation history and reset token counters.  (Task 1.5)
    """
    messages.clear()
    token_usage["prompt_tokens"] = 0
    token_usage["completion_tokens"] = 0
    token_usage["total_tokens"] = 0
    return ResetResponse(status="ok")


# ---------------------------------------------------------------------------
# Static file serving (Task 1.6)
# ---------------------------------------------------------------------------

# Resolve the frontend directory relative to this file.
# When running locally: backend/main.py → ../frontend
# When running in Docker: /app/main.py → /app/frontend
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if not FRONTEND_DIR.is_dir():
    # Fallback for local dev where frontend/ is a sibling of backend/
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
async def serve_index():
    """Serve the frontend index.html at the root path."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static assets (CSS, JS) — must come after explicit routes so it
# doesn't shadow /api/* or /.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
