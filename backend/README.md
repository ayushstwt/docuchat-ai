# DocuChat AI - Backend

FastAPI backend service for DocuChat AI.

## Environment Configuration

DocuChat AI supports multiple environments (`local`, `dev`, `staging`, `prod`).
For full environment documentation, Docker configurations, and deployment guidelines, please refer to the [Root README.md](../README.md#environments).

### Quick Local Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
