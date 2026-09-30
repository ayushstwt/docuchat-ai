#!/usr/bin/env bash
set -e

# Change directory to repository root
cd "$(dirname "$0")/.."
ROOT_DIR="$(pwd)"

echo "===================================================="
echo " Starting DocuChat AI (Backend + Frontend)"
echo "===================================================="

# Backend environment setup
cd "$ROOT_DIR/backend"
if [ -d ".venv" ]; then
    echo "[Backend] Activating virtual environment (.venv)..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    echo "[Backend] Activating virtual environment (../.venv)..."
    # shellcheck disable=SC1091
    source ../.venv/bin/activate
fi

# Trap cleanup to kill all child background processes on exit
cleanup() {
    echo ""
    echo "[Dev] Shutting down backend and frontend processes..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start backend server
echo "[Backend] Starting FastAPI server on http://localhost:8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend dev server
cd "$ROOT_DIR/frontend"
echo "[Frontend] Starting Vite dev server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "===================================================="
echo " DocuChat AI Dev Environment is running!"
echo " - Backend API docs: http://localhost:8000/docs"
echo " - Frontend Web UI:  http://localhost:5173"
echo " Press Ctrl+C to terminate both servers."
echo "===================================================="
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
