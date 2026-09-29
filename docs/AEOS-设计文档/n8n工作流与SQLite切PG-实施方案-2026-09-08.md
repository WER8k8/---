# n8n 工作流启用 & SQLite→PostgreSQL 切换 实施方案（只读勘察版）

> 生成时间：2026-09-08 15:4x
> 状态：**方案稿，未实施**。以下所有结论均来自当前仓库真实代码与本机实测。
> 代码路径基准：`上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend`（下文简称 `backend/`）

---

## 0. 一句话结论（先看这个）

| 问题 | 结论 |
|---|---|
| 现在该启用这两个 n8n 工作流吗 | **不该**。本机没有 n8n 实例（5678 不可达）、4 个 compose 里没有任何 n8n 服务、6 个 env 全未设置。现在启用只会产生无意义重试和日志噪声 |
| 现在该切 PostgreSQL 吗 | **开发阶段可以先不切**。当前 SQLite 219 表/4.8MB 工作正常；切 PG 的前置是 **Docker 守护进程目前没启动**（`docker ps` 报 npipe 连接失败），5433/6379 都无监听 |
| 5433 是什么 | compose 里 `postgres` 服务的**宿主机映射端口**（5433→容器 5432），不是 PG 的默认端口。见 §B1 |

---

# Part A｜n8n 两个工作流的真实实现

## A1. 机制全貌（4 个文件，2 条链路）

```
触发源（成功后）                  出站                                    n8n
─────────────────────────────────────────────────────────────────────────────
hermes_task_bridge._notify_site_built      ┐
  (仅 task_type in ai_site_build/site_build)├→ trigger_n8n_workflow.delay(
deerflow/executor._notify_content_published┘   workflow_id, payload)  [Celery]
  (仅 seo_publish / multi_channel_publish)        │
                                                 ↓
                        N8nTriggerService.trigger()  ← ensure_builtin_workflows()
                                                 │    (读 env，幂等注册)
                                                 ↓
                              registry.get(workflow_id)
                                  ├─ None        → ValueError「未注册」→ 不重试
                                  └─ enabled=False→ ValueError「已禁用」→ 不重试
                                                 ↓
                                    httpx POST endpoint（30s 超时，3 次退避重试）
```

## A2. 文件与行号（逐条对应你的疑问）

### ① 环境变量读取位置
`backend/app/services/n8n/workflow_registry.py`

| 位置 | 作用 |
|---|---|
| `_ensure_one_workflow()`（约 L229–282） | 通用注册器：`os.environ.get(url_env)` / `enabled_env` / `auth_env`，**不经过 pydantic Settings** |
| `ensure_builtin_workflows()`（约 L285–330） | 调两次上面函数，注册两个内建工作流 |
| `site_built_notify` | `url_env=N8N_SITE_BUILT_WEBHOOK_URL`、`enabled_env=N8N_SITE_BUILT_ENABLED`、`auth_env=N8N_SITE_BUILT_AUTH_HEADER` |
| `content_publish_dispatch` | `url_env=N8N_CONTENT_PUBLISH_WEBHOOK_URL`、`enabled_env=N8N_CONTENT_PUBLISH_ENABLED`、`auth_env=N8N_CONTENT_PUBLISH_AUTH_HEADER` |

三个关键行为（决定你怎么改才生效）：
- `enabled` 判定：`(os.environ.get(...) or "false").strip().lower() == "true"` → **默认 false**，只有字面量 `true` 才开。
- `auth` 解析：`"X-Api-Key: xxx"` 按**第一个冒号**拆成 header 名/值。
- **幂等且只注册一次**：`if registry.get(workflow_id) is not None: return`。注册表是**进程内内存单例**，所以：
  - 改 env 后**必须重启进程**（API / Celery worker / beat 各自都要重启，各自持有独立注册表）；
  - 运行时通过 API 改过的 endpoint/enabled 不会被 seed 覆盖。

### ② 工作流开关与 webhook 调用点
`backend/app/services/n8n/trigger.py`

| 位置 | 行为 |
|---|---|
| `N8nTriggerService.trigger()`（L59 起） | 先 `ensure_builtin_workflows()` → `registry.get()` → 未注册/已禁用均 `raise ValueError` → 否则 `httpx.AsyncClient(timeout=30)` POST endpoint |
| 重试 | 内部 3 次退避重试（1s→2s→4s），判定成功条件是 `status_code < 400` |
| `_build_n8n_request_headers()`（L150 起） | 固定加 `Content-Type`、`X-N8n-Trigger-Source: uj-backend`、`X-N8n-Workflow-Id`；`auth_type=header` 时追加鉴权头 |
| `trigger_n8n_workflow`（文件末尾，`@shared_task(bind=True, max_retries=3)`） | Celery 任务；**`ValueError`（未注册/已禁用）直接抛出不重试**，其它失败 `self.retry` 最多 3 次 |

