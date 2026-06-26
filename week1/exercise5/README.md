# EASY-CHATGPT

A simple, fast, and fully containerised chatbot server acting as a proxy between a vanilla JavaScript frontend and an OpenAI-compatible LLM.

Built for **Week 1 · Exercise 5** (Baseline Implementation).

## Features

- **FastAPI Backend:** Proxies all LLM requests, hiding API keys and configurations from the client.
- **Vanilla JS Frontend:** No heavy frameworks (no React, Svelte, etc.). Uses `marked.js` and `highlight.js` for beautiful Markdown and code rendering.
- **Context View:** A dedicated sidebar showing exact token usage (Prompt, Completion, Total) and the raw message history sent to the model on every turn.
- **Single Container:** The backend serves the REST API and mounts the frontend as static files, meaning one `docker compose up` starts the entire stack instantly.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. **Clone the repository** and navigate to this directory:
   ```bash
   cd week1/exercise5
   ```

2. **Configure your environment:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your specific model configuration.

3. **Run with Docker:**
   ```bash
   docker compose up --build
   ```

4. **Access the Chat:**
   Open your browser and navigate to: [http://localhost:6661](http://localhost:6661)

## Configuration (`.env`)

All settings are read from the `.env` file (which is gitignored).

| Variable | Description | Example |
|---|---|---|
| `OPENAI_API_KEY` | Your LLM provider API key | `sk-your-key-here` |
| `OPENAI_BASE_URL` | The endpoint for the API | `https://api.openai.com/v1` (or `http://localhost:11434/v1` for local Ollama) |
| `MODEL_NAME` | The exact model identifier | `gpt-4o-mini` (or `ministral-3` locally) |

> **Note:** If using a local model on the host machine (like Ollama) from within Docker on Linux, use `http://host.docker.internal:11434/v1` as the base URL. (The `docker-compose.yml` is already configured to map this host).

## Local Development (Without Docker)

If you prefer to run the application directly on your machine:

1. Ensure you have Python 3.12+ and [uv](https://docs.astral.sh/uv/) installed.
2. Navigate to the backend directory and run the server:
   ```bash
   cd backend
   uv run uvicorn main:app --host 0.0.0.0 --port 6661 --reload
   ```

## Project Structure

```text
week1/exercise5/
├── backend/
│   ├── main.py            # FastAPI application (proxy + static file server)
│   ├── Dockerfile         # Container build instructions for the backend
│   └── pyproject.toml     # Python dependencies managed by `uv`
├── frontend/
│   ├── index.html         # Main UI layout
│   ├── style.css          # Dark-themed custom styling
│   └── app.js             # Vanilla JS logic (chat, context updating, markdown)
├── docker-compose.yml     # Orchestrates the container on port 6661
├── .env.example           # Template for environment variables
└── tasks.md               # Task breakdown and progression tracking
```
