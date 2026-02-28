FROM python:3.14-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency definition first (Docker layer caching)
COPY pyproject.toml .

# Copy source code
COPY src/ src/

# Install production dependencies with uv (no dev deps, no cache)
RUN uv pip install --system --no-cache -e "."

# Koyeb injects PORT env var; default to 8080
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn graphlit.api.main:app --host 0.0.0.0 --port ${PORT}"]
