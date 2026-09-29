# 开发交接记录 —— n8n 出站链路接通 + 开发环境 SQLite→PostgreSQL 切换（2026-09-08 断点）

> 生成时间：2026-09-08 17:20（GMT+8）；编写：小鹅（WorkBuddy）
> 用途：**让下一个 Agent / 其他编程 IDE 不重建、不跑偏、不踩已踩过的坑地接续工作**。
> 配套文档：
> - `../后端运行环境强制索引-必读.md`（工作区根，30 秒版环境红线，**IDE 接手先读这份**）
> - `n8n工作流与SQLite切PG-实施方案-2026-09-08.md`（勘察方案 + 实施记录 + **服务器部署对照清单**）
> - 勘察产物基于开发真相源 worktree：`上线网站.worktrees/agents-install-vscode-cline-deploy-strix/backend`

---

## 〇、30 秒速览（当前状态一句话）

**后端开发环境已从 SQLite 切换到原生 PostgreSQL 15.8（@5433），Redis（@6379）已启用，n8n（@5678，本机 Docker）两个出站工作流已接通并端到端实证，自检 14/14 全绿。** 数据未迁移（SQLite 留档，可秒级回滚）。Docker 拉镜像在本机被硬拦，故 PG/Redis 采用原生 Windows 安装——这是权宜形态，**生产服务器仍按部署清单用 Docker**。

---

## 一、断点 snapshot（已实测核实）

| 项 | 当前状态 | 证据 / 位置 |
|---|---|---|
| 数据库 | **PG 15.8 原生安装**，`postgresql://youding:youding@127.0.0.1:5433/youding_dev`，**229 张表**，head=105 | `C:\Users\Administrator\youding-pg\`（二进制）、`C:\Users\Administrator\youding-pgdata\`（数据目录） |
| Redis | **Windows 版 5.0.14.1 @6379**，appendonly，数据目录 `C:\Users\Administrator\redis-data\` | `tools\redis\redis-server.exe` |
| n8n | **v2.37.10**，容器 `optional-sidecars-n8n-1` @5678，随 Docker Desktop 自启；两个工作流已激活 | 工作流 JSON：`worktree/n8n-workflows/`（site-built-notify / content-publish-dispatch） |
| Celery worker | 本机已启动消费过队列（端到端实证完成）；**无常驻机制，重启机器后需手动拉起** | 启动命令见强制索引 |
| env（两份已同步） | `config/dev/.env` 与 `backend/.env` → DB_TYPE=postgresql、REDIS_ENABLED=true、N8N 两工作流 enabled=true、redis 地址用 `127.0.0.1` | 备份：`config/dev/.env.bak-20260908`、`youding_dev.db.bak-20260908` |
| 自检 | `scripts/orchestration_selfcheck.py` **14/14**（第 1 项 postgresql/229 表、第 6 项 enabled=True）；脚本已补 load_dotenv | worktree backend |
| 业务数据 | **未迁移**：SQLite `youding_dev.db`（4.9MB）留档为 `youding_dev.db.bak-20260908`，PG 是干净结构 + 76 技能 | — |

---

## 二、本轮完成的事（A/B/C 三步全部实证）

### A. n8n 出站链路接通 ✅
1. Docker Desktop 启动后自动带起**已存在**的 n8n 容器（`optional-sidecars-n8n-1`）——之前"5678 不可达"只是 Docker 没开。
2. 通过 CLI 导入两个 Webhook 工作流并激活：`n8n import:workflow --input=...`（**v2 导入必须带顶层 `id` 字段**）→ `n8n update:workflow --id=... --active=true` → `n8n publish:workflow` → `docker restart`。
3. 验证：`POST /webhook/site-built-notify` 与 `/webhook/content-publish-dispatch` 均 HTTP 200；不存在路径 404（对照证明真实注册）。
4. 后端侧开关：`N8N_SITE_BUILT_ENABLED=true` + `N8N_SITE_BUILT_WEBHOOK_URL`、`N8N_CONTENT_PUBLISH_ENABLED=true` + `N8N_CONTENT_PUBLISH_WEBHOOK_URL`（registry 直读 `os.environ`，**改 env 必须重启 API/worker/beat**）。

### B. SQLite → PostgreSQL ✅（路线变更：原生安装）
- Docker 拉镜像全链被拦（1panel 加速器 403、daocloud/1ms 等 blob CDN 全断流、直连 auth.docker.io TLS 超时）→ compose 路线在本机**当前不可行**。
- 改用原生安装：PG 15.8 官方二进制（EDB）+ Redis for Windows（tporadowski 5.0.14.1），下载源 GitHub/EDB 直连可达。
- `alembic upgrade head` 001→105 全绿（229 表）；`seed_skill_pack` 重灌 76 技能（created=76）。
- 迁移中确认：020 迁移是 pgvector 守卫式空操作，迁移链无 vector 硬依赖（原生 PG 可跑）。

### C. 端到端实证 ✅
- 直连：`N8nTriggerService.trigger_sync()` → n8n HTTP 200（双工作流）。
- 全链路：`trigger_n8n_workflow.delay()` → Celery worker 消费 → n8n 执行 success（n8n 执行库 6 条记录全 success；**查库必须连 `-wal` 文件一起拷**，否则看到的是空表假象）。

---

## 三、本轮修掉的 bug 与新增防护

| # | 问题 | 修复 |
|---|---|---|
| 1 | **`app/services/n8n/trigger.py:89,146`**：`trigger()` 调用不存在的模块级函数 `_build_n8n_request_headers`/`_finalize_n8n_failure`（实为实例方法）→ **此前任何真实出站触发都 NameError 且被上层 except 静默吞掉** | 改为 `self.` 调用，py_compile + 实跑双验证 |
| 2 | `scripts/orchestration_selfcheck.py` 裸跑时 n8n registry 误显示 enabled=False | 脚本头补 `load_dotenv`（对齐 run.py 行为） |
| 3 | `backend/.env` 头部已加**警告注释**说明覆盖关系（见红线 1） | 已写入 |

---

## 四、红线（违反任一条会直接翻车，全部实测踩中过）

1. **★ `backend/.env` 会覆盖 `config/dev/.env`**（pydantic 多 env_file 是"后面的覆盖前面的"，代码注释写反了）。改环境必须**两份同步改**，或干脆只信 `backend/.env`。本轮第一次"迁移成功"其实打到了旧 SQLite，就是这个坑。
2. **PG 的二进制目录与数据目录必须在纯 ASCII 路径**。路径含中文 → `initdb` 报 `invalid byte sequence for encoding UTF8` 直接崩。
3. **Redis 地址必须写 `127.0.0.1` 不能写 `localhost`**：Windows Redis 只绑 IPv4，`localhost` 解析到 `::1` 直接拒连。
4. `alembic.ini` 的 `sqlalchemy.url` 是**死配置**（被 `alembic_migrations/env.py` 用 `DATABASE_URL` 覆盖）；代码无 create_all，空库必须 `alembic upgrade head`。
5. `app/core/startup.py` 及其"PreFlight PG 硬检查"在当前 worktree **不存在**（归档文档过时，别去找）。
6. `_init_db_type_validation` 强制 `DB_TYPE` 与 `DATABASE_URL` 协议一致，不一致 ValueError 拒绝启动——**两行必须成对改**。
7. 驱动只有 psycopg2（asyncpg 未装）：URL 只能 `postgresql://` 或 `+psycopg2`。
8. FastAPI 路由枚举陷阱：`_IncludedRouter` 无 `.router`（真字段 `original_router`），数 APIRoute 条数恒为 0 是测量假象；**401/403=已挂载，404 才是未挂载**。
9. 不要把 n8n 工作流重新禁用：后端已在真实任务里调用（hermes_task_bridge / deerflow executor 两处触发点）。
10. 探测本机端口时 curl 带浏览器 UA（WAF 拦"恶意 User-Agent"）+ `--noproxy "*"`。

