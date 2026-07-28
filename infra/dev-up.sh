#!/usr/bin/env bash
# Starts the whole local dev stack: Docker Desktop, the Odoo/Postgres/proxy
# containers, and the Vite dev server - bound to 0.0.0.0 so the Nginx proxy
# container can reach it (a plain `npm run dev` binds to localhost only and
# breaks http://localhost:8080).
#
# Safe to run repeatedly: skips anything that's already up and reachable.
# Wired to run automatically on folder open via .vscode/tasks.json.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$REPO_ROOT/infra"
WEB_DIR="$REPO_ROOT/project"
LOG_DIR="$REPO_ROOT/.dev-logs"
mkdir -p "$LOG_DIR"

echo "== Peart Serenity: starting local dev stack =="

# 1. Docker Desktop
if ! docker info >/dev/null 2>&1; then
  echo "-> Docker daemon not running, launching Docker Desktop..."
  open -a Docker
  for _ in $(seq 1 60); do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
  if ! docker info >/dev/null 2>&1; then
    echo "!! Docker did not come up in time. Open Docker Desktop manually and re-run this script." >&2
    exit 1
  fi
fi
echo "-> Docker is up."

# 2. Odoo + Postgres + reverse proxy (no-op if already running)
echo "-> Ensuring Odoo/Postgres/proxy containers are up..."
(cd "$INFRA_DIR" && docker compose up -d) || {
  echo "!! Failed to start the Docker Compose stack. See output above." >&2
  exit 1
}

# 3. Vite dev server
site_status() { curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000"; }

if [ "$(site_status)" = "200" ]; then
  echo "-> Website already reachable through the proxy, leaving Vite as-is."
else
  if lsof -tiTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "-> Something is on :5173 but not reachable via the proxy (likely bound to localhost only). Restarting it..."
    lsof -tiTCP:5173 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
    sleep 1
  fi

  NPM_BIN="$(command -v npm || true)"
  if [ -z "$NPM_BIN" ]; then
    for candidate in "$HOME/Library/Application Support/Herd/config/nvm/versions/node"/*/bin/npm "$HOME/.nvm/versions/node"/*/bin/npm; do
      [ -x "$candidate" ] && NPM_BIN="$candidate" && break
    done
  fi
  if [ -z "$NPM_BIN" ]; then
    echo "!! Could not find npm on this machine. Install Node, then run manually:" >&2
    echo "   cd project && npm run dev -- --port 5173 --strictPort --host 0.0.0.0" >&2
    exit 1
  fi
  export PATH="$(dirname "$NPM_BIN"):$PATH"

  if [ ! -d "$WEB_DIR/node_modules" ]; then
    echo "-> Installing frontend dependencies (first run)..."
    (cd "$WEB_DIR" && npm install)
  fi

  echo "-> Starting Vite dev server..."
  (cd "$WEB_DIR" && nohup npm run dev -- --port 5173 --strictPort --host 0.0.0.0 > "$LOG_DIR/vite.log" 2>&1 & disown)

  for _ in $(seq 1 15); do
    sleep 1
    [ "$(site_status)" = "200" ] && break
  done
fi

echo
if [ "$(site_status)" = "200" ]; then
  echo "== Ready =="
  echo "Website + Odoo (single entry point): http://localhost:8080"
  echo "Odoo direct (bypass proxy):           http://localhost:8169"
  echo "Vite dev server log:                  $LOG_DIR/vite.log"
else
  echo "!! Something isn't reachable yet. Check $LOG_DIR/vite.log and 'docker compose logs' in infra/." >&2
  exit 1
fi
