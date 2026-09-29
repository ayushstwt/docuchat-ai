# DocuChat AI

DocuChat AI is a full-stack, chat-with-your-PDFs web application featuring semantic search, vector embeddings, streaming chat responses with source citations, JWT authentication, and activity logging.

---

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ and npm / pnpm
- **PostgreSQL**: 15+ with the `pgvector` extension installed locally
- **Azure OpenAI**: Provisioned instance with chat completion (e.g. `gpt-4o`) and text embedding (e.g. `text-embedding-3-small`, 1536 dims) deployments

---

## Project Architecture

```text
docuchat-ai/
├── backend/      # FastAPI, SQLAlchemy 2.0 async, Alembic, pgvector, Azure OpenAI
├── frontend/     # React, Vite, TypeScript, Tailwind CSS, TanStack Query
└── README.md
```

---

## Backend Setup & Instructions

### 1. Virtual Environment & Dependencies

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database & Migrations

Ensure PostgreSQL is running and has the `vector` extension enabled:
```sql
CREATE DATABASE docuchat;
\c docuchat
CREATE EXTENSION IF NOT EXISTS vector;
```

Run Alembic database migrations:
```bash
alembic upgrade head
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env` in `backend/` and update the required values:

| Variable | Description | Example / Default |
|---|---|---|
| `APP_ENV` | Application environment (`development` or `production`) | `development` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/docuchat` |
| `JWT_SECRET` | Secret key for signing JWT tokens (min 32 chars) | `<secure_random_string_32_chars_min>` |
| `JWT_ACCESS_MINUTES` | Access token lifespan in minutes | `60` |
| `JWT_REFRESH_DAYS` | Refresh token lifespan in days | `7` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint URL | `https://<resource-name>.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | `<your-azure-api-key>` |
| `AZURE_OPENAI_API_VERSION`| Azure OpenAI API version | `2024-02-01` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat completion model deployment name | `gpt-4o` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding model deployment name | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | Dimensionality of embedding vectors | `1536` |
| `UPLOAD_DIR` | Local directory for storing uploaded PDF files | `uploads` |
| `MAX_UPLOAD_MB` | Maximum allowed upload size in megabytes | `20` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated or JSON list) | `http://localhost:5173,http://localhost:3000` |

### 4. Running the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Running the Test Suite

```bash
pytest
```

---

## Backend API Endpoints Reference (`/api/v1`)

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| **Health** | | | |
| `GET` | `/api/v1/health` | Health check endpoint | `200 OK` |
| **Authentication** | | | |
| `POST` | `/api/v1/auth/register` | Register new user account | `201 Created` |
| `POST` | `/api/v1/auth/login` | Login user & issue access + refresh tokens | `200 OK` |
| `POST` | `/api/v1/auth/refresh` | Refresh access token using refresh token | `200 OK` |
| `GET` | `/api/v1/auth/me` | Retrieve current authenticated user profile | `200 OK` |
| **Documents** | | | |
| `POST` | `/api/v1/documents` | Upload PDF & start background ingestion | `201 Created` (`Location` header) |
| `GET` | `/api/v1/documents` | Paginated list of owned documents (with `status` filter) | `200 OK` |
| `GET` | `/api/v1/documents/{id}` | Retrieve document details & processing status | `200 OK` |
| `GET` | `/api/v1/documents/{id}/file` | Download or preview original PDF file | `200 OK` |
| `DELETE` | `/api/v1/documents/{id}` | Soft delete document and its chunks | `204 No Content` |
| **Conversations & Messages** | | | |
| `POST` | `/api/v1/conversations` | Create conversation with READY documents | `201 Created` (`Location` header) |
| `GET` | `/api/v1/conversations` | Paginated list of owned conversations | `200 OK` |
| `GET` | `/api/v1/conversations/{id}` | Retrieve conversation details & attached document IDs | `200 OK` |
| `PATCH` | `/api/v1/conversations/{id}` | Rename conversation title | `200 OK` |
| `DELETE` | `/api/v1/conversations/{id}` | Soft delete conversation | `204 No Content` |
| `GET` | `/api/v1/conversations/{id}/messages` | Paginated message history for a conversation | `200 OK` |
| `POST` | `/api/v1/conversations/{id}/messages` | Send user message & stream RAG response tokens via SSE | `200 OK` (`text/event-stream`) |
| **Activity Logs** | | | |
| `GET` | `/api/v1/activity-logs` | Paginated list of current user's activity logs | `200 OK` |