⚠️ **一个未防护的角落**：`trigger()` **不校验 endpoint 是否为空**。若 `enabled=true` 但 URL 未配，会对空 URL 发请求 → httpx `RequestError` → 内部 4 次 + Celery 4 次 = **最多 16 次无效调用与退避**。所以两个变量必须成对配置。

### ③ 两个业务调用点（什么时候会触发）
| 文件:行 | 触发条件 | 备注 |
|---|---|---|
| `app/services/tasks/hermes_task_bridge.py:165` `_notify_site_built` | 桥执行成功 **且** `task.task_type in ("ai_site_build","site_build")`（L224–225） | payload: tenant_id/task_id/event=site_built/product/url |
| `app/services/deerflow/executor.py:512` `_notify_content_published` | `seo_publish` / `multi_channel_publish` 真实发布成功（L643、另一处 multi_channel） | payload: tenant_id/job_id/intent/event=content_publish/publish_result |

两者都被 `except Exception` 包住并 `logger.warning` —— **失败不影响主链路**，但也意味着"发了没成功"很容易被忽略，只能靠日志和 `registry.record_trigger` 计数观察。

### ④ 不要混淆：另一套 n8n 配置是「入站」
| 变量 | 位置 | 用途 |
|---|---|---|
| `N8N_WEBHOOK_SECRET` | `app/api/v1/routes/ubrain_commercial_os.py:382,399-404` | **入站**回调鉴权（n8n → 本后端）。未配置时该路由返回 503「拒绝写入」 |
| `N8N_WEBHOOK_URL` / `N8N_BASE_URL` | 仅出现在 `主要备份/上线网站/.env:92-94` | **worktree 代码里没有任何地方读取**，是遗留/示例值 |

即：出站（本方案 A 部分）与入站是**两套互不相干**的配置，启用 A 不需要配 `N8N_WEBHOOK_SECRET`。

## A3. 本机实测现状

```
site_built_notify        : enabled=False  endpoint=''  scene=site_built     auth=False
content_publish_dispatch : enabled=False  endpoint=''  scene=content_publish auth=False

N8N_SITE_BUILT_ENABLED / N8N_SITE_BUILT_WEBHOOK_URL / N8N_SITE_BUILT_AUTH_HEADER      = 未设置
N8N_CONTENT_PUBLISH_* (3 个)                                                          = 未设置
N8N_WEBHOOK_SECRET / N8N_WEBHOOK_URL / N8N_BASE_URL                                   = 未设置

curl http://127.0.0.1:5678/  → HTTP code=000（无 n8n 实例）
docker ps → failed to connect to Docker daemon（npipe 不存在）
```

**n8n 在仓库里的唯一痕迹**：`主要备份/上线网站/.claude/worktrees/nostalgic-mirzakhani-b5ac7e/deploy/examples/optional-sidecars/foreign-trade-stack.compose.yml`
（`n8nio/n8n:latest`，`5678:5678`，basic auth admin/changeme，卷 `n8n_data`）—— 这是 **examples 示例，未纳入 active worktree 的任何 compose**。

## A4. 启用前必须存在什么 + 怎么验证端点可用

### 硬性前置（缺一不可）
1. **一个真的在跑的 n8n 实例**（自建 Docker 或 n8n.cloud）。
2. **n8n 里两个 Workflow 已创建并 Active**，各自带一个 Webhook 触发节点。
3. **Production Webhook URL**（形如 `http://<host>:5678/webhook/<id>`）。
   ⚠️ 不要用 `/webhook-test/<id>`：测试 URL 只在编辑器打开时有效，生产会 404。
4. 若 n8n 开了鉴权，准备 header（如 `X-Api-Key: <token>`）。
5. 后端到 n8n 的网络可达（若后端跑在 Docker 内，用 `http://n8n:5678/...` 服务名，不能用 localhost）。

### 端点可用性验证（按序执行，全绿才配 env）

