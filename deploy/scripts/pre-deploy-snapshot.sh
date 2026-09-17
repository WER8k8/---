#!/bin/bash
# ============================================================
# 优丁建材 SaaS — 发布前快照（配合 rollback.sh 做 5 分钟快速回滚）
#
# 在每次发布前调用，把「当前能回滚到的状态」固化下来：
#   1. 记录当前 alembic 迁移版本（回滚点）
#   2. 给数据库打逻辑备份（pg_dump / sqlite 拷贝）
#   3. 记录当前部署的 git 版本 / 二进制时间戳
#   4. 写出 snapshot.json 供 rollback.sh 读取
#
# 用法:
#   ./deploy/scripts/pre-deploy-snapshot.sh
# 输出: deploy/snapshots/snapshot-<ts>.json  +  latest 软链
# ============================================================
set -euo pipefail

DB_TYPE="${DB_TYPE:-postgresql}"
DB_NAME="${DB_NAME:-youding_dev}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-youding}"
DB_PASS="${DB_PASS:-youding}"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "$0")/../../backend" && pwd)}"

SNAP_ROOT="deploy/snapshots"
mkdir -p "$SNAP_ROOT"
TS="$(date +%Y%m%d-%H%M%S)"
SNAP="deploy/snapshots/snapshot-${TS}.json"

echo "[snapshot] 记录当前 alembic 版本…"
# 兼容 Windows (.venv/Scripts/alembic) 与 Unix (.venv/bin/alembic)
ALEMBIC_BIN="$BACKEND_DIR/.venv/bin/alembic"
[ -x "$ALEMBIC_BIN" ] || ALEMBIC_BIN="$BACKEND_DIR/.venv/Scripts/alembic"
PY_BIN="$BACKEND_DIR/.venv/bin/python"
[ -x "$PY_BIN" ] || PY_BIN="$BACKEND_DIR/.venv/Scripts/python"
ALEMBIC_NOW="$(cd "$BACKEND_DIR" && "$ALEMBIC_BIN" current 2>/dev/null | grep -oE "[a-f0-9_]{6,}" | head -1 || true)"
CURRENT_REV="${ALEMBIC_NOW:-unknown}"
echo "[snapshot] 当前迁移: ${CURRENT_REV}"

echo "[snapshot] 打数据库逻辑备份…"
DB_BACKUP="deploy/snapshots/db-${TS}.sql"
if [ "$DB_TYPE" = "postgresql" ] && command -v pg_dump >/dev/null 2>&1; then
  PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain > "$DB_BACKUP" && echo "[snapshot] 备份完成: $DB_BACKUP ($(du -h "$DB_BACKUP" | cut -f1))" \
    || echo "[snapshot][warn] pg_dump 失败，跳过数据库备份"
elif [ -f "$BACKEND_DIR/youding_dev.db" ] || [ -f "backend/youding_dev.db" ]; then
  SRC="$( [ -f "$BACKEND_DIR/youding_dev.db" ] && echo "$BACKEND_DIR/youding_dev.db" || echo "backend/youding_dev.db" )"
  cp "$SRC" "deploy/snapshots/db-${TS}.sqlite" && echo "[snapshot] sqlite 备份完成"
else
  echo "[snapshot][warn] 未找到数据库源，跳过备份"
fi

GIT_REV="$(git rev-parse HEAD 2>/dev/null || echo 'n/a')"
cat > "$SNAP" <<EOF
{
  "ts": "${TS}",
  "git_rev": "${GIT_REV}",
  "alembic_rev": "${CURRENT_REV}",
  "db_backup": "${DB_BACKUP}",
  "db_type": "${DB_TYPE}"
}
EOF
ln -sf "$(basename "$SNAP")" "$SNAP_ROOT/latest"
echo "[snapshot] 快照已写入 $SNAP"
echo "[snapshot] 完成 — 发布前回滚点已固化"
