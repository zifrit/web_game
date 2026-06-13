FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/0.9.1/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

COPY pyproject.toml uv.lock* ./
RUN uv export --format requirements-txt --no-dev --no-hashes | uv pip install --system -r -

COPY . .

EXPOSE 8000
