# DocuChat AI

DocuChat AI is a full-stack, enterprise-grade "Chat with your PDFs" application featuring semantic retrieval augmented generation (RAG), pgvector similarity embeddings, real-time SSE streaming responses with verified page citations, JWT authentication with silent token refresh, activity audit logging, and light/dark theme modes.

---

## Project Architecture

```text
docuchat-ai/
├── backend/                  # FastAPI (Python 3.11+), SQLAlchemy 2.0 async, Alembic, pgvector, Azure OpenAI
│   ├── alembic/              # Database migration scripts
│   ├── app/                  # Application code (routers, schemas, models, services, core config)
│   ├── tests/                # Automated pytest suite (27 unit & integration tests)
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 18, Vite, TypeScript, Tailwind CSS, TanStack Query, Zustand
│   ├── src/                  # Application code (components, pages, api, store)
│   └── package.json          # Frontend dependencies and build/lint scripts
├── scripts/
│   ├── dev.sh                # Linux / macOS / Git Bash runner (backend + frontend)
│   └── dev.ps1               # Windows PowerShell runner (backend + frontend)
└── README.md
```

---

## Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ and npm
- **PostgreSQL**: 15+ with the `pgvector` extension installed
- **Azure OpenAI**: Provisioned instance with chat completion (e.g. `gpt-4o`) and text embedding (e.g. `text-embedding-3-small`, 1536 dimensions) deployments

---

## Run the Whole Project Locally

Follow these step-by-step instructions to run the entire project locally without Docker:

### 1. Database Setup (PostgreSQL + pgvector)

Create the PostgreSQL database and enable the `vector` extension:

```sql
-- Connect to your local PostgreSQL instance:
CREATE DATABASE docuchat;
\c docuchat
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux / Git Bash:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and configure Azure OpenAI credentials and database URL:
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Configure environment variables
# Copy .env.example to .env:
cp .env.example .env

# Start Vite development server
npm run dev
```

### 4. Application URLs

- **Frontend Web UI**: [http://localhost:5173](http://localhost:5173)
- **Backend Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Quick Start Scripts (One Command)

Convenience scripts are provided in the `scripts/` directory to start both backend and frontend concurrently with graceful termination:

### Windows (PowerShell)
```powershell
.\scripts\dev.ps1
```

### Linux / macOS / Git Bash
```bash
chmod +x ./scripts/dev.sh
./scripts/dev.sh
```

---

## End-to-End Walkthrough Script

Follow this verification script to test all features end-to-end:

### Step 1: User Registration & Authentication
1. Open the frontend at [http://localhost:5173](http://localhost:5173).
2. Click **Create an account** or navigate to `/register`.
3. Register with:
   - **Full Name**: `Jane Doe`
   - **Email**: `jane@example.com`
   - **Password**: `SecurePassword123`
4. Upon submitting, you are automatically logged in, issued a JWT session, and redirected to `/documents`.

### Step 2: Upload a PDF Document
1. On the **Documents** page (`/documents`), locate the upload drag-and-drop zone.
2. Drag and drop any PDF file (or click to browse and select a PDF up to 20 MB).
3. Observe the upload progress indicator.
4. The document initially appears with status badge **UPLOADED** or **PROCESSING** while the backend extracts page text, chunks the text, and generates pgvector embeddings.
5. The UI automatically polls every 3 seconds until the status turns to **READY** (with page count and file size displayed).

### Step 3: Start a Grounded Conversation
1. Click the **Chat** button next to your READY document in the table (or click **New Chat** at the top).
2. In the modal, enter an optional title (e.g. `PDF Analysis Q1`), verify your document is selected, and click **Start Chat**.
3. You are redirected to `/chat/<conversation_id>`.

### Step 4: Ask a Question & Inspect Citations
1. In the chat prompt box, type a specific question about your document content (e.g., `"What are the key findings discussed in this document?"`) and press **Enter**.
2. Watch the assistant response **stream token-by-token in real-time**.
3. Above or below the response, notice the **Verified Sources** chips (e.g. `[1] Report.pdf p.4`).
4. Click any source chip to open the **Verified Source Drawer** on the right. Inspect the exact grounded document extract, similarity match percentage, and page number.

### Step 5: Audit & Activity Logging
1. Click **Activity Logs** in the sidebar (or navigate to `/activity`).
2. Review the chronological audit trail displaying:
   - `USER_LOGIN`
   - `DOCUMENT_UPLOAD`
   - `DOCUMENT_CHUNK`
   - `DOCUMENT_EMBED`
   - `CONVERSATION_CREATE`
   - `CHAT_MESSAGE`
3. Test search filtering and pagination controls.

### Step 6: Dark Mode & Error Boundaries
1. Click the **Sun / Moon toggle** in the top navigation bar.
2. Confirm all views, modals, chat bubbles, source drawers, and tables transition into high-contrast dark mode.
3. Refresh the page to verify that the theme preference persists via `localStorage`.

---

## Testing & Quality Assurance

Run the test suite and verify frontend build integrity:

### Backend Pytest Suite
```bash
cd backend
python -m pytest -q
```
*Expected: 27 passed tests covering auth, document upload, chunking, pgvector search, conversation isolation, and activity logging.*

### Frontend Build & Typecheck
```bash
cd frontend
npm run lint
npm run build
```
*Expected: TypeScript typecheck passes with 0 errors and production bundle builds successfully.*

---

## Known Limitations

- **OCR for Scanned Images**: Scanned image PDFs without selectable text layers are not currently extracted via OCR (standard text and programmatic PDFs with text streams are supported).
- **File Format**: Currently restricted to PDF documents (DOCX and Markdown ingestion can be added in future iterations).
- **Multi-Modal Figures**: Tables and diagram images embedded as bitmap graphics are not processed through multimodal vision models.

---

## Suggested Next Steps & Roadmap

1. **OCR Ingestion Pipeline**: Add Tesseract or Azure Document Intelligence OCR fallback for scanned/image-only PDFs.
2. **Hybrid Search**: Combine pgvector dense cosine search with PostgreSQL `tsvector` full-text BM25 search with Reciprocal Rank Fusion (RRF).
3. **Multi-File Chat Grounding**: Add multi-document synthesis mode with cross-document comparative summaries.
4. **Document Export**: Add PDF export or Markdown export for generated conversation transcripts and citations.
