FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first (layer caching)
# Note: Paths are relative to the build context (which is week1/exercise5/)
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies (no dev deps)
RUN uv sync --frozen --no-dev

# Copy backend code
COPY backend/main.py .

# Copy frontend (served by FastAPI as static files)
COPY frontend/ ./frontend/

EXPOSE 6661

# Note: We run main:app inside the container, but since we copied it to /app
# and WORKDIR is /app, it will find it.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6661"]
