# DocuChat AI: Multi-Environment Setup (Local, Dev, Staging, Prod)

**Local:** Docker के बिना (uvicorn + local PostgreSQL + `npm run dev`)
**Dev / Staging / Prod:** Docker Compose, हर environment की अलग env file
**Principle:** *Build once, deploy anywhere*: एक ही Docker image हर environment में चलती है, फर्क सिर्फ env file का है।

---

## 1. Environment Matrix

| | **Local** | **Dev** | **Staging** | **Prod** |
|---|---|---|---|---|
| कैसे चलता है | बिना Docker | Docker Compose | Docker Compose | Docker Compose |
| `APP_ENV` | `local` | `dev` | `staging` | `prod` |
| Git branch / trigger | कोई भी | `develop` | `main` | tag `v1.2.3` |
| Frontend | Vite dev server `:5173` | nginx `:8080` | nginx + Caddy (HTTPS) | nginx + Caddy (HTTPS) |
| Backend | `uvicorn --reload` | uvicorn `--reload` (source mounted) | uvicorn multi-worker | uvicorn multi-worker |
| Database | local PostgreSQL + pgvector | container (`pgvector/pgvector:pg16`) | container | container (या managed DB, नीचे नोट देखें) |
| Image source | none | local build | registry (GHCR) से pull | registry से pull, **pinned version tag** |
| HTTPS | नहीं | नहीं | हाँ (Caddy, automatic) | हाँ (Caddy, automatic) |
| `LOG_LEVEL` / `LOG_FORMAT` | DEBUG / text | DEBUG / text | INFO / json | INFO / json |
| `ENABLE_DOCS` (/docs) | true | true | true | **false** |
| `WEB_CONCURRENCY` (workers) | 1 | 1 | 2 | 4 (CPU के हिसाब से) |
| Rate-limit storage | memory | memory | Redis | Redis |
| Azure OpenAI | dev key | dev key | **अलग** staging resource/key | **अलग** prod resource/key |
| JWT secret | कोई भी लंबी string | dev secret | अलग, 32+ chars | अलग, 48+ random chars |
| DB port बाहर खुला | localhost:5432 | `127.0.0.1:5433` | **नहीं** | **नहीं** |
| Hardening | - | - | resource limits | read-only FS, cap_drop, limits |

**Managed DB (Prod के लिए सुझाव):** Azure Database for PostgreSQL जैसी सेवा में pgvector चालू करके `DATABASE_URL` उसी की दें और prod compose से `db` service हटा दें। इसमें backups, HA और patching provider संभालता है।

---

## 2. Final Folder Structure

```
docuchat-ai/
├── README.md
├── .gitignore
├── scripts/
│   ├── compose.sh              # ./scripts/compose.sh <dev|staging|prod> <docker compose args>
│   └── backup-db.sh
├── deploy/
│   ├── docker-compose.yml      # base (सभी envs में साझा)
│   ├── docker-compose.dev.yml
│   ├── docker-compose.staging.yml
│   ├── docker-compose.prod.yml
│   ├── caddy/Caddyfile
│   ├── db/init.sql
│   └── env/
│       ├── dev.env.example     # commit होगा
│       ├── staging.env.example
│       ├── prod.env.example
│       └── (dev.env, staging.env, prod.env : असली values, gitignored)
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example            # LOCAL के लिए
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── .dockerignore
│   ├── .env.example            # LOCAL के लिए
│   └── ...
└── .github/workflows/
    ├── ci.yml
    └── publish-images.yml
```

**Request flow (staging/prod):**
```
Browser ─HTTPS─► Caddy :443 ─► web (nginx :8080) ─┬─► static React files
                                                   └─► /api/* ─► backend (uvicorn :8000) ─► db (pgvector)
                                                                          │                └► redis (rate limit)
                                                                          └─► Azure OpenAI
```
Frontend और API एक ही domain पर हैं (`/api/v1`), इसलिए **CORS की समस्या नहीं** और `VITE_API_BASE_URL=/api/v1` हर environment में एक ही रहता है।

---

## 3. Code Changes (Backend / Frontend)

### 3.1 `backend/app/core/config.py` (env-aware settings + validation)

