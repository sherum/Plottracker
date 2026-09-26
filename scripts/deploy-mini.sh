#!/usr/bin/env bash
# Deploy to a remote Mac over ssh and run it with docker compose.
# Usage: scripts/deploy-mini.sh [host] [port]
# Existing remote data (database, manuscripts) is never overwritten.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${1:-davids-mac-mini.local}"
PORT="${2:-8010}"
REMOTE_DIR="scify"
REMOTE_PATH='PATH=$PATH:/usr/local/bin:/opt/homebrew/bin'

echo "Syncing code to $HOST:~/$REMOTE_DIR"
rsync -az --delete \
    --exclude .git --exclude .venv --exclude '**/.venv' --exclude '**/node_modules' \
    --exclude '**/__pycache__' --exclude frontend/dist --exclude .idea --exclude oos \
    --exclude '*.pid' --exclude '*.log' --exclude .DS_Store \
    --exclude data --exclude draft_scripts --exclude story_notes \
    "$ROOT_DIR/" "$HOST:$REMOTE_DIR/"

echo "Copying data that does not exist remotely yet"
rsync -az --ignore-existing "$ROOT_DIR/data" "$ROOT_DIR/draft_scripts" "$ROOT_DIR/story_notes" "$HOST:$REMOTE_DIR/"

echo "Building and starting on $HOST (port $PORT)"
ssh "$HOST" "$REMOTE_PATH; cd $REMOTE_DIR && HOST_PORT=$PORT docker compose up -d --build"

echo "Checking health"
curl -sS --retry 10 --retry-delay 2 --retry-all-errors "http://$HOST:$PORT/health" && echo && echo "Deployed: http://$HOST:$PORT"
