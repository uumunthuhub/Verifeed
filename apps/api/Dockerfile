FROM python:3.12-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (for layer caching)
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Copy application source and configuration
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