```python
from enum import Enum
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    # Docker में env vars inject होते हैं (.env image में नहीं जाता); local में .env पढ़ी जाती है।
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: AppEnv = AppEnv.LOCAL
    log_level: str = "INFO"
    log_format: str = "text"  # "text" | "json"

    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 5

    jwt_secret: str
    jwt_access_minutes: int = 30
    jwt_refresh_days: int = 7

    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_chat_deployment: str
    azure_openai_embedding_deployment: str
    embedding_dimensions: int = 1536

    upload_dir: str = "./uploads"
    max_upload_mb: int = 20
    cors_origins: str = ""
    enable_docs: bool = True
    rate_limit_storage_url: str = "memory://"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_deployed(self) -> bool:
        return self.app_env in (AppEnv.STAGING, AppEnv.PROD)

    @model_validator(mode="after")
    def validate_for_environment(self) -> "Settings":
        """Staging/Prod में कमजोर या खतरनाक config होने पर app start ही नहीं होगा।"""
        if not self.is_deployed:
            return self
        problems: list[str] = []
        if len(self.jwt_secret) < 32 or "change" in self.jwt_secret.lower():
            problems.append("JWT_SECRET must be a random string of 32+ characters")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain '*'")
        if self.app_env == AppEnv.PROD and self.enable_docs:
            problems.append("ENABLE_DOCS must be false in prod")
        if self.app_env == AppEnv.PROD and self.rate_limit_storage_url.startswith("memory://"):
            problems.append("RATE_LIMIT_STORAGE_URL must point to Redis in prod")
        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 3.2 `main.py` में बदलाव (docs को env से control करना)
```python
settings = get_settings()
app = FastAPI(
    title="DocuChat AI",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)
```

### 3.3 Health endpoints (दो होने चाहिए)
- `GET /api/v1/health/live`: बिना DB के, सिर्फ "process ज़िंदा है" (Docker healthcheck यही इस्तेमाल करेगा)
- `GET /api/v1/health`: DB check सहित (readiness/monitoring के लिए)

### 3.4 `requirements.txt` में जोड़ें
`redis` (slowapi/limits के Redis storage के लिए)। Production के लिए versions **pin** करें (`pip freeze` या `pip-tools`)।

### 3.5 `frontend/vite.config.ts` (local dev proxy)
```ts
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: env.DEV_PROXY_TARGET || "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
```

---

## 4. Local Environment (Docker के बिना)

### `backend/.env.example`
```dotenv
# ===== LOCAL (Docker के बिना) =====
APP_ENV=local
LOG_LEVEL=DEBUG
LOG_FORMAT=text

DATABASE_URL=postgresql+asyncpg://docuchat:change_me@localhost:5432/docuchat
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5

JWT_SECRET=local-only-secret-change-me-at-least-32-chars
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7

AZURE_OPENAI_ENDPOINT=https://<your-dev-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=<supported version>
AZURE_OPENAI_CHAT_DEPLOYMENT=<chat deployment name>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<embedding deployment name>
EMBEDDING_DIMENSIONS=1536

UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=20
CORS_ORIGINS=http://localhost:5173
ENABLE_DOCS=true
RATE_LIMIT_STORAGE_URL=memory://
```

### `frontend/.env.example`
```dotenv
# ===== LOCAL =====
# API path relative रखें: local में Vite proxy, deployed envs में nginx proxy इसे संभालता है
VITE_API_BASE_URL=/api/v1
# सिर्फ vite.config.ts इस्तेमाल करता है (browser bundle में नहीं जाता)
DEV_PROXY_TARGET=http://localhost:8000
```

### Local run
```bash
# 1) Database (एक बार)
#    psql में: CREATE USER docuchat ...; CREATE DATABASE docuchat OWNER docuchat; CREATE EXTENSION vector;

