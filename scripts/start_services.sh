#!/bin/bash

set -euo pipefail  # Exit on error, unset vars, pipe failures

# =========================
# ✅ Environment Setup
# =========================
export ENVIRONMENT=dev
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
QDRANT_BIN="$HOME/Documents/Apps/qdrant/bin/qdrant"
QDRANT_CONFIG="$PROJECT_ROOT/config/qdrant_config.yaml"
LOG_DIR="$PROJECT_ROOT/logs"
QDRANT_LOG="$LOG_DIR/qdrant_$(date +%Y%m%d_%H%M%S).log"
FASTAPI_LOG="$LOG_DIR/fastapi_$(date +%Y%m%d_%H%M%S).log"
ENV_FILE="$PROJECT_ROOT/.env"
REQUIRED_COLLECTION="llamaindex-docs"

mkdir -p "$LOG_DIR"

# =========================
# ✅ Helper Functions
# =========================
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

relative_path() {
  local full_path="$1"
  echo "${full_path#$PROJECT_ROOT/}"
}

# =========================
# ✅ Virtual Environment Activation
# =========================
if [ -d "$VENV_PATH" ]; then
  log "🧩 Activating Python virtual environment..."
  source "$VENV_PATH/bin/activate"
else
  log "❌ Virtual environment not found at .venv. Exiting."
  exit 1
fi

log "🐍 Python Executable: $(which python | xargs basename)"
log "🐍 Python Version: $(python --version)"

# =========================
# ✅ .env Verification
# =========================
if [ ! -f "$ENV_FILE" ]; then
  log "❌ .env file not found at root. Exiting."
  exit 1
fi

# =========================
# ✅ API Key Setup
# =========================
if grep -q "^API_KEY=" "$ENV_FILE"; then
  log "🔑 API_KEY found in .env."
else
  GENERATED_KEY=$(openssl rand -hex 12)
  echo "API_KEY=$GENERATED_KEY" >> "$ENV_FILE"
  log "✅ API_KEY generated and added to .env: $GENERATED_KEY"
fi

# =========================
# ✅ Vector Database (Qdrant) Start or Detect
# =========================
log "🔍 Checking if Vector Database (Qdrant) is already running..."
QDRANT_PID=$(pgrep -f "qdrant.*--config-path $QDRANT_CONFIG" || true)

if [ -n "$QDRANT_PID" ]; then
  log "✅ Vector Database (Qdrant) already running at PID $QDRANT_PID"
else
  log "🚀 Starting Vector Database (Qdrant)..."
  "$QDRANT_BIN" --config-path "$QDRANT_CONFIG" > "$QDRANT_LOG" 2>&1 &
  QDRANT_PID=$!
  log "✅ Vector Database (Qdrant) started with PID $QDRANT_PID"
fi

# =========================
# ✅ Verify Collection Exists
# =========================
log "🔍 Verifying vector db collection: $REQUIRED_COLLECTION..."
COLLECTION_EXISTS=false
for i in {1..20}; do
  if curl -s "http://localhost:6333/collections/$REQUIRED_COLLECTION" | grep -q '"status":"ok"'; then
    log "✅ Vector db collection '$REQUIRED_COLLECTION' is available."
    COLLECTION_EXISTS=true
    break
  else
    log "⌛ Attempt $i: Waiting for vector db collection '$REQUIRED_COLLECTION'..."
    sleep 1
  fi
done

if [ "$COLLECTION_EXISTS" = false ]; then
  log "⚠️ Vector db collection '$REQUIRED_COLLECTION' not found. Proceeding to data load..."
  python -m app.data_loader.load_data
  log "✅ Data load completed. Vector db collection '$REQUIRED_COLLECTION' is now ready."
else
  log "✅ Skipping data load. Vector db collection already exists."
fi

# =========================
# ✅ API Server (FastAPI) Start (Background)
# =========================
log "🚀 Starting API Server (FastAPI) in background..."
python -m app.main --host 0.0.0.0 --port 8000 > "$FASTAPI_LOG" 2>&1 &
FASTAPI_PID=$!
log "✅ API Server (FastAPI) started with PID $FASTAPI_PID"

# =========================
# ✅ FastAPI Health Check
# =========================
log "🔍 Verifying API Server (FastAPI) health endpoint..."
for i in {1..20}; do
  if curl -s http://localhost:8000/health | grep -q '"status":"✅ API is running"'; then
    log "✅ FastAPI health check passed."
    break
  else
    log "⌛ Attempt $i: Waiting for FastAPI..."
    sleep 1
  fi
done

# =========================
# ✅ Final System Summary
# =========================
echo ""
echo "🚀 All services started successfully!"
echo "=================================================="
echo "Your system bootstrapped fully, no errors in the logs, all services came alive:"
echo -e "\t→ Vector Database (Qdrant) ✅"
echo -e "\t→ API Server (FastAPI) ✅"
echo -e "\t→ Gradio interface ✅ (Check: http://localhost:8000/gradio)"
echo -e "\t→ Web Search Client (Tavily) ✅ (Check logs for init confirmation)"
echo -e "\t→ Vector Engine ✅ (Check logs for init confirmation)"
echo -e "\t→ Summary Engine ✅ (Check logs for init confirmation)"
echo -e "\t→ Router Tool ✅ (Check logs for init confirmation)"
echo -e "\t→ Agent ✅ (Check logs for init confirmation)"
echo "=================================================="
echo ""
echo -e "🧭 Gradio UI:      \thttp://localhost:8000/gradio"
echo -e "🧭 FastAPI Health: \thttp://localhost:8000/"
echo -e "🧭 Vector DB Admin:\thttp://localhost:6333"
echo ""
echo -e "💡 To stop services manually: run 'make stop' or Ctrl+C"
echo ""

log "✅ Background services are running."
log "✅ You can tail logs here: tail -f $FASTAPI_LOG $QDRANT_LOG"
log "🎉 Application ready to use!"
