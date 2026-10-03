FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY packages ./packages
COPY services ./services
RUN uv sync --locked --no-dev --no-editable \
    && useradd --create-home --uid 10001 appuser

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=3)"]
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