```bash
# 1) n8n 本体活着
curl -s -o /dev/null -w "n8n UI: %{http_code}\n" http://127.0.0.1:5678/

# 2) webhook 端点接受 POST（无鉴权时）—— 期望 200
curl -s -w "\nHTTP=%{http_code}\n" -X POST "http://127.0.0.1:5678/webhook/<id>" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"t_probe","task_id":"probe","event":"site_built","url":"https://example.com"}'

# 3) 需要鉴权时（对应 N8N_*_AUTH_HEADER）
curl -s -w "\nHTTP=%{http_code}\n" -X POST "http://127.0.0.1:5678/webhook/<id>" \
  -H "Content-Type: application/json" -H "X-Api-Key: <token>" -d '{"event":"probe"}'

# 4) 确认工作流是 Active（inactive 的 production webhook 会 404）
```

判定标准：**第 2/3 步返回 `HTTP=200`（或至少 < 400）且在 n8n 的 Executions 里能看到这条执行记录** —— 这一步看到记录，才算端点真的可用。

### 失效模式速查（配错了会怎样）
| 配置组合 | 实际行为 |
|---|---|
| `ENABLED` 未设 / `false`（现状） | 静默跳过，只在日志留一条 warning。**当前就是这个状态，无害** |
| `ENABLED=true` + URL 空 | 对空 URL 请求，内部 4 次 + Celery 4 次重试，纯噪声 |
| `ENABLED=true` + URL 404 | 重试后失败，Celery 任务报错，主链路仍不受影响 |
| `ENABLED=true` + URL 正常 | ✅ 触发成功，`registry.record_trigger` 累加 success |

### 建议的启用顺序（等你确认后再做）
1. 先只开一个（`site_built_notify`），配 URL + `true`，重启 API 与 worker。
2. 跑一次建站任务，在 n8n Executions 里确认收到 payload。
3. 稳定后再开第二个 `content_publish_dispatch`。

---

# Part B｜SQLite → PostgreSQL 完整方案

## B1. 5433 端口到底是什么

`docker-compose.dev.yml`（worktree 根）：

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: youding-dev-postgres
    environment:
      POSTGRES_DB: youding_dev
      POSTGRES_USER: youding
      POSTGRES_PASSWORD: youding
      POSTGRES_INITDB_ARGS: --encoding=UTF-8 --lc-collate=C --lc-ctype=C
    ports:
      - "5433:5432"     # 宿主机 5433 → 容器 5432
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

- **5433 = 宿主机侧端口**，5432 是容器内端口。之所以用 5433，是为了避开本机可能已存在的 5432。
- 同一份 compose 顶部给容器内服务用的是 `postgresql://youding:youding@postgres:5432/youding_dev`（**服务名 + 5432**）；
  宿主机上的应用/脚本要用 `localhost:5433`。**两套 URL 别混用**。
- 镜像是 `pgvector/pgvector:pg15`，如需向量能力要 `CREATE EXTENSION vector`。
- `docker-compose.dev.yml` 还定义了 `celery-worker` / `celery-beat` / mailhog 等（部分在 profile 下）。

**当前状态**：`docker ps` 失败（Docker Desktop 未启动），`netstat` 无 5433/6379 监听 → **PG 与 Redis 都没起来**。所以"切 PG"的第一步其实是"把 Docker 起来"。

## B2. 驱动现状（决定 URL 怎么写）

```
psycopg2 : OK      ← 可用
asyncpg  : MISSING ← 不可用
pgvector : MISSING
```

- URL 必须写 `postgresql://...` 或 `postgresql+psycopg2://...`。
- **不要写 `+asyncpg`**，装了才会工作；`config.py` 对 `postgresql://`（无显式驱动）只会打一条「建议 +asyncpg」的 warning，不阻断。
- 若确实要 asyncpg：`HTTP_PROXY= HTTPS_PROXY= ./.venv/Scripts/python.exe -m pip install asyncpg`
  （本机 `HTTP_PROXY` 指向死代理 127.0.0.1:7897；且 backend venv 的 `pip.exe` 启动器会静默失败，**必须用 `python -m pip`**）。

## B3. env 加载优先级（最容易改错文件的地方）

| 层 | 位置 | 说明 |
|---|---|---|
| 启动入口 | `run.py:13–35` `load_environment_config(env)` | 读 `backend/config/{env}/.env`，并设 `os.environ['ENVIRONMENT']`；找不到会回退读 `.env.example` |
| Settings | `app/core/config.py:27–39` | `_env_candidates = [$ENV_FILE, config/{ENVIRONMENT}/.env, .env]` → **config/{env}/.env 优先，`.env` 仅兜底**；`extra="allow"` |

