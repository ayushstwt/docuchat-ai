# DocuChat AI

DocuChat AI is a full-stack, chat-with-your-PDFs web application featuring semantic search, vector embeddings, streaming chat responses, user authentication, and activity logging.

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ and npm / pnpm
- **PostgreSQL**: 15+ with the `pgvector` extension installed locally
- **Azure OpenAI**: Provisioned instance with chat completion and text embedding deployments

## Project Architecture

```text
docuchat-ai/
├── backend/      # FastAPI, SQLAlchemy 2.0 async, Alembic, pgvector, Azure OpenAI
├── frontend/     # React, Vite, TypeScript, Tailwind CSS, TanStack Query
└── README.md
```

## Running the Application

### 1. Backend Setup

Detailed instructions will be provided in subsequent steps.

```bash
# Setup virtual environment and install dependencies
cd backend
python -m venv .venv
# Activate virtual environment
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload
```

### 2. Frontend Setup

Detailed instructions will be configured during frontend initialization (Prompt 11).

```bash
cd frontend
npm install
npm run dev
```
