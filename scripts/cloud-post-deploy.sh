#!/usr/bin/env bash
# 云上部署后自动展开：Agency LLM + 首巡站 + 运维 cron 提示
# 由 deploy/deploy.sh Step 9 或手动调用：
#   bash scripts/cloud-post-deploy.sh
#   HERMES_AGENCY_AUTO_DOCKER_OLLAMA=1 bash scripts/cloud-post-deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

log() { echo "[cloud-post-deploy] $*"; }

cd "$ROOT"

# --- 1. Agency LLM（Ollama 侧车 + 探测）---
log "Agency LLM bootstrap..."
if [[ -f "$ROOT/deploy/production/agency-llm-compose.yml" ]]; then
  if [[ "${HERMES_AGENCY_AUTO_DOCKER_OLLAMA:-1}" == "1" ]] && command -v docker >/dev/null 2>&1; then
    docker compose -f deploy/production/agency-llm-compose.yml up -d ollama 2>/dev/null || true
    sleep 3
    MODEL="${HERMES_AGENCY_OLLAMA_MODEL:-llama3.1}"
    docker exec youding-ollama ollama pull "$MODEL" 2>/dev/null || log "ollama pull skipped (container starting)"
  fi
fi

if [[ -f "$ROOT/scripts/setup-agency-llm-providers.sh" ]]; then
  bash "$ROOT/scripts/setup-agency-llm-providers.sh" --target=server || true
fi

# --- 2. 后端内 bootstrap（ollama pull / npm 若显式开启）---
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-post-deploy-$(openssl rand -hex 16 2>/dev/null || echo xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)}"
export SECRET_KEY="${SECRET_KEY:-$JWT_SECRET_KEY}"
if [[ -d "$BACKEND" ]]; then
  cd "$BACKEND"
  python3 -c "
from app.services.hermes.agency.provider_setup import run_automated_bootstrap
import json
print(json.dumps(run_automated_bootstrap(), ensure_ascii=False, indent=2))
" 2>/dev/null || log "in-process bootstrap skipped (backend deps not on host)"
  cd "$ROOT"
fi

# --- 3. 首巡站 / Hermes 运维循环（容器内或宿主机 venv）---
run_hermes_ops() {
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q youding-backend; then
    docker exec youding-backend python scripts/run_ops_jobs.py --job hermes-ops 2>/dev/null && return 0
  fi
  if [[ -x "$BACKEND/.venv/bin/python" ]]; then
    (cd "$BACKEND" && .venv/bin/python scripts/run_ops_jobs.py --job hermes-ops) && return 0
  fi
  if command -v python3 >/dev/null 2>&1 && [[ -f "$BACKEND/scripts/run_ops_jobs.py" ]]; then
    (cd "$BACKEND" && python3 scripts/run_ops_jobs.py --job hermes-ops) && return 0
  fi
  log "hermes-ops skipped (no backend runtime)"
  return 0
}

log "Hermes ops autopilot (first cycle)..."
run_hermes_ops || true

# --- 4. cert:gate 轻量探测（Admin 构建机有 node 时）---
if [[ -f "$ROOT/frontend/admin/package.json" ]] && command -v npm >/dev/null 2>&1; then
  log "cert:gate dry-run (optional)..."
  (cd "$ROOT/frontend/admin" && npm run cert:gate -- --dry-run 2>/dev/null) || log "cert:gate skipped"
fi

# --- 5. cron 提示 ---
log "=== 建议 crontab（见 scripts/ops-cron.example.sh）==="
grep -v '^#' "$ROOT/scripts/ops-cron.example.sh" 2>/dev/null | grep -v '^$' || true

log "cloud-post-deploy done"