→ **要改的是 `backend/config/dev/.env`（或 `config/prod/.env`），不要只改 `backend/.env`**（后者是兜底，两个文件并存会变双份维护，代码注释里已把它标注为待清理项）。

**成对校验（改错直接拒绝启动）**：`config.py` 的 `_init_db_type_validation`（约 L1006–1030）
- `DB_TYPE=postgresql` 但 URL 不含 postgresql → **ValueError 启动失败**
- `DB_TYPE=sqlite` 但 URL 不含 sqlite → **ValueError 启动失败**
- `DB_TYPE` 只认 `sqlite` / `postgresql`，其它值只 warning

所以切换时必须 **DB_TYPE 与 DATABASE_URL 一起改**。

**SQLite 路径解析**：`sqlite:///./youding_dev.db` 会被 `app/core/sqlite_paths.resolve_sqlite_database_url()` 解析为绝对路径
`...\backend\youding_dev.db`（实测，当前 4.8MB / 219 表）。

## B4. Alembic 与建表

- `alembic.ini`：`script_location = alembic_migrations`；`sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/youding` —— **这行是死的**：
  `alembic_migrations/env.py:44–45,85` 用 `os.getenv("DATABASE_URL", settings.DATABASE_URL)` 覆盖它。
  （这行写死值有误导性，属"看着像配置其实不生效"，建议加注释说明，但不影响切换。）
- 当前 **单 head**（`105_reconcile_model_backfill`），无分叉 → 迁移可正常进行（此前"双 head 不能碰迁移"是过时结论）。
- **代码中没有 `create_all`** → 表结构**完全依赖 Alembic**。空库必须先 `alembic upgrade head` 才有表。

## B5. 切换步骤（建议按顺序，每步可验证）

```
# 0) 备份（回滚的生命线）
cp backend/youding_dev.db backend/youding_dev.db.bak-20260908
cp backend/config/dev/.env backend/config/dev/.env.bak-20260908

# 1) 启动 Docker Desktop（必须人工确认 daemon 就绪）
docker ps

# 2) 起 PG + Redis
cd 上线网站.worktrees/agents-install-vscode-cline-deploy-strix
docker compose -f docker-compose.dev.yml up -d postgres redis

# 3) 等 healthy（约 10~30s）
docker compose -f docker-compose.dev.yml ps
docker exec youding-dev-postgres pg_isready -U youding -d youding_dev

# 4) 可选：向量扩展
docker exec youding-dev-postgres psql -U youding -d youding_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 5) 改 config/dev/.env（两行成对）
DB_TYPE=postgresql
DATABASE_URL=postgresql://youding:youding@localhost:5433/youding_dev   # 容器内用 postgres:5432

# 6) 空库建结构
cd backend && ./.venv/Scripts/python.exe -m alembic upgrade head

# 7) 起应用
./.venv/Scripts/python.exe run.py --env dev --port 8080

# 8) 验证
./.venv/Scripts/python.exe scripts/orchestration_selfcheck.py   # 第 1 项应显示 postgresql + 表数
```

## B6. 数据迁移（SQLite 现有 219 表 → PG）

三种路线，按推荐度排序：

| 方案 | 做法 | 优点 | 风险 |
|---|---|---|---|
| **A. 不迁数据（推荐先做）** | PG 只做新环境，`alembic upgrade head` 建空结构，老 SQLite 文件保留作归档 | 零数据风险、可随时回滚 | 历史数据在 PG 里没有，需要手工重建基础数据（租户/用户/技能包） |
| **B. 只迁关键表** | 用脚本逐表搬：tenants / users / skills / 配置类小表 | 可控、可校验 | 需处理自增序列（PG 需 `setval`）、布尔/时间类型差异、JSON 字段 |
| **C. 全量迁（pgloader / sqlite3 dump）** | 一次性搬 219 表 | 数据完整 | 类型差异（SQLite 动态类型 vs PG 严格）、外键顺序、`alembic_version` 会一起搬过来导致 PG 误认为已迁移 → **必须排除或事后修正 `alembic_version`** |

⚠️ 若走 C：**不要直接搬 `alembic_version`**。做法是先在 PG 跑 `alembic upgrade head` 建结构，再只搬业务表数据；或搬完后 `alembic stamp head`。

## B7. 回滚

