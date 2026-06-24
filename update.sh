#!/bin/bash
# =============================================================
#  27 CARS — PI UNIT UPDATE
#  Pulls latest code from GitHub and rebuilds the container.
#  Run manually or called automatically on boot.
# =============================================================

REPO_DIR="$HOME/piforgit"

echo "[$(date '+%H:%M:%S')] 27 Cars — Update starting..."

cd "$REPO_DIR" || { echo "ERROR: Repo not found at $REPO_DIR. Run setup.sh first."; exit 1; }

# Wait for internet before pulling
echo "[$(date '+%H:%M:%S')] Waiting for connectivity..."
timeout 30s bash -c 'until ping -c 1 github.com &>/dev/null; do sleep 2; done' || {
    echo "WARNING: No internet after 30s — starting with existing code."
}

# Pull latest
echo "[$(date '+%H:%M:%S')] Pulling latest from GitHub..."
git pull origin main

# Rebuild and restart
echo "[$(date '+%H:%M:%S')] Rebuilding container..."
docker compose up -d --build

echo "[$(date '+%H:%M:%S')] Done. Unit is running."
