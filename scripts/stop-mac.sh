#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

stop_service() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    if [ -f "$pid_file" ]; then
        local pid
        pid="$(cat "$pid_file")"
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "$name stopped (pid $pid)"
        fi
        rm -f "$pid_file"
    else
        local pid
        pid="$(lsof -ti:"$port" || true)"
        if [ -n "$pid" ]; then
            kill "$pid"
            echo "$name stopped (pid $pid)"
        else
            echo "$name not running"
        fi
    fi
}

stop_service "Backend" "$ROOT_DIR/.backend.pid" 8000
stop_service "Frontend" "$ROOT_DIR/.frontend.pid" 5173
