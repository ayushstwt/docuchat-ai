# DocuChat AI

DocuChat AI is a full-stack, enterprise-grade "Chat with your PDFs" application featuring semantic retrieval-augmented generation (RAG), pgvector vector similarity search, real-time Server-Sent Events (SSE) streaming responses with verified page citations, JWT authentication with silent token refresh, audit logging, and light/dark theme modes.

---

## Features

- **Document Ingestion & Chunking**: Upload PDF documents up to 20MB with token-bounded sliding window chunking using `tiktoken`.
- **Vector Search with pgvector**: High-dimensional semantic embeddings stored in PostgreSQL with HNSW / Cosine distance querying.
- **Real-Time Token Streaming**: Server-Sent Events (SSE) endpoint providing responsive conversational AI streams with verified source citations.
- **Multi-Tenant Data Isolation**: Strict user-level access controls across documents, chunks, conversations, and audit logs.
- **Enterprise Security**: Argon2id password hashing, rotating JWT access & refresh tokens, security headers (HSTS, CSP, XSS-Protection, Sniff-Protection), and Rate Limiting.
- **Comprehensive Audit Trail**: Automatic user activity recording (`REGISTER`, `LOGIN`, `DOCUMENT_UPLOAD`, `DOCUMENT_DELETE`, `CONVERSATION_CREATE`, `CHAT_MESSAGE`).
- **Modern Responsive UI**: React 18 + Tailwind CSS frontend with dark mode persistence, interactive source inspection drawer, and drag-and-drop document uploads.

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database & ORM**: PostgreSQL 15+ with `pgvector`, SQLAlchemy 2.0 (AsyncIO), Alembic
- **AI & Embeddings**: Azure OpenAI (`gpt-4o` / `gpt-5-mini`, `text-embedding-3-small` / embeddings)
- **Tokenization & PDF Extraction**: `tiktoken` (`cl100k_base`), `pypdf`
- **Security & Validation**: Argon2 (`argon2-cffi`), PyJWT, Pydantic v2, SlowAPI (Rate Limiting)
- **Testing**: Pytest, Pytest-AsyncIO, HTTPX

### Frontend
- **Framework**: React 18, Vite, TypeScript
- **State & Server Cache**: Zustand, TanStack Query (React Query)
- **Styling & UI**: Tailwind CSS, Lucide React, Markdown Renderer (`react-markdown`, `remark-gfm`)
- **Routing**: React Router v6

---

## Project Architecture

```text
docuchat-ai/
├── backend/                  # FastAPI backend application
│   ├── alembic/              # Database migration scripts
│   ├── app/                  # Application source code
│   │   ├── constants/        # Enums and error codes
│   │   ├── core/             # Config, database, security, dependencies, logging
│   │   ├── exceptions/       # Custom exceptions and global handlers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Database access layer
│   │   ├── routers/          # FastAPI API route controllers
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── scripts/          # CLI helper scripts
│   │   └── services/         # Business logic (chat, document, pdf, auth, retrieval)
│   ├── tests/                # Automated pytest unit & integration test suite
│   ├── uploads/              # Local storage for uploaded PDF files
│   ├── .env.example          # Environment variables template
│   ├── alembic.ini           # Alembic configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React Vite frontend application
│   ├── src/                  # Application source code
│   │   ├── api/              # API clients and SSE stream consumer
│   │   ├── components/       # Reusable UI, layout, and chat components
│   │   ├── pages/            # View pages (Login, Register, Documents, Chat, Logs)
│   │   └── store/            # Zustand state stores
│   ├── .env.example          # Frontend environment variables template
│   ├── package.json          # Node dependencies & scripts
│   └── vite.config.ts        # Vite build configuration
├── scripts/                  # Cross-platform startup scripts (dev.ps1, dev.sh)
├── .github/workflows/        # Continuous Integration (CI) workflows
├── .gitignore                # Root gitignore
└── README.md                 # Project documentation
```

---

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ and `npm`
- **PostgreSQL**: 15+ with the `pgvector` extension enabled
- **Azure OpenAI**: Provisioned instance with chat completion and text embedding deployments

---

## Environment Variables Configuration

### Backend (`backend/.env`)

