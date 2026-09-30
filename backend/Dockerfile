# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM base AS prod
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --home /app --shell /usr/sbin/nologin app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    TIKTOKEN_CACHE_DIR=/opt/tiktoken

# tokenizer file build के समय ही download (runtime पर internet/writable FS की ज़रूरत नहीं)
RUN mkdir -p /opt/tiktoken /app/uploads \
 && python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')" \
 && chown -R app:app /opt/tiktoken /app

COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app app ./app

USER app
EXPOSE 8000
ENV WEB_CONCURRENCY=2
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY} --proxy-headers --forwarded-allow-ips='*' --no-server-header --timeout-graceful-shutdown 30"]