| 场景 | 回滚动作 | 耗时 |
|---|---|---|
| 切 PG 后应用起不来 | `config/dev/.env` 改回 `DB_TYPE=sqlite` + `DATABASE_URL=sqlite:///./youding_dev.db`，重启 | 秒级（SQLite 文件全程未动） |
| PG 数据脏了 | 删库重建：`dropdb`/`createdb` 或直接删容器卷后重跑 `upgrade head` | 分钟级 |
| SQLite 文件损坏 | `cp youding_dev.db.bak-20260908 youding_dev.db` | 秒级 |

**关键安全性**：整个过程不删除 SQLite 文件，只改 env 指向 → 回滚成本极低。

---

# Part C｜env 配置清单（开发 vs 生产）

## C1. 数据库与队列

| 变量 | 开发（现状 SQLite） | 开发（切 PG 后建议） | 生产 | 说明/位置 |
|---|---|---|---|---|
| `ENVIRONMENT` | `dev` | `dev` | `prod` | `run.py` 按它选 `config/{env}/.env` |
| `ENV_FILE` | 不设 | 不设 | 不设 | 显式指定 env 文件，最高优先级 |
| `DB_TYPE` | `sqlite` | **`postgresql`** | `postgresql` | 必须与 URL 协议一致，否则启动拒绝 |
| `DATABASE_URL` | `sqlite:///./youding_dev.db` | `postgresql://youding:youding@localhost:5433/youding_dev` | `postgresql://<user>:<pwd>@<host>:5432/<db>`（**禁用弱密码**，`config.py:972` 会校验） | 主库 |
| `DATABASE_READ_URL` | 不设（可选） | 不设 | 只读副本 URL（可选） | `config.py:123`，设了才建读引擎 |
| `REDIS_ENABLED` | `false` | `true`（若要跑 Celery） | `true` | 当前 false → Celery 异步链路未通 |
| `REDIS_URL` | `redis://redis:6379/0` | `redis://localhost:6379/0`（本机跑）／`redis://redis:6379/0`（compose 内跑） | `redis://:<pwd>@<host>:6379/0` | 主机写法取决于跑在哪 |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | 同上 | `redis://:<pwd>@<host>:6379/1` | prod 建议与 result 用 db/1，和应用缓存 db/0 分开 |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | 同上 | 同上 | |
| `TASK_CONTROL_ENABLED` | `false` | 保持 `false` | 按需 | 默认关，仅控 Trace/计量副作用 |

## C2. n8n（出站分发）

| 变量 | 开发（无 n8n） | 开发（有 n8n 后） | 生产 |
|---|---|---|---|
| `N8N_SITE_BUILT_ENABLED` | `false`（默认） | `true` | `true` |
| `N8N_SITE_BUILT_WEBHOOK_URL` | 空 | `http://127.0.0.1:5678/webhook/<id>` | `https://n8n.<domain>/webhook/<id>` |
| `N8N_SITE_BUILT_AUTH_HEADER` | 空 | 可选 `X-Api-Key: <token>` | 必配 |
| `N8N_CONTENT_PUBLISH_ENABLED` | `false`（默认） | `true`（第二步再开） | `true` |
| `N8N_CONTENT_PUBLISH_WEBHOOK_URL` | 空 | `http://127.0.0.1:5678/webhook/<id2>` | `https://n8n.<domain>/webhook/<id2>` |
| `N8N_CONTENT_PUBLISH_AUTH_HEADER` | 空 | 可选 | 必配 |

> **入站（与本方案无关，别混）**：`N8N_WEBHOOK_SECRET` —— 供 `ubrain_commercial_os.py` 的 n8n 回调鉴权，未配置时该回调返回 503。

## C3. 其它需注意的环境差异

| 变量 | 开发 | 生产 | 备注 |
|---|---|---|---|
| `DEBUG` | `true` | **`false`** | |
| `JWT_SECRET_KEY` / `SECRET_KEY` | 可用示例值 | **必须重新生成** | `config/prod/.env:31` 现有一个 64 位 hex，投产前务必换掉 |
| `BROWSER_EVIDENCE_DIR` | `data/browser_evidence` | 挂持久卷路径 | 取证落盘目录，调用时读取 |
| `SKILL_PACK_SOURCES` | 默认 `business` | `business` | 设成 `business,ecc` 会纳入 286 个 ECC 工程技能，会稀释外贸匹配质量 |

---

# Part D｜验证步骤清单（可直接照抄执行）

