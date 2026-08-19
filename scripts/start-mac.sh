#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.backend.pid"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Backend already running (pid $(cat "$PID_FILE"))"
    exit 0
fi

cd "$ROOT_DIR/backend"
nohup uv run uvicorn app.main:app --port 8000 > "$ROOT_DIR/.backend.log" 2>&1 &
echo $! > "$PID_FILE"
echo "Backend started (pid $!) - http://localhost:8000"
