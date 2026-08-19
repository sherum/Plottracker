#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.backend.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        echo "Backend stopped (pid $PID)"
    fi
    rm -f "$PID_FILE"
else
    PID="$(lsof -ti:8000 || true)"
    if [ -n "$PID" ]; then
        kill "$PID"
        echo "Backend stopped (pid $PID)"
    else
        echo "Backend not running"
    fi
fi