## D1. 切换前基线（现在就能跑）
```bash
cd backend
./.venv/Scripts/python.exe scripts/orchestration_selfcheck.py
# 期望：14/14；第 1 项应显示 sqlite | 219 张表
```

## D2. 切 PG 后
```bash
# 1) 配置真的生效了（不是读到了兜底 .env）
./.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0,'.')
from app.core.config import settings
print('DB_TYPE =', settings.DB_TYPE)
print('URL     =', settings.DATABASE_URL)
" 2>&1 | grep -v UserWarning

# 2) 连通 + 表数
./.venv/Scripts/python.exe scripts/orchestration_selfcheck.py     # 第 1 项应变成 postgresql

# 3) 迁移到最新
./.venv/Scripts/python.exe -m alembic current
./.venv/Scripts/python.exe -m alembic heads      # 必须只有 1 个 head

# 4) 应用能起
./.venv/Scripts/python.exe run.py --env dev --port 8080
curl -s -m 5 -A "Mozilla/5.0" http://127.0.0.1:8080/api/v1/health
```

## D3. 启用 n8n 工作流后
```bash
# 1) 注册表里两个工作流 enabled + endpoint 都对
./.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0,'.')
from app.services.n8n.workflow_registry import get_workflow_registry, ensure_builtin_workflows
ensure_builtin_workflows()
r = get_workflow_registry()
for w in ('site_built_notify','content_publish_dispatch'):
    x = r.get(w); print(w, '| enabled=', x.enabled, '| endpoint=', x.endpoint)
"

# 2) 真实触发一次（建站任务成功后自动触发），然后看 n8n Executions 是否出现记录
# 3) 看计数
./.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0,'.')
from app.services.n8n.workflow_registry import get_workflow_registry, ensure_builtin_workflows
ensure_builtin_workflows()
print(get_workflow_registry().stats())
"
```

---

# 附：本次勘察推翻/修正的旧结论

1. **没有"PreFlight PG 硬检查"**：归档文档 `05-归档抢救-2026-08-16/overview.md` 称 `app/core/startup.py` 有 PG 连通性硬检查 —— 该文件在当前 worktree **不存在**，无此检查。
2. **Alembic 不是双 head**：实测单 head `105_reconcile_model_backfill`，迁移无阻塞。
3. **`alembic.ini` 里的 `sqlalchemy.url` 不生效**：被 `alembic_migrations/env.py` 用 `DATABASE_URL` 覆盖（误导性配置）。
4. **`主要备份/上线网站/backend/config/dev/.env` 仍是 `DB_TYPE=postgresql` + `localhost:5433`** —— 与 active worktree 的 `sqlite` 不一致。若两套后端混用，会出现"改了 worktree 但跑的是备份副本"的错位，切换前先确认**你实际启动的是哪一份**。

---

# 实施记录（2026-09-08 16:00–17:05，已执行）

> 用户确认后实施。以下为实际落地情况与方案的偏差说明。

## ✅ A. n8n 已部署接通（与方案一致，含惊喜发现）
- **惊喜**：Docker Desktop 启动后自动带起已存在容器 `optional-sidecars-n8n-1`（n8n **v2.37.10**，端口 5678）——本机本来就有 n8n，之前"不可达"只是 Docker 没开。
- 两个工作流已通过 CLI 导入并激活（`n8n-workflows/site-built-notify.json`、`content-publish-dispatch.json`，v2 导入需显式 `id` 字段；激活需 `update:workflow --active=true` + `publish:workflow` + 重启容器）。
- **实跑验证**：生产 webhook `POST /webhook/site-built-notify` 与 `/webhook/content-publish-dispatch` 均 HTTP 200；不存在的路径 404（对照证明真实注册）。n8n 执行库（WAL checkpoint 后）显示 **6 条执行全部 success**，其中一条来自 Celery 全链路。

## ⚠️ B. PG 切换的路线变更（方案内没有的路）
- **Docker 拉镜像被硬拦截**：镜像加速器 `docker.1panel.live` 失效（403/超时）；所有替代源的 blob CDN 全部 EOF（连 `hello-world` 都拉不动）；直连 `auth.docker.io` TLS 超时 → **compose 方案在本机当前网络不可行**。
- **改用原生 Windows 安装**（GitHub/EDB 直连可达）：
  - PostgreSQL 15.8 官方二进制：`C:/Users/Administrator/youding-pg/`，数据目录 `C:/Users/Administrator/youding-pgdata`，`pg_ctl` 启动 @5433，密码 youding，库 youding_dev。
  - Redis for Windows 5.0.14.1：`tools\redis\redis-server.exe` @6379（appendonly，数据目录 `C:/Users/Administrator/redis-data`）。
