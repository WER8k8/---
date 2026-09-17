#!/bin/bash
# ============================================================
# 优丁建材 SaaS — 5 分钟快速回滚
#
# 目标：发布后发现问题，≤5 分钟回到上一个已知良好状态。
# 回滚三步（顺序不可颠倒）：
#   ① 数据库回滚：alembic 迁移回退 N 版（默认 1）
#   ② 应用回滚：切回上一 git 版本 / 二进制
#   ③ 数据回填（仅当 DB 迁移破坏数据时）：从 pre-deploy 快照的 pg_dump 恢复
#
# 用法:
#   ./deploy/scripts/rollback.sh                 # 回滚 1 版迁移 + 应用
#   STEPS=3 ./deploy/scripts/rollback.sh         # 含数据恢复（危险）
#   ALEMBIC_STEPS=2 ./deploy/scripts/rollback.sh # 回退 2 版迁移
#   ./deploy/scripts/rollback.sh --dry-run        # 只打印不执行
# ============================================================
set -euo pipefail

ALEMBIC_STEPS="${ALEMBIC_STEPS:-1}"
STEPS="${STEPS:-2}"                 # 1=仅迁移, 2=迁移+应用, 3=+数据恢复
DRY_RUN="${DRY_RUN:-false}"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "$0")/../../backend" && pwd)}"
SNAP="deploy/snapshots/latest"

log() { echo -e "[rollback $*]"; }

run() {
  if [ "$DRY_RUN" = "true" ]; then
    echo "  (dry-run) $*"
  else
    "$@"
  fi
}

[ -f "$SNAP" ] || { log "未找到快照 $SNAP，无法定位回滚点"; exit 1; }
SNAP_ABS="$(cd "$(dirname "$SNAP")" && readlink -f "$SNAP" 2>/dev/null || echo "$SNAP")"
SNAP_REV="$(python -c "import json,sys; print(json.load(open('$SNAP_ABS'))['alembic_rev'])" 2>/dev/null || echo "")"

echo "════════ 5 分钟快速回滚 ════════"
echo " 目标迁移版本: ${SNAP_REV:-latest-snapshot}"
echo " 迁移回退步数: $ALEMBIC_STEPS   范围: $STEPS"
echo " dry-run: $DRY_RUN"

# ── ① 数据库迁移回退 ──
# 兼容 Windows (.venv/Scripts/alembic) 与 Unix (.venv/bin/alembic)
ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"
[ -x "$ALEMBIC_BIN" ] || ALEMBIC_BIN="$BACKEND_DIR/.venv/Scripts/alembic"
log "① alembic 回退（目标: ${SNAP_REV:-回退$ALEMBIC_STEPS步}）"
if [ -n "$SNAP_REV" ] && [ "$SNAP_REV" != "unknown" ]; then
  run bash -c "cd '$BACKEND_DIR' && '$ALEMBIC_BIN' downgrade '$SNAP_REV'"
else
  run bash -c "cd '$BACKEND_DIR' && for i in $(seq 1 $ALEMBIC_STEPS); do '$ALEMBIC_BIN' downgrade -1; done"
fi

# ── ② 应用回滚 ──
if [ "$STEPS" -ge 2 ]; then
  log "② 应用切回上一版本"
  GIT_REV="$(python -c "import json; print(json.load(open('$SNAP_ABS'))['git_rev'])" 2>/dev/null || echo "")"
  if [ -n "$GIT_REV" ] && [ "$GIT_REV" != "n/a" ]; then
    run bash -c "cd '$BACKEND_DIR/..' && git checkout '$GIT_REV'"
  else
    log "   无 git 版本，请手动切回应用二进制/容器镜像"
  fi
fi

# ── ③ 数据恢复（仅破坏性迁移需要）──
if [ "$STEPS" -ge 3 ]; then
  log "③ 从快照 pg_dump 恢复数据（危险，请确认）"
  DB_BACKUP="$(python -c "import json; print(json.load(open('$SNAP_ABS')).get('db_backup',''))" 2>/dev/null)"
  if [ -n "$DB_BACKUP" ] && [ -f "$DB_BACKUP" ]; then
    run bash -c "psql -h \${DB_HOST:-localhost} -p \${DB_PORT:-5433} -U \${DB_USER:-youding} -d \${DB_NAME:-youding_dev} -f '$DB_BACKUP'"
  else
    log "   快照无可用数据库备份，跳过"
  fi
fi

echo "════════ 回滚完成 ════════"
log "下一步：跑冒烟测试验证 → ./deploy/scripts/smoke-test.sh"
