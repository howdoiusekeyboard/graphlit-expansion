FROM python:3.14-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency definition + README (required by PEP 621 metadata)
COPY pyproject.toml README.md ./

# Copy source code
COPY src/ src/

# Install production dependencies with uv (no dev deps, no cache)
RUN uv pip install --system --no-cache .

# Create non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

# Koyeb injects PORT env var; default to 8080
ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,sys,urllib.request;sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8080\")}/health',timeout=3).status==200 else 1)"

CMD ["sh", "-c", "uvicorn graphlit.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