- **两个必须记住的坑**：
  1. **路径含中文会让 initdb 崩**（`invalid byte sequence for encoding UTF8`）——二进制与数据目录都必须在纯 ASCII 路径。
  2. **pydantic 多 env_file 是"后面的文件覆盖前面的"**：`backend/.env`（兜底）会覆盖 `config/dev/.env`！代码注释"config 优先"只在 run.py（load_dotenv→os.environ）场景成立。已把 `backend/.env` 同步为 PG（文件头有警告注释）——否则 alembic/裸跑脚本会静默打到旧 SQLite（本次实施中真实踩中：第一次"迁移成功"其实打到了 SQLite）。
- **Redis 地址必须写 `127.0.0.1` 不能写 `localhost`**：Windows 版 Redis 只绑 IPv4，`localhost` 解析到 `::1` 直接拒绝连接。
- **env 已切换**：`config/dev/.env` + `backend/.env` → DB_TYPE=postgresql、REDIS_ENABLED=true、N8N 两工作流 enabled=true（备份：`.env.bak-20260908` / `youding_dev.db.bak-20260908`）。
- **迁移与数据**：`alembic upgrade head` 全绿（PG 229 表，head=105）；按方案**不迁业务数据**，SQLite 留档可回滚；76 技能已重灌（created=76）。

## ✅ C. 端到端实证
- Celery worker 已启动（消费 celery 队列）；`trigger_n8n_workflow.delay(...)` 入队 → worker 消费 → n8n 执行 success（执行记录 id=5，mode=webhook）。
- **自检 14/14 全绿**（第 1 项=postgresql/229 表；第 6 项=两工作流 enabled=True；自检脚本已补 load_dotenv 对齐 run.py 行为）。

## 🐛 实施中修掉的新 bug
- `n8n/trigger.py:89,146`：`trigger()` 调用了不存在的模块级函数 `_build_n8n_request_headers`/`_finalize_n8n_failure`（实为实例方法）→ **此前任何真实触发都会 NameError 且被上层 except 静默吞掉**。已改为 `self.` 调用，py_compile + 实跑双验证。

## 📌 当前常驻进程（重启机器后需手动拉起）
| 进程 | 启动方式 |
|---|---|
| PostgreSQL 15.8 @5433 | `C:/Users/Administrator/youding-pg/bin/pg_ctl.exe -D C:/Users/Administrator/youding-pgdata -o "-p 5433" start` |
| Redis @6379 | `tools\redis\redis-server.exe --port 6379 --appendonly yes --dir C:/Users/Administrator/redis-data` |
| n8n @5678 | Docker Desktop 启动后自动（容器 restart=unless-stopped） |
| Celery worker | `cd backend && ./.venv/Scripts/python.exe -m celery -A app.tasks.celery_app worker -Q celery -l info`（需带 N8N_*/REDIS env 或经 run.py 环境） |

---

# 服务器部署对照清单（本地 → 生产，2026-09-08 补充）

> 本文档前面记录的是**本机开发环境**的实施。以下为将来部署到服务器时需要做的事：哪些照搬、哪些必须改。

## 一、本地实施 → 服务器的映射总表

