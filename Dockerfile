FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

EXPOSE $PORT

CMD ["sh", "-c", "uv run uvicorn rss_pipes.main:app --host 0.0.0.0 --port $PORT"]