# 2) Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # फिर values भरें
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3) Frontend (नया terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                                            # http://localhost:5173
```

---

## 5. Docker Files

### `backend/Dockerfile`
```dockerfile
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
```
*`--forwarded-allow-ips='*'` यहाँ सुरक्षित है क्योंकि backend का कोई port बाहर publish नहीं होता; सिर्फ nginx container इस तक पहुँचता है।*

### `backend/.dockerignore`
```
.venv
venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
.env
.env.*
uploads/*
tests
.git
```

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
```

### `frontend/.dockerignore`
```
node_modules
dist
.env
.env.*
.git
```

### `frontend/nginx.conf`
```nginx
# Caddy से X-Forwarded-Proto आए तो वही, वरना nginx का scheme
map $http_x_forwarded_proto $fwd_proto {
    default $http_x_forwarded_proto;
    ""      $scheme;
}

server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    client_max_body_size 25m;          # MAX_UPLOAD_MB (20) से थोड़ा ज़्यादा
    server_tokens off;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    # Google Fonts जैसी external चीज़ें इस्तेमाल करें तो CSP में allow करें
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $fwd_proto;
        proxy_set_header Connection        "";
        # SSE streaming के लिए ज़रूरी
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri /index.html;
        add_header Cache-Control "no-cache";
    }
}
```

---

## 6. Docker Compose Files

### `deploy/docker-compose.yml` (base)
```yaml
name: docuchat-${APP_ENV:-dev}

x-logging: &logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "5"

x-backend-build: &backend-build
  context: ../backend

x-backend-env: &backend-env
  APP_ENV: ${APP_ENV}
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  LOG_FORMAT: ${LOG_FORMAT:-json}
  DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
  DB_POOL_SIZE: ${DB_POOL_SIZE:-10}
  DB_MAX_OVERFLOW: ${DB_MAX_OVERFLOW:-10}
  JWT_SECRET: ${JWT_SECRET:?JWT_SECRET is required}
  JWT_ACCESS_MINUTES: ${JWT_ACCESS_MINUTES:-30}
  JWT_REFRESH_DAYS: ${JWT_REFRESH_DAYS:-7}
  AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT:?AZURE_OPENAI_ENDPOINT is required}
  AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY:?AZURE_OPENAI_API_KEY is required}
  AZURE_OPENAI_API_VERSION: ${AZURE_OPENAI_API_VERSION:?AZURE_OPENAI_API_VERSION is required}
  AZURE_OPENAI_CHAT_DEPLOYMENT: ${AZURE_OPENAI_CHAT_DEPLOYMENT:?required}
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT: ${AZURE_OPENAI_EMBEDDING_DEPLOYMENT:?required}
  EMBEDDING_DIMENSIONS: ${EMBEDDING_DIMENSIONS:-1536}
  UPLOAD_DIR: /app/uploads
  MAX_UPLOAD_MB: ${MAX_UPLOAD_MB:-20}
  CORS_ORIGINS: ${CORS_ORIGINS:-}
  ENABLE_DOCS: ${ENABLE_DOCS:-false}
  RATE_LIMIT_STORAGE_URL: ${RATE_LIMIT_STORAGE_URL:-memory://}
  WEB_CONCURRENCY: ${WEB_CONCURRENCY:-2}

services:
  db:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?POSTGRES_USER is required}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_DB: ${POSTGRES_DB:?POSTGRES_DB is required}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/00-init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks: [internal]
    logging: *logging

  # एक बार चलकर `alembic upgrade head` करता है, backend इसके पूरे होने का इंतज़ार करता है
  migrate:
    image: ${IMAGE_REGISTRY:-docuchat}/backend:${IMAGE_TAG:-local}
    build: *backend-build
    command: ["alembic", "upgrade", "head"]
    environment: *backend-env
    depends_on:
      db:
        condition: service_healthy
    restart: "no"
    networks: [internal]
    logging: *logging

  backend:
    image: ${IMAGE_REGISTRY:-docuchat}/backend:${IMAGE_TAG:-local}
    build: *backend-build
    environment: *backend-env
    volumes:
      - uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).status == 200 else 1)"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 20s
    restart: unless-stopped
    networks: [internal]
    logging: *logging

  web:
    image: ${IMAGE_REGISTRY:-docuchat}/web:${IMAGE_TAG:-local}
    build:
      context: ../frontend
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
      interval: 15s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks: [internal]
    logging: *logging

  # ---- सिर्फ staging/prod (--profile edge) ----
  redis:
    image: redis:7-alpine
    profiles: [edge]
    command: ["redis-server", "--appendonly", "no", "--maxmemory", "128mb", "--maxmemory-policy", "allkeys-lru"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks: [internal]
    logging: *logging

  caddy:
    image: caddy:2-alpine
    profiles: [edge]
    environment:
      DOMAIN: ${DOMAIN:?DOMAIN is required}
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      web:
        condition: service_healthy
    restart: unless-stopped
    networks: [internal]
    logging: *logging

volumes:
  pgdata:
  uploads:
  caddy_data:
  caddy_config:

networks:
  internal:
```

### `deploy/docker-compose.dev.yml`
```yaml
services:
  db:
    ports:
      - "127.0.0.1:${DB_PORT:-5433}:5432"   # DB tool से जुड़ने के लिए (local Postgres से टकराव नहीं)

  backend:
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    volumes:
      - ../backend/app:/app/app             # code बदलते ही auto reload
    ports:
      - "127.0.0.1:8000:8000"               # सीधे /docs देखने के लिए
    restart: "no"

  web:
    ports:
      - "${WEB_PORT:-8080}:8080"
    restart: "no"
```

### `deploy/docker-compose.staging.yml`
```yaml
services:
  backend:
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 768M

  db:
    deploy:
      resources:
        limits:
          memory: 768M
```

### `deploy/docker-compose.prod.yml`
```yaml
services:
  db:
    deploy:
      resources:
        limits:
          memory: 2G

  backend:
    depends_on:
      redis:
        condition: service_healthy
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1536M

  web:
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```
*Staging और Prod अलग servers पर चलाएँ (दोनों को port 80/443 चाहिए)।*

### `deploy/caddy/Caddyfile`
```
{$DOMAIN} {
	encode zstd gzip

	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		-Server
	}

	request_body {
		max_size 25MB
	}

	reverse_proxy web:8080 {
		flush_interval -1
	}
}
```
*`flush_interval -1` से SSE streaming बिना रुके browser तक पहुँचती है। HTTPS certificate Caddy अपने आप लेता है, बस domain का DNS server के IP पर होना चाहिए।*

### `deploy/db/init.sql`
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 7. Env Files (हर environment की अलग)

### `deploy/env/dev.env.example`
```dotenv
APP_ENV=dev
IMAGE_REGISTRY=docuchat
IMAGE_TAG=dev
WEB_PORT=8080
DB_PORT=5433

POSTGRES_USER=docuchat
POSTGRES_PASSWORD=dev_password_change_me
POSTGRES_DB=docuchat_dev

LOG_LEVEL=DEBUG
LOG_FORMAT=text
ENABLE_DOCS=true
WEB_CONCURRENCY=1
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
RATE_LIMIT_STORAGE_URL=memory://
CORS_ORIGINS=http://localhost:8080

JWT_SECRET=dev-secret-change-me-at-least-32-characters
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7

AZURE_OPENAI_ENDPOINT=https://<dev-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<dev key>
AZURE_OPENAI_API_VERSION=<supported version>
AZURE_OPENAI_CHAT_DEPLOYMENT=<chat deployment>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<embedding deployment>
EMBEDDING_DIMENSIONS=1536
MAX_UPLOAD_MB=20
```

### `deploy/env/staging.env.example`
```dotenv
APP_ENV=staging
DOMAIN=staging.example.com
IMAGE_REGISTRY=ghcr.io/<github-owner-lowercase>/docuchat
IMAGE_TAG=staging

POSTGRES_USER=docuchat
POSTGRES_PASSWORD=<strong random, सिर्फ letters/digits या URL-encoded>
POSTGRES_DB=docuchat_staging

LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_DOCS=true
WEB_CONCURRENCY=2
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=10
RATE_LIMIT_STORAGE_URL=redis://redis:6379/0
CORS_ORIGINS=https://staging.example.com

JWT_SECRET=<random 48+ chars, prod से अलग>
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7

AZURE_OPENAI_ENDPOINT=https://<staging-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<staging key>
AZURE_OPENAI_API_VERSION=<supported version>
AZURE_OPENAI_CHAT_DEPLOYMENT=<chat deployment>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<embedding deployment>
EMBEDDING_DIMENSIONS=1536
MAX_UPLOAD_MB=20
```

### `deploy/env/prod.env.example`
```dotenv
APP_ENV=prod
DOMAIN=app.example.com
IMAGE_REGISTRY=ghcr.io/<github-owner-lowercase>/docuchat
IMAGE_TAG=1.0.0                  # हमेशा pinned version, "latest" कभी नहीं

POSTGRES_USER=docuchat
POSTGRES_PASSWORD=<strong random, सिर्फ letters/digits या URL-encoded>
POSTGRES_DB=docuchat_prod

LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_DOCS=false
WEB_CONCURRENCY=4
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=10
RATE_LIMIT_STORAGE_URL=redis://redis:6379/0
CORS_ORIGINS=https://app.example.com

JWT_SECRET=<random 48+ chars, हर env में अलग>
JWT_ACCESS_MINUTES=15
JWT_REFRESH_DAYS=7

AZURE_OPENAI_ENDPOINT=https://<prod-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<prod key>
AZURE_OPENAI_API_VERSION=<supported version>
AZURE_OPENAI_CHAT_DEPLOYMENT=<chat deployment>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=<embedding deployment>
EMBEDDING_DIMENSIONS=1536
MAX_UPLOAD_MB=20
```

**Random secret बनाने का तरीका:** `openssl rand -base64 48` (URL में `POSTGRES_PASSWORD` के लिए `openssl rand -hex 24` बेहतर है, क्योंकि special characters `DATABASE_URL` तोड़ देते हैं)।

**ज़रूरी:** सभी environments में `EMBEDDING_DIMENSIONS` और embedding model एक जैसा होना चाहिए, क्योंकि DB column `vector(1536)` है।

### `.gitignore` में जोड़ें
```gitignore
# Deploy env files (असली secrets)
*.env
!*.env.example
!.env.example
deploy/env/*.env
backups/
```

---

## 8. Helper Scripts

### `scripts/compose.sh`
```bash
#!/usr/bin/env bash
# Usage: ./scripts/compose.sh <dev|staging|prod> <docker compose arguments...>
set -euo pipefail

ENV="${1:?usage: scripts/compose.sh <dev|staging|prod> <docker compose args...>}"
shift
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "$ENV" in
  dev|staging|prod) ;;
  *) echo "Unknown environment: $ENV (use dev, staging or prod)" >&2; exit 1 ;;
esac

[[ -f "$ROOT/deploy/env/$ENV.env" ]] || { echo "Missing deploy/env/$ENV.env (copy from $ENV.env.example)" >&2; exit 1; }

PROFILE=()
[[ "$ENV" != "dev" ]] && PROFILE=(--profile edge)

exec docker compose \
  --env-file "$ROOT/deploy/env/$ENV.env" \
  ${PROFILE[@]+"${PROFILE[@]}"} \
  -f "$ROOT/deploy/docker-compose.yml" \
  -f "$ROOT/deploy/docker-compose.$ENV.yml" \
  "$@"
```
`chmod +x scripts/*.sh` करें। Windows पर Git Bash/WSL इस्तेमाल करें, या नीचे की raw commands चलाएँ।

### `scripts/backup-db.sh`
```bash
#!/usr/bin/env bash
# Usage: ./scripts/backup-db.sh <staging|prod>   (cron से रोज़ चलाएँ)
set -euo pipefail
ENV="${1:?usage: scripts/backup-db.sh <staging|prod>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/backups"; mkdir -p "$OUT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

"$ROOT/scripts/compose.sh" "$ENV" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$OUT/docuchat-$ENV-$STAMP.dump"

find "$OUT" -name "docuchat-$ENV-*.dump" -mtime +14 -delete   # 14 दिन से पुराने हटाओ
echo "Backup saved: $OUT/docuchat-$ENV-$STAMP.dump"
```

---

## 9. CI/CD (GitHub Actions)

### `.github/workflows/publish-images.yml`
```yaml
name: publish-images

on:
  push:
    branches: [develop, main]
    tags: ["v*.*.*"]

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - { name: backend, context: backend }
          - { name: web, context: frontend }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/docuchat/${{ matrix.name }}
          tags: |
            type=sha,format=short
            type=raw,value=dev,enable=${{ github.ref == 'refs/heads/develop' }}
            type=raw,value=staging,enable=${{ github.ref == 'refs/heads/main' }}
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.context }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
*GHCR में owner का नाम lowercase होना चाहिए।*

### `ci.yml` में जोड़ें
हर PR पर: `pytest`, `npm run lint`, `npm run build`, और compose config की जाँच (placeholder values के साथ):
```yaml
      - name: Validate compose files
        run: |
          for e in dev staging prod; do
            cp deploy/env/$e.env.example deploy/env/$e.env
            profile=""; [ "$e" != "dev" ] && profile="--profile edge"
            docker compose --env-file deploy/env/$e.env $profile \
              -f deploy/docker-compose.yml -f deploy/docker-compose.$e.yml config -q
          done
```

---

## 10. Commands Cheat Sheet

| काम | Command |
|-----|---------|
| Local backend | `cd backend && uvicorn app.main:app --reload` |
| Local frontend | `cd frontend && npm run dev` |
| Dev शुरू | `./scripts/compose.sh dev up -d --build` |
| Dev logs | `./scripts/compose.sh dev logs -f backend` |
| Dev बंद | `./scripts/compose.sh dev down` |
| Config जाँच | `./scripts/compose.sh staging config -q` |
| Staging/Prod deploy | `./scripts/compose.sh prod pull && ./scripts/compose.sh prod up -d --remove-orphans` |
| Status | `./scripts/compose.sh prod ps` |
| सिर्फ migration | `./scripts/compose.sh prod run --rm migrate` |
| DB shell | `./scripts/compose.sh prod exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` |
| Backup | `./scripts/backup-db.sh prod` |
| Rollback | `.env` में पुराना `IMAGE_TAG` डालें, फिर deploy command दोबारा |

**बिना script (Windows PowerShell) के dev:**
```powershell
docker compose --env-file deploy/env/dev.env -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml up -d --build
```

---

## 11. Release Flow

```
feature/* ──PR──► develop ──► images "dev"      ──► Dev server
                     │
                     └─PR──► main ──► images "staging" ──► Staging server (test करें)
                                │
                                └─ git tag v1.2.0 ──► images "1.2.0" ──► Prod (IMAGE_TAG=1.2.0)
```

**Server पर पहली बार (Staging/Prod):**
1. Docker + Docker Compose plugin install करें, firewall में सिर्फ 22, 80, 443 खोलें
2. Domain का DNS A record server के IP पर
3. Repo clone करें (read-only deploy key से)
4. `cp deploy/env/prod.env.example deploy/env/prod.env` → असली values → `chmod 600 deploy/env/prod.env`
5. GHCR से pull के लिए `docker login ghcr.io` (Personal Access Token, सिर्फ `read:packages`)
6. `./scripts/compose.sh prod pull && ./scripts/compose.sh prod up -d`
7. `https://<domain>/api/v1/health` जाँचें
8. cron में daily `./scripts/backup-db.sh prod`

**GitHub में:** Settings → Environments में `staging` और `production` बनाएँ। Production पर *required reviewers* लगाएँ (अगर आगे auto-deploy job जोड़ें)।

---

## 12. Production Checklist

- [ ] `prod.env` git में नहीं है, server पर permission `600`
- [ ] Prod और Staging के JWT secret, DB password और Azure keys अलग-अलग हैं
- [ ] `IMAGE_TAG` pinned version है (`latest` नहीं)
- [ ] `ENABLE_DOCS=false` और `/docs` prod पर 404 देता है
- [ ] DB और Redis का कोई port बाहर publish नहीं है
- [ ] HTTPS चालू है और HTTP से HTTPS redirect हो रहा है
- [ ] Daily DB backup चल रहा है और एक बार **restore test** किया गया है
- [ ] `uploads` volume का भी backup है
- [ ] Container logs rotate होते हैं (json-file 10m x 5)
- [ ] Migration सिर्फ `migrate` service से होती है, app start पर नहीं
- [ ] Health endpoints `/health/live` और `/health` काम करते हैं
- [ ] Staging पर पूरा flow टेस्ट हुआ (upload, chat streaming, delete) फिर ही tag बना

**सीमाएँ (ईमानदारी से):**
- एक server पर Compose चलाने में deploy के दौरान कुछ सेकंड का downtime हो सकता है। Zero-downtime चाहिए तो load balancer के पीछे 2 servers या Kubernetes/Azure Container Apps देखें।
- PDF processing FastAPI `BackgroundTasks` में होती है। Container restart के बीच कोई document `PROCESSING` में अटक सकता है, इसलिए नीचे के prompt में startup पर ऐसे documents को `FAILED` करने का step है। बड़े scale पर job queue (Celery/ARQ/RQ) बेहतर होगी।
- Uploaded PDFs local volume में हैं। कई servers पर scale करने के लिए Azure Blob Storage पर जाना होगा।

---

## 13. README में डालने वाला Section (ready to paste)

````markdown
## Environments

DocuChat AI runs in four environments. Local runs without Docker; Dev, Staging and Prod use Docker Compose with one env file each. The same Docker images are used everywhere; only the env file differs.

| | Local | Dev | Staging | Prod |
|---|---|---|---|---|
| Runs with | uvicorn + npm | Docker Compose | Docker Compose | Docker Compose |
| `APP_ENV` | `local` | `dev` | `staging` | `prod` |
| Config file | `backend/.env`, `frontend/.env` | `deploy/env/dev.env` | `deploy/env/staging.env` | `deploy/env/prod.env` |
| URL | http://localhost:5173 | http://localhost:8080 | https://staging.example.com | https://app.example.com |
| API docs (`/docs`) | on | on | on | **off** |
| HTTPS | no | no | yes (Caddy) | yes (Caddy) |
| Branch / trigger | any | `develop` | `main` | tag `vX.Y.Z` |

### Architecture (Dev, Staging, Prod)

Browser → Caddy (HTTPS, staging/prod only) → nginx (serves the React app and proxies `/api/*`) → FastAPI backend → PostgreSQL + pgvector. Redis is used for rate limiting in staging/prod. The frontend and the API share one origin, so no CORS setup is needed and `VITE_API_BASE_URL=/api/v1` is identical in every environment.

### Run locally (no Docker)

Prerequisites: Python 3.11+, Node.js 20+, PostgreSQL 15+ with the pgvector extension, an Azure OpenAI resource.

    # Database (once)
    CREATE USER docuchat WITH PASSWORD 'change_me';
    CREATE DATABASE docuchat OWNER docuchat;
    -- connect to docuchat as a superuser:
    CREATE EXTENSION IF NOT EXISTS vector;

    # Backend
    cd backend
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env                                # fill in values
    alembic upgrade head
    uvicorn app.main:app --reload --port 8000

    # Frontend
    cd frontend
    npm install
    cp .env.example .env
    npm run dev

Backend docs: http://localhost:8000/docs. Frontend: http://localhost:5173.

### Run Dev / Staging / Prod with Docker Compose

    cp deploy/env/dev.env.example deploy/env/dev.env    # then fill in values
    ./scripts/compose.sh dev up -d --build              # http://localhost:8080

Staging and Prod pull prebuilt images from GHCR:

    cp deploy/env/prod.env.example deploy/env/prod.env
    chmod 600 deploy/env/prod.env
    ./scripts/compose.sh prod pull
    ./scripts/compose.sh prod up -d --remove-orphans
    ./scripts/compose.sh prod ps

Migrations run automatically through the one-shot `migrate` service before the backend starts.

Useful commands: `logs -f backend`, `down`, `config -q` (validate), `run --rm migrate`, and `./scripts/backup-db.sh prod`.

### Environment variables

Local variables live in `backend/.env` and `frontend/.env`. Docker environments use `deploy/env/<env>.env`. Never commit real env files; only `*.example` files are tracked.

| Variable | Description | Local | Dev | Staging | Prod |
|---|---|---|---|---|---|
| `APP_ENV` | Environment name | local | dev | staging | prod |
| `LOG_LEVEL` | Log verbosity | DEBUG | DEBUG | INFO | INFO |
| `LOG_FORMAT` | `text` or `json` | text | text | json | json |
| `DATABASE_URL` | Async SQLAlchemy URL (built by Compose for Docker envs) | localhost | db container | db container | db container / managed |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Database container credentials | n/a | required | required | required |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | Connection pool sizing | 5 / 5 | 5 / 5 | 10 / 10 | 10 / 10 |
| `JWT_SECRET` | Token signing secret (32+ chars; unique per environment) | any | dev value | random | random 48+ |
| `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS` | Token lifetimes | 30 / 7 | 30 / 7 | 30 / 7 | 15 / 7 |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | dev | dev | staging | prod |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key (separate per environment) | dev | dev | staging | prod |
| `AZURE_OPENAI_API_VERSION` | API version supported by your resource | set | set | set | set |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment name | set | set | set | set |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name | set | set | set | set |
| `EMBEDDING_DIMENSIONS` | Must match the `vector(N)` column (1536) | 1536 | 1536 | 1536 | 1536 |
| `UPLOAD_DIR` | PDF storage path (`/app/uploads` volume in Docker) | ./uploads | volume | volume | volume |
| `MAX_UPLOAD_MB` | Upload size limit | 20 | 20 | 20 | 20 |
| `CORS_ORIGINS` | Allowed origins (no `*` in staging/prod) | :5173 | :8080 | https domain | https domain |
| `ENABLE_DOCS` | Expose `/docs` (must be false in prod) | true | true | true | false |
| `RATE_LIMIT_STORAGE_URL` | `memory://` or Redis URL (Redis required in prod) | memory | memory | redis | redis |
| `WEB_CONCURRENCY` | Uvicorn worker count | 1 | 1 | 2 | 4 |
| `DOMAIN` | Public domain for HTTPS (Caddy) | n/a | n/a | required | required |
| `IMAGE_REGISTRY`, `IMAGE_TAG` | Image location and version | n/a | local | `staging` | pinned `X.Y.Z` |
| `VITE_API_BASE_URL` | Frontend API base path | /api/v1 | /api/v1 | /api/v1 | /api/v1 |
| `DEV_PROXY_TARGET` | Vite dev proxy target (local only) | http://localhost:8000 | n/a | n/a | n/a |

The backend refuses to start in staging/prod if `JWT_SECRET` is weak, `CORS_ORIGINS` contains `*`, or (prod) `ENABLE_DOCS` is true or rate limiting is not backed by Redis.

### Release flow

Feature branches merge into `develop` (deploys to Dev), `develop` merges into `main` (Staging), and a `vX.Y.Z` tag publishes versioned images that Prod pins via `IMAGE_TAG`. GitHub Actions builds and pushes images to GHCR (`publish-images.yml`) and runs tests and lint (`ci.yml`).

To roll back, set the previous `IMAGE_TAG` in the environment file and run the deploy commands again. Write migrations to be backward compatible so a rollback does not require a database downgrade.

### Backups

    ./scripts/backup-db.sh prod        # schedule daily with cron; keeps 14 days
    # restore:
    ./scripts/compose.sh prod exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < backups/<file>.dump

Also back up the `uploads` Docker volume (PDF files).

### Security notes

- Never commit `.env` or `deploy/env/*.env`. If a secret leaks, rotate it immediately.
- Use different JWT secrets, database passwords and Azure keys in every environment.
- DB and Redis ports are not exposed in staging/prod; only Caddy publishes 80/443.
- Prod containers run as a non-root user with a read-only filesystem and dropped capabilities.
- Keep `.env` files at `chmod 600` on servers.

### Troubleshooting

| Problem | Fix |
|---|---|
| `variable is not set` on compose | Fill the missing key in `deploy/env/<env>.env` |
| Backend exits with "Invalid configuration" | Fix the listed staging/prod setting (JWT secret, CORS, docs, Redis) |
| `extension "vector" is not available` | Use the `pgvector/pgvector` image, or install pgvector locally / allow it on the managed DB |
| Migration fails on startup | `./scripts/compose.sh <env> logs migrate` |
| Chat streaming freezes or arrives in one chunk | Check `proxy_buffering off` (nginx) and `flush_interval -1` (Caddy) |
| Upload returns 413 | Raise `MAX_UPLOAD_MB` and the `client_max_body_size` / Caddy `max_size` limits together |
| Password with special characters breaks `DATABASE_URL` | Use a hex password (`openssl rand -hex 24`) or URL-encode it |
````

---

## 14. AI Coding Tool के लिए Prompt

*इस file को (`DocuChat_Multi_Env_Setup.md`) अपने Claude Code / Cursor में attach करें और नीचे का prompt paste करें।*

```text
I have attached DocuChat_Multi_Env_Setup.md. Apply it to the existing `docuchat-ai` monorepo (backend/ FastAPI, frontend/ React). Use the exact contents from the guide for the files it lists; adapt only where the existing code requires it. Do not push anything to git.

PART A: Infrastructure files (create exactly as in the guide)
1. backend/Dockerfile, backend/.dockerignore, frontend/Dockerfile, frontend/.dockerignore, frontend/nginx.conf.
2. deploy/docker-compose.yml, docker-compose.dev.yml, docker-compose.staging.yml, docker-compose.prod.yml, deploy/caddy/Caddyfile, deploy/db/init.sql.
3. deploy/env/dev.env.example, staging.env.example, prod.env.example.
4. scripts/compose.sh and scripts/backup-db.sh (make them executable).
5. .github/workflows/publish-images.yml, and extend the existing ci.yml with the compose validation step.
6. Update .gitignore with the deploy env rules.

PART B: Backend code changes
1. core/config.py: implement AppEnv, all new settings (log_level, log_format, db_pool_size, db_max_overflow, enable_docs, rate_limit_storage_url, cors_origin_list) and the model_validator that fails startup in staging/prod for a weak JWT secret, wildcard CORS, ENABLE_DOCS=true in prod, or memory rate limiting in prod. Use these settings everywhere (engine pool sizes, CORS middleware, upload dir).
2. main.py: disable /docs, /redoc and /openapi.json when ENABLE_DOCS is false.
3. core/logging.py: support LOG_FORMAT=json (one JSON object per line with timestamp, level, logger, message, request id, exception info) and text; honor LOG_LEVEL. Never log secrets.
4. Add GET /api/v1/health/live (no DB access, always 200 while the process is up) next to the existing /api/v1/health (with DB check). Both use the standard ApiResponse envelope.
5. Rate limiting (slowapi): use settings.rate_limit_storage_url as the storage URI (memory:// or redis://). The 429 response must still use the standard error envelope with E015. Add `redis` to requirements.txt and pin all versions in requirements.txt.
6. Startup recovery: on app startup, find documents stuck in PROCESSING for more than 15 minutes (updated_on older than that) and mark them FAILED with error_code E999, with a WARNING log listing their ids. Keep it a single bulk update that sets updated_on explicitly, and never let a failure here stop the app from starting.
7. Make sure the app never runs migrations on startup (only the `migrate` service does), and that it works when the filesystem is read-only except for UPLOAD_DIR and /tmp.
8. Add tests: settings validation for each env (local passes with weak values; staging/prod fail for each bad setting; prod passes with good values), docs disabled when ENABLE_DOCS=false, health/live works without a database, JSON log formatter output.

PART C: Frontend changes
1. vite.config.ts: dev proxy for /api using DEV_PROXY_TARGET (default http://localhost:8000), as in the guide.
2. Set frontend/.env.example to VITE_API_BASE_URL=/api/v1 and DEV_PROXY_TARGET. Confirm the axios client and the SSE stream helper both build URLs from VITE_API_BASE_URL and work with a relative base path (also when opening the PDF file endpoint via blob fetch).
3. Ensure nothing in the frontend depends on an absolute backend URL or on environment-specific build arguments (one build must work in every environment).

PART D: README.md
Add/replace the "Environments" documentation using the README section from the guide (section 13): the environment table, architecture, local run, Docker run for dev/staging/prod, the complete environment variables table, release flow, backups, security notes and troubleshooting. Keep the rest of the README (overview, features, API list) and update any outdated instructions so the README matches what the repo really does. Also update backend/README.md and frontend/README.md with a short "Environment configuration" note pointing to the root README.

PART E: Verification (run and report results)
1. `pytest -q` in backend and `npm run lint` + `npm run build` in frontend.
2. `docker compose config -q` for dev, staging and prod using the *.env.example files copied to temporary .env files (delete the temporary files afterwards).
3. If Docker is available: build both images, start the dev stack with dummy Azure values, and check that migrate completes, /api/v1/health/live and /api/v1/health return 200 through http://localhost:8080, and an SSE endpoint is not buffered by nginx (describe how you checked). If Docker is not available, say so and skip.
4. Run a secrets check: no real secrets in tracked files, no deploy/env/*.env tracked, `git ls-files | grep -E "\.env$"` prints nothing.

Finish with a summary table of every file created/changed, any assumption you made, and a short manual checklist for the first deploy of Staging and Prod (DNS, Docker install, GHCR login, env file with chmod 600, first deploy, health check, backup cron).
```

---

## 15. Quick Tips

1. **पहले Dev पर चलाएँ**, फिर Staging, फिर Prod। हर बार वही image आगे बढ़ती है, rebuild नहीं होती।
2. **Prod की `.env` कभी laptop या chat में paste न करें।** सीधे server पर बनाएँ।
3. **Azure quota:** Prod के लिए अलग Azure OpenAI resource रखें ताकि dev की testing prod का quota न खाए।
4. **Password में `@`, `:`, `/` जैसे characters** `DATABASE_URL` तोड़ देते हैं, इसलिए hex password इस्तेमाल करें।
5. Docker commands आपके OS/version पर थोड़े अलग हो सकते हैं। कोई command fail हो तो `docker compose version` और error यहाँ भेज दें।
