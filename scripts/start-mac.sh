#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID_FILE="$ROOT_DIR/.backend.pid"
FRONTEND_PID_FILE="$ROOT_DIR/.frontend.pid"

if [ -f "$BACKEND_PID_FILE" ] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
    echo "Backend already running (pid $(cat "$BACKEND_PID_FILE"))"
else
    cd "$ROOT_DIR/backend"
    nohup uv run uvicorn app.main:app --port 8000 > "$ROOT_DIR/.backend.log" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
    echo "Backend started (pid $!) - http://localhost:8000"
fi

if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
    echo "Frontend already running (pid $(cat "$FRONTEND_PID_FILE"))"
else
    cd "$ROOT_DIR/frontend"
    nohup npm run dev > "$ROOT_DIR/.frontend.log" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    echo "Frontend started (pid $!) - http://localhost:5173"
fi