---

## 五、重启机器后的常驻进程拉起（按序）

```powershell
# 1. PostgreSQL @5433
C:\Users\Administrator\youding-pg\bin\pg_ctl.exe -D C:\Users\Administrator\youding-pgdata -o "-p 5433" start

# 2. Redis @6379
C:\Users\Administrator\Documents\上线网站开发完成\tools\redis\redis-server.exe --port 6379 --appendonly yes --dir C:\Users\Administrator\redis-data

# 3. n8n @5678 —— 启动 Docker Desktop 即自动（容器 restart 策略）

# 4. Celery worker（在 worktree backend 下，env 已在 .env 内）
cd 上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend
.venv\Scripts\python.exe -m celery -A app.tasks.celery_app worker -Q celery -l info

# 5. API（run.py 走 load_dotenv，env 优先级才与注释一致）
.venv\Scripts\python.exe run.py --env dev --port 8000
```

自检：`python scripts/orchestration_selfcheck.py` → 14/14；`pg_isready -h 127.0.0.1 -p 5433`；`redis-cli -p 6379 ping`；`curl http://127.0.0.1:5678/healthz`。

---

## 六、回滚方式（秒级）

1. `config/dev/.env.bak-20260908` 覆盖回 `config/dev/.env`，**同时**把 `backend/.env` 的 DB/Redis 段改回 sqlite（两份同步！）。
2. 重启 API/Celery。SQLite 文件全程未动（`youding_dev.db.bak-20260908` 就是原库副本）。

---

## 七、下一步候选

1. **服务器部署**：按《n8n工作流与SQLite切PG-实施方案-2026-09-08.md》末尾「服务器部署对照清单」执行（Docker 化 + 生产 env 必改项 + 验证清单，约半天）。
2. n8n 工作流加鉴权头（`N8N_*_AUTH_HEADER`）与真实业务节点（当前是 Webhook→noOp 骨架）。
3. Celery worker 常驻化（Windows 服务 / 计划任务 / 或服务器上 systemd）。
4. 其余 32 处 N+1 查询继续优化（见记忆/TODO）。
