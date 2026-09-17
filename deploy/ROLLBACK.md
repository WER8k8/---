# 5 分钟快速回滚预案（§17）

> 目标：线上发布后发现问题，**5 分钟内**回到上一个已知良好状态。
> 三件套脚本在 `deploy/scripts/`：`pre-deploy-snapshot.sh` / `rollback.sh` / `smoke-test.sh`。

## 流程（发布前 → 出问题 → 回滚）

### 1. 发布前：固化回滚点（必做）
```bash
./deploy/scripts/pre-deploy-snapshot.sh
```
产出 `deploy/snapshots/snapshot-<ts>.json`（含 git 版本、alembic 版本、pg_dump 备份路径），并更新 `latest` 软链。
**没跑快照 = 没有回滚点，禁止发布。**

### 2. 发布后：冒烟验证（必做）
```bash
./deploy/scripts/smoke-test.sh
```
- 通过 → 完成，观察 2 分钟监控。
- 失败 → 立即进入第 3 步。

### 3. 回滚（≤5 分钟）
```bash
# 默认：迁移回退 1 版 + 应用切回上一 git 版本
./deploy/scripts/rollback.sh

# 迁移破坏数据时（危险，需二次确认）：连数据一起从 pg_dump 恢复
STEPS=3 ./deploy/scripts/rollback.sh

# 先演练不真执行
DRY_RUN=true ./deploy/scripts/rollback.sh
```

### 4. 回滚后再验一次
```bash
./deploy/scripts/smoke-test.sh
```

## 关键原则

| 原则 | 说明 |
|---|---|
| 顺序不可颠倒 | 先回 DB 迁移，再切应用，最后才动数据 |
| 默认最小回滚 | `STEPS=2`（迁移+应用），`STEPS=3`（含数据恢复）只在破坏性迁移时用 |
| 破坏性迁移要可回退 | 写 alembic 迁移时必须写 `downgrade()`；`ALTER TABLE DROP COLUMN` 这类不可逆操作，发布前必须额外做数据备份 |
| 快照 = 回滚点的唯一来源 | `rollback.sh` 靠 `snapshots/latest` 定位版本，缺了它回滚无从下手 |

## 数据库迁移回滚细节

项目用 alembic（90 个迁移版本在 `backend/alembic_migrations/versions/`）。
- 查询当前版本：`cd backend && ./.venv/bin/alembic current`
- 回退一步：`./.venv/bin/alembic downgrade -1`
- 回退到快照版本：`./.venv/bin/alembic downgrade <快照里的 alembic_rev>`

**红线**：生产数据库回滚前，`pg_dump` 备份必须成功落盘（`pre-deploy-snapshot.sh` 已含此步）。

## 未覆盖项（诚实标注）

- **蓝绿部署切换**：当前是单机 `deploy.sh` 直发，无蓝绿。要做到真正的零停机回滚，需接 `deploy/production/` 的容器编排（docker-compose.prod.yml），把上一版镜像保留 24h 作为回滚目标。
- **自动触发**：目前回滚是手动执行；接 CI/CD 后可把 `smoke-test.sh` 失败自动调 `rollback.sh`（加一个 guardrail：只允许自动回滚 `STEPS<=2`，`STEPS=3` 必须人工）。
