#!/usr/bin/env bash
# Hermes agency LLM — 服务器探测与半自动安装
# 用法:
#   bash scripts/setup-agency-llm-providers.sh
#   bash scripts/setup-agency-llm-providers.sh --install-cli
#   bash scripts/setup-agency-llm-providers.sh --start-ollama
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
TARGET="${TARGET:-server}"
OLLAMA_MODEL="${HERMES_AGENCY_OLLAMA_MODEL:-llama3.1}"
INSTALL_CLI=0
START_OLLAMA=0
for arg in "$@"; do
  case "$arg" in
    --install-cli) INSTALL_CLI=1 ;;
    --start-ollama) START_OLLAMA=1 ;;
    --target=dev) TARGET=dev ;;
    --target=server) TARGET=server ;;
  esac
done

export JWT_SECRET_KEY="${JWT_SECRET_KEY:-test-$(python3 -c 'print("x"*32)')}"
export SECRET_KEY="${SECRET_KEY:-test-$(python3 -c 'print("x"*32)')}"

echo "=== 1. Provider 探测 ==="
cd "$BACKEND"
python3 "$ROOT/scripts/probe-agency-llm-providers.py" || true

if [ "$INSTALL_CLI" = "1" ]; then
  echo ""
  echo "=== 2. npm 全局 CLI（不含 OAuth）==="
  for pkg in @google/gemini-cli @anthropic-ai/claude-code @github/copilot @openai/codex openclaw@latest; do
    echo "npm install -g $pkg"
    npm install -g "$pkg" || true
  done
fi

if [ "$START_OLLAMA" = "1" ]; then
  echo ""
  echo "=== 3. Ollama（Docker 推荐）==="
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$ROOT/deploy/production/agency-llm-compose.yml" up -d ollama || true
    sleep 3
    docker exec youding-ollama ollama pull "$OLLAMA_MODEL" || true
  elif command -v ollama >/dev/null 2>&1; then
    (systemctl is-active ollama >/dev/null 2>&1 || ollama serve &) || true
    sleep 2
    ollama pull "$OLLAMA_MODEL" || true
  else
    echo "请安装 Ollama 或使用 deploy/production/agency-llm-compose.yml"
  fi
fi

echo ""
echo "=== 4. 部署计划 (target=$TARGET) ==="
python3 -c "
import json
from app.services.hermes.agency.provider_setup import build_setup_plan
print(json.dumps(build_setup_plan(target='$TARGET'), ensure_ascii=False, indent=2))
"

echo ""
echo "=== 生产建议 ==="
echo "  HERMES_AGENCY_PROVIDER_CHAIN=deepseek,ollama,openai,hermes-cli"
echo "  配置 AI_DEEPSEEK_API_KEY / OPENAI_API_KEY；CLI OAuth 仅适合跳板机一次性登录"
