# 交接给 cowork 会话 — 优丁 B2B AI Revenue Engine 已完成工作交接

> 用途：让并行运行的 cowork 会话拿到本会话（2026-08-29）已完成的工作，避免重复劳动，专注剩余 4 项。
> 生成时间：2026-08-29 12:50
> 真实代码库：`主要备份\上线网站`（注意：工作目录的 `上线网站` 是空壳，`上线网站.worktrees` 是 7-22 旧代码）

## ⚠️ 先读这个（避免重复劳动）

**以下工作本会话已全部完成，cowork 不要重复做：**

### 1. 完成度核查（已更新盘点文档）
- [项目完成度盘点.md](C:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\项目完成度盘点.md) 已全面更新为真实完成度。
- 关键结论：代码层约 90%（后端 177 路由、150+ 模型、100+ 服务、83 迁移、前端几十页），核心闭环「产品→匹配→RFQ→落库→自动建销售任务」已在真实服务器端到端验证通过。

### 2. 已修复的两个真实 bug
- **matching 路由从未挂载**：`backend/app/api/v1/routes/__init__.py` 已补 `matching_router` 的 import + `include_router(prefix="/matching")`。修复前 `POST /api/v1/matching/product-match` 返回 404。
- **SQLite UUID 绑定崩溃**：`backend/app/core/database.py` 已注册 `sqlite3.register_adapter(uuid.UUID, str)`。修复前 POST /rfq 报 `type 'UUID' is not supported`（500）。

### 3. 已补建 24 张 ORM-only 表（对 live 库执行 create_all）
- 备份：`主要备份\上线网站\youding_dev_pre_migration_20260829_093507.bak`
- 表数 247 → 271，新增 rfqs / rfq_items / rfq_requirements / rfq_documents / opportunities / opportunity_stages / campaigns / campaign_steps / campaign_recipients / companies / company_signals / projects / project_signals / ai_queries 等

### 4. 端到端验证（真实运行服务器 + 前端代理）
- 后端 :8000（DB_TYPE=sqlite） + 前端 :3000（Vite，代理 /api→8000）
- 经前端代理实测：首页 200 / matching 200 / rfq 200；rfqs 落库 + sales_tasks 自动创建
- 测试数据已清理，服务已停止，端口已释放

## 剩余 4 项（cowork 负责）

| # | 项 | 说明 | 关键文件/命令 |
|---|---|---|---|
| 1 | **迁移 080 补跑** | SQLite 已用 create_all 建表，但 `080_add_phase1_revenue_engine_tables.py`（414行，定义 18 张核心 Revenue 表）从未执行；`alembic_version` 停在 068 | `cd backend && .venv\Scripts\python.exe -m alembic upgrade heads`（注意 SQLite 会报 UUID 类型错误，需先确认适配已生效） |
| 2 | **种子数据充实** | products 仅 8 行、quotes 3 行，需真实业务数据支撑商业演示 | `backend/seed_products.py`、`backend/seed.py` |
| 3 | **rfqs 主表 Postgres 迁移** | 080 只建了 rfq_requirements/rfq_documents 子表，rfqs 主表靠 ORM create_all（上 Postgres 会缺） | `backend/alembic/versions/` 需为 rfqs 补 create_table |
| 4 | **模型缺对应类** | product_standards / seo_pages 在 080 定义了表，但 ORM 模型无对应类（SQLite create_all 建不出） | `backend/app/models/` 需补模型 |

## 环境事实（cowork 开工前必读）

- 后端启动：`cd backend && DB_TYPE=sqlite REDIS_ENABLED=false .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 前端启动：`cd frontend && API_HOST=http://127.0.0.1:8000 npm run dev`（:3000）
- **本机未装 PostgreSQL**（规划文档指定 Postgres 技术栈，开发全程 SQLite fallback）——若做 Postgres 相关迁移，需先决定是否要装/起 Postgres
- 后端 venv：`backend\.venv`；live 库：`主要备份\上线网站\youding_dev.db`（SQLite，alembic_version=068）
- 前端实际是 Vite（非 Nuxt），`useApi.ts` 的 baseURL 是 `/api/v1`

## 建议的分工衔接

- **建议先做第 1 项（迁移 080）**：这是唯一可能影响数据库一致性的项，且和本会话已建的表相关。跑前先确认 `alembic_version` 当前值、以及 SQLite 下 UUID 适配是否生效（本会话已修复 database.py）。
- 若你（cowork）要上 Postgres 验证完整迁移链，需先装 Postgres——这是环境决策，建议和用户确认。