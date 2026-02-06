# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends unixodbc

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

WORKDIR /app
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd -ms /bin/bash mcpuser \
    && chmod +x /app/src/vector/entrypoint.sh

USER mcpuser

ENTRYPOINT ["/app/src/vector/entrypoint.sh"]
CMD ["actian-mcp-server", "--dbms", "vector", "--transport", "http", "--conf-file", "/app/src/vector/conf.json"]
