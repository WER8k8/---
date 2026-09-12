# PROJECT INDEX · 优丁 B2B 外贸 SaaS（活跃开发版）

> **给任何 IDE / AI 编码工具**：本文件是代码级全貌索引，读完即可开工，无需全盘扫描。
> 由每日自动化维护校正（规模数字 + 最近变更段）。最后更新：2026-09-06

## 技术栈

- **后端**：FastAPI + SQLAlchemy 2.0 + Pydantic v2 + Celery + Redis + Alembic（Python venv：`backend/.venv/Scripts/python.exe`）
- **官网前端**：Nuxt 3（`frontend/`，:3000）
- **超管后台**：Vite + Vue3 + TS + Ant Design Vue（`frontend/admin/`，:5174）
- **SEO 双系统**：`seo-backend/`（Node，:8000 独立实例）+ `seo-admin/`（:5173）
- **基础设施**：PostgreSQL(:5433 Docker pgvector/pg15) + Redis(:6379) + Temporal(:7233) + n8n(:5678)

## 后端结构（backend/app/，17 个子模块）

| 模块 | 职责 | 规模 |
|------|------|------|
| `api/v1/` | REST 路由层 | **146 个路由模块（自动发现机制）**，OpenAPI **1,240 路径 / 1,370 个操作** |
| `services/` | 业务逻辑层 | **297 顶层项 / 660+ py 文件**（含跨境、获客闭环、U-Brain、智能建站、国际支付等） |
| `models/` | SQLAlchemy ORM | **200 张数据表**（Base.metadata 完整定义），Alembic 单 Head `105`（迁移链 001→105 全绿；104=租户回填，105=模型兜底合流（链尾 create_all 幂等补缺表）；见 backend/.scratch/adr-002-multi-tenant-runtime/issues/10） |
| `schemas/` | Pydantic v2 请求/响应模型 | — |
| `repositories/` | 数据访问层 | — |
| `tasks/` | Celery 任务 | **12 个任务模块**，7 队列：celery,default,deerflow,cross_border,ops,seo,geo |
| `workers/` | 后台 worker | — |
| `core/` | 配置/安全/日志（config.py, security, logging_config） | — |
| `db/` | 会话/RLS 策略 | — |
| `domains/` | 租户域名/多租户路由（tenant_middleware 主站白名单在此） | — |
| `geo_engine/` | GEO 生成引擎（融合 geolook-0.2.0） | — |
| `orchestration/` | 编排（含 Temporal 工作流） | — |
| `data/` | 静态数据（deerflow_research_brief_templates 等） | — |
| `graduation/` `performance/` | 毕业机制/性能模块 | — |
| `main.py` | 应用入口（lifespan 300 行，注册 4268 接口） | — |

**关键机制**：路由自动发现（`app/api/v1/routes/__init__.py` + `auto_discovery.py` 双机制）；多租户靠 Host 头识别；统一登录 `resolve_user_for_unified_login` 贯通主库 users 与 SEO 矩阵 admin_users。

## 前端结构

- `frontend/`（官网 Nuxt 3）：components / composables / layouts / locales（i18n）/ middleware / pages
- `frontend/admin/`（超管）：src 下 api / components / router / layout / constants；路由表 `adminSystemRoutes.ts`
- API 客户端由 **Orval** 自动生成

## 启动（三种方式任选）

```bat
:: 1) 工作区一键启动（推荐，含依赖编排+端口自检）
..\..\启动脚本\youding-dev-start.bat

:: 2) 工作区 npm scripts（工作区根目录）
npm run backend | frontend | admin | seo:backend | seo:admin

:: 3) 手动后端（注意必须用项目 venv，系统 python 没装依赖）
cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

后端启动链：加载 `config/dev/.env` → `alembic upgrade heads` → 种子脚本 → uvicorn。Docker 依赖：`docker-compose -f docker-compose.dev.yml up -d postgres redis`（注意本机用**连字符版** docker-compose）。

## 环境配置

- 开发：`backend/config/dev/.env`（真实值）
- 生产模板：`backend/config/.env.prod.example`（**AI Key 一律留空，严禁编造**）
- OAuth 开发模式：`OAUTH_DEV_BYPASS`（登录页 `client/login.vue`，注册页 `tenants/register.vue`）

## 顶层关键文档

`AGENTS.md`（AI 助手约定）· `DEPLOY.md`（部署）· `POSTGRESQL_SETUP.md` · `IMPLEMENTATION-TRACKER.md`（进度）· `GB25000-Compliance-Checklist.md`（合规）

## 已知注意事项（踩坑记录）

1. 本机 Docker 命令只支持 `docker-compose`（连字符），`docker compose`（空格）不可用
2. npm 会吞 `--host/--port`，前端启动须直接调 `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port X --strictPort`
3. 项目代码树内**禁止存放备份文件**（.bak/backups 已清理至工作区 `_archive/worktree备份-20260904/`，含来源路径清单）
4. DeerFlow 是 celery 任务模块（订阅 deerflow 队列），不是独立 Docker 栈，无独立端口

## 最近变更（自动化滚动更新区）

- 2026-09-06：认证/Cookie 安全链路更新（admin_bff/auth_adapter、routes/auth、csrf_middleware、jwt_cookie、core/security）+ U-Brain Accio 销售服务（accio_sales_service）+ routes/news + services/ai_engine，共 11 个后端文件；前端无改动
- 2026-09-05：U-Brain 邮件外联链路 + 支付订单/平台账户 + 核心层 cache/database/logging（22 个 py 改动）；services 规模口径修正为"297 顶层项 / 660+ py"
- 2026-09-04：备份类文件大清理（16 项归档至工作区 _archive）；修复路由自动发现注册报错（auto_discovery 跳过空前缀 + product_commerce 拼写 + 网关端口 5174/8000），commit c1f74b7
- 2026-09-06：租户端全面测试 + 7 个 bug 修复轮 26——auth cookie 哨兵值'bearer cookie'(核心)、bff_logout 500、logout 竞态、refresh 旧 rt 401、重复 cookie 间歇 401、产品 307 Location 跨域、产品路由被 tenant 守卫弹回。修改文件：auth_adapter/routes/auth/csrf_middleware/jwt_cookie/core/security + stores/auth/api/index/utils/api/api/authRefresh + router/index + views/products/*（3个）+ vite.config.ts。干净链路：vite 5180→uvicorn 8600