| 组件 | 本地（Windows 开发机） | 服务器上怎么做 | 变更程度 |
|---|---|---|---|
| PostgreSQL 15 | 原生二进制 `youding-pg\` @5433 | Linux 上**用 Docker**（`pgvector/pgvector:pg15` 或官方 `postgres:15`），服务器网络正常时 compose 直接可拉 | 换形态，数据无关 |
| Redis | Windows 版 redis-server @6379 | Docker `redis:7-alpine` 或云托管 Redis | 换形态 |
| n8n | 已有容器 `optional-sidecars-n8n-1` @5678（本机 Docker） | 服务器单独跑 n8n 容器/云服务；**工作流 JSON 直接复用**（`n8n-workflows/` 目录两个文件，CLI 导入命令一样） | 只迁移 2 个 JSON |
| Celery worker | 本机手动启动 | 服务器 systemd service / supervisor / 容器编排，**常驻** | 换启动方式 |
| Alembic | 本地已升到 head=105（229 表） | 服务器空库跑 `alembic upgrade head`，或用 `pg_dump`/`pg_restore` 直接搬本地库 | 命令一致 |

## 二、env 必改项（生产 vs 当前 dev 值）

| 变量 | 当前 dev 值 | 生产必改为 | 原因 |
|---|---|---|---|
| `ENVIRONMENT` | development | production | 行为开关 |
| `DEBUG` | true | **false** | 安全 |
| `SECRET_KEY` / JWT 相关 | 开发默认 | **重新生成强随机值** | 泄露即全站失守 |
| `DATABASE_URL` | `postgresql://youding:youding@127.0.0.1:5433/youding_dev` | 独立账号+强密码，库不用 `_dev` 后缀；容器内网则写服务名（如 `postgres:5432`） | 不得复用弱口令 |
| `REDIS_URL` / `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/...` | 服务器上若同机可保留 127.0.0.1；跨机/容器写服务名+密码 | 网络拓扑 |
| `N8N_*_WEBHOOK_URL` | `http://127.0.0.1:5678/webhook/...` | n8n 实际地址（同机可 127.0.0.1，跨机写内网 IP/域名；对外暴露必须 HTTPS + n8n webhook 鉴权头） | 与部署拓扑一致 |
| `N8N_WEBHOOK_SECRET`（入站） | 未设 | **必设**（否则 n8n 回调 UJ 时返回 503） | 入站鉴权 |
| `CORS_ORIGINS` 等域名类 | localhost:3000 | 真实域名 | — |

## 三、★ 最重要的一条：env 优先级坑在服务器上同样存在

- `backend/.env` 会**覆盖** `config/prod/.env`（pydantic 多 env_file 后者覆盖前者）。
- 服务器上要么**只放一份** `config/prod/.env`（删掉/不部署 `backend/.env`），要么两份严格同步。二选一，不要凭代码注释猜优先级。
- `run.py --env prod` 场景（load_dotenv → os.environ）下优先级才与注释一致，但仍建议单一 env 源。

## 四、服务器部署步骤概要

1. **装 Docker**（服务器网络正常，无本机镜像墙问题）→ `docker compose` 起 `postgres` + `redis` + `n8n`（可基于 `docker-compose.dev.yml` 改出 prod 版：去掉端口对宿主机裸暴露、加 healthcheck、加 volume）。
2. **n8n**：导入 `n8n-workflows/` 两个 JSON → `update:workflow --active=true` + `publish:workflow` → curl 验证 `/webhook/` 路径 200。
3. **后端**：上传代码 → 建 `config/prod/.env`（按上表）→ `.venv` 装依赖（`psycopg2` 已在依赖内）→ `alembic upgrade head` → 首次 `seed_skill_pack` 灌 76 技能。
4. **数据迁移（可选）**：本地库要搬的话 `pg_dump -Fc youding_dev` → 服务器 `pg_restore`；**不要 dump/restore `alembic_version`**（见方案 Part B 回滚说明）。
5. **Celery**：systemd 常驻 worker + beat，env 与后端一致。
6. **反代/HTTPS**：Nginx/Caddy 挂 443，n8n 若对外必须 HTTPS。

## 五、部署后验证清单（照抄执行）

```bash
# 1. DB 就绪且表数正确
psql "$DATABASE_URL" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"   # 应 229
# 2. alembic 到 head
python -m alembic current   # 应 105
# 3. n8n webhook
curl -X POST https://<n8n地址>/webhook/site-built-notify -H 'Content-Type: application/json' -d '{"probe":1}'   # 200
# 4. 后端→n8n 出站（在 backend venv 内，env 已配好的 shell 下）
python -c "from app.services.n8n.trigger import N8nTriggerService; s=N8nTriggerService(timeout=15,max_retries=1); print(s.trigger_sync('site_built_notify',{'probe':'deploy-check'}))"
# 5. Celery 消费
# delay() 一条后看 n8n Executions 出现新记录
# 6. 自检
python scripts/orchestration_selfcheck.py   # 14/14，第 1 项 postgresql、第 6 项 enabled=True
```

## 六、本地/服务器职责总结

- **本地保留**：开发用 PG@5433 + Redis@6379 + n8n@5678 全套已跑通，继续日常开发即可；`config/dev/.env` 与 `backend/.env` 已同步为 dev 专用值。
- **服务器新增**：只需按本文二~五节重建一遍（约半天工作量），两个 n8n 工作流 JSON 与 Alembic 迁移链可直接复用，无需重做勘察。