| Variable Name | Description | Example / Default |
|---|---|---|
| `APP_ENV` | Environment mode (`development`, `production`, `test`) | `development` |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/docuchat_db` |
| `JWT_SECRET` | Secret key for signing JWT tokens (min 32 chars in production) | `replace_with_a_secure_random_jwt_secret_key_minimum_32_chars` |
| `JWT_ACCESS_MINUTES` | Access token lifespan in minutes | `60` |
| `JWT_REFRESH_DAYS` | Refresh token lifespan in days | `7` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL | `https://your-resource-name.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API Key | `your_azure_openai_api_key` |
| `AZURE_OPENAI_API_VERSION`| Azure OpenAI API version | `2024-02-01` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Deployment name for chat completions | `gpt-4o` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment name for embeddings | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | Dimensionality of embedding model | `1536` |
| `UPLOAD_DIR` | Local directory for document file storage | `uploads` |
| `MAX_UPLOAD_MB` | Maximum allowed upload size in megabytes | `20` |
| `CORS_ORIGINS` | JSON list or comma-separated allowed web origins | `["http://localhost:5173","http://localhost:3000"]` |

### Frontend (`frontend/.env`)

| Variable Name | Description | Example / Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL pointing to the FastAPI backend API | `http://localhost:8000/api/v1` |

---

## Local Run Steps

### 1. Database Setup (PostgreSQL + pgvector)

Ensure PostgreSQL is running and create the database with the `pgvector` extension:

```sql
CREATE DATABASE docuchat_db;
\c docuchat_db
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux / Git Bash:
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create .env from template and configure credentials
cp .env.example .env

# 5. Run database migrations
python -m alembic upgrade head

# 6. Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

In a separate terminal:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Create .env from template
cp .env.example .env

# 4. Start Vite development server
npm run dev
```

### 4. Application URLs

- **Frontend Web UI**: [http://localhost:5173](http://localhost:5173)
- **Backend Swagger Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Backend Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## Quick Start (One Command)

Convenience dev scripts are available in `scripts/`:

- **Windows PowerShell**:
  ```powershell
  .\scripts\dev.ps1
  ```
- **Linux / macOS**:
  ```bash
  chmod +x ./scripts/dev.sh
  ./scripts/dev.sh
  ```

---

## API Overview

All API routes follow the standard envelope format `{ "status": "success", "message": "...", "data": ..., "metadata": ... }`:

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Register a new user account
- `POST /api/v1/auth/login` — Authenticate and receive JWT access & refresh tokens
- `POST /api/v1/auth/refresh` — Issue a new access token using a refresh token
- `GET /api/v1/auth/me` — Retrieve current authenticated user profile

### Documents (`/api/v1/documents`)
- `POST /api/v1/documents` — Upload and trigger asynchronous PDF ingestion
- `GET /api/v1/documents` — List user documents with pagination and status filters
- `GET /api/v1/documents/{id}` — Get document metadata, status, and chunk statistics
- `GET /api/v1/documents/{id}/file` — Download or preview original PDF file
- `DELETE /api/v1/documents/{id}` — Soft delete a document and associated vector chunks

### Conversations & Chat (`/api/v1/conversations`)
- `POST /api/v1/conversations` — Create a conversation linked to one or more documents
- `GET /api/v1/conversations` — List user conversations with pagination
- `GET /api/v1/conversations/{id}` — Get conversation details
- `PATCH /api/v1/conversations/{id}` — Rename conversation title
- `DELETE /api/v1/conversations/{id}` — Delete conversation and messages
- `GET /api/v1/conversations/{id}/messages` — Get message history
- `POST /api/v1/conversations/{id}/messages` — Stream chat question response via SSE (`sources`, `token`, `done`, `error`)

### Activity Logs (`/api/v1/activity-logs`)
- `GET /api/v1/activity-logs` — List chronological user audit trail events

---

## Testing & Quality Assurance

### Run Backend Tests
```bash
python -m pytest backend -q
```
*Executes all 38 unit, integration, security, and full end-to-end user lifecycle tests.*

### Run Frontend Lint & Build
```bash
cd frontend
npm run lint
npm run build
```

---

## Security Notes

1. **Never Commit Secrets**: `.env` files containing real API keys, connection strings, or JWT secrets must **never** be committed to version control. The repository `.gitignore` is configured to prevent accidental staging.
2. **Key Rotation**: If any production API key or secret is accidentally exposed, rotate it immediately in the Azure Portal or cloud provider console.
3. **JWT Secret Strength**: Always generate a high-entropy secret (at least 32 cryptographically random bytes) for `JWT_SECRET` in non-development environments.
4. **CORS Configuration**: Restrict `CORS_ORIGINS` to trusted domains in production environments.
