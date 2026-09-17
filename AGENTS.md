# 开发协作入口

改代码前 **先读仓库内契约**，不要凭记忆或旧文档恢复已删除能力。

## 硬锁：管理端登录（LOGIN-LOCK-01）

| 项 | 值 |
|----|-----|
| 契约 JSON | `.project/login-entry-lock.json` |
| 说明文档 | `docs/product/LOGIN-SINGLE-ENTRY-CHARTER.md` |
| 唯一登录路由 | `/login` |
| 唯一登录组件 | `frontend/admin/src/views/login/index.vue` |
| 文案模块 | `frontend/admin/src/constants/loginPortalCopy.ts` |
| 产品图片空间 | 超管 `/admin/file-manager` · 租户 `/client/product-images` · `constants/productImageSpace.ts` |

**禁止：**

- 新建第二套登录 Vue 页（含 `client/login.vue`、四门户 `?portal=`）
- 恢复 `DEV_PORTAL_CREDENTIALS` / `normalizeLoginPortal` / 多门户 `LOGIN_PORTAL_COPY`
- 按 `docs/meetings/ECC-LOGIN-GLASS-PORTAL-PM-DESIGN-MKT.md` 做四门户（已废止）

**改登录/路由/Landing 登录链后必跑：**

```powershell
powershell -File scripts/verify-login-entry-lock.ps1
```

## 硬锁：角色壳入口（ROLE-SHELL-LOCK-01）

**先读：** `.project/role-shell-lock.json` · `frontend/admin/src/constants/roleShellLock.ts`

| 你要找的 | 路由 | 代码目录 | 开发账号 |
|----------|------|----------|----------|
| **租户自用后台** | `/client/*`，首页 `/client/today` | `frontend/admin/src/views/client/` | `tenant` / `tenant123` |
| **超管管 SaaS 租户** | `/admin/tenants` 或 `/tenants/dashboard` | `views/tenants/dashboard.vue` | `admin` / `admin123` |
| **区域代理** | `/agent/*` | `views/agent/` | `agent` / `agent123` |
| **平台超管工作台** | `/admin` | `views/admin/` | 同上 |
| **唯一登录页** | `/login`（全员共用，外观是运营控制台） | `views/login/index.vue` | 登录后按 JWT 角色自动分流 |

**禁止误建：**

- `views/admin/tenants.vue`（wrapper，已废止）
- `views/client/login.vue`、`views/tenant/**`、第二套 login 页

验证：`npm run cert:role-shell-lock`（已接入 `cert:gate`）

## 硬锁：设计令牌单一真源（DESIGN-TOKEN-LOCK-01）

平台主色 = **薄荷绿 `#4a9b8c`**（运行时权威 `frontend/admin/src/stores/uiPreferences.ts` 的 `PLATFORM_BRAND_DEFAULT`；旧紫 `#7c3aed` / 蓝灰 `#6f93ab` 已迁移）。所有前端令牌必须收敛到这一颗薄荷，禁止再出现多主色混用。

| 层 | 唯一真源 | 说明 |
|----|----------|------|
| 营销站 `--color-primary` | `frontend/assets/css/main.css` `:root` | 已统一为 `#4a9b8c`（原近黑 `#0f172a` 已废除） |
| 营销站 Tailwind `primary` | `frontend/tailwind.config.ts` | 已统一为薄荷色板（原蓝 `#3b82f6` 已废除） |
| 后台静态主色 | `frontend/admin/tailwind.config.js` `primary` | 已统一为薄荷色板（原 sky `#0ea5e9` 已废除） |
| 后台运行时主色 | `--uj-brand` / `mint-glass-shell.scss` | 运行时权威，覆盖一切 |
| 语义功能色 | success `#10b981` / warning `#f59e0b` / danger `#ef4444` / info `#2563eb` | 前后端共用同一组值 |

**禁止：**

- 新增/改 `--color-primary` / `--saas-primary` / `--b2b-primary` / Tailwind `primary` 为**非薄荷**值（蓝 `#2563eb`、近黑 `#0f172a`、teal `#0f766e`、紫 `#7c3aed`、橙 `#ea580c`）
- 在 `style.css` / 组件里把主操作色硬编码为 `bg-[#2563eb]`、`#7c3aed`、`#ea580c`（`.btn-primary` 已改薄荷；`.gradient-secondary` 紫 / `.gradient-accent` 橙 已删除）
- 恢复后台 `secondary`=紫、`accent`=橙 的旧色板
- 重新引入 `@nuxtjs/color-mode` 暗色切换（2026-07-18 移除：仅注册无样式、切换无效；完整暗色需作为独立项目实现）

**改令牌/配色后自检：** `grep -rn "#2563eb\|#7c3aed\|#ea580c\|#0f172a" frontend/assets frontend/admin/src` 应无「主操作色」残留（链接/信息蓝 `#2563eb` 作为 info 语义允许保留）。

## 工作区隔离

见 `docs/DEV-TOOLS-ISOLATION.md`：

- 产品代码：`backend/` `frontend/` `deploy/` `docs/` `scripts/` `.project/`
- 勿把本地 IDE 配置、代码索引提交入库

## 本地开发

```powershell
powershell -File scripts/start-dev-admin.ps1
```

- API `http://127.0.0.1:8001`
- Admin `http://127.0.0.1:5173/login`
- 超管 `admin / admin123` → `/admin`
- 租户 `tenant / tenant123` → `/client/today`
- 代理 `agent / agent123` → `/agent/performance`

**稳定性（必读）：**

- **禁止**手敲 `uvicorn` 起后端（易漏 `REDIS_ENABLED=false`，全站变慢/转圈）
- 异常时：`powershell -File scripts/start-dev-admin.ps1 -ForceRestart`
- **联机/第二台笔记本/手机**：`powershell -File scripts/start-dev-lan.ps1 -ForceRestart`，浏览器用 `http://<本机192.168.x.x>:5173/login`（勿用 127.0.0.1 或 172.26.x）
- 自检：`powershell -File scripts/verify-dev-admin-stack.ps1`
- 开发壳内 API 未响应时会顶栏提示；单请求 15s 超时，不会无限转圈

## 租户预览 SEO 审计（TENANT-SEO-AUDIT）

| 场景 | 入口 |
|------|------|
| **本地预览站**（`lpro=1`） | `powershell -File scripts/run-tenant-seo-audit.ps1` |
| **公网已上线 URL** | Admin `/seo/site-audit` → `POST /api/v1/seo/site-audit` |
| **dev 冒烟** | 已接入 `scripts/smoke-gap-closure-dev.py` |
| **GEO/AEO 审计** | `powershell -File scripts/run-tenant-geo-audit.ps1` |
| **每周闭环** | `powershell -File scripts/run-weekly-seo-geo-loop.ps1` |
| **周一挖词** | `python scripts/run-seo-keyword-discover.py` → `docs/ops/seo-keyword-discover-latest.json` |
| **计划任务安装** | `powershell -File scripts/install-weekly-seo-geo-task.ps1` |
| **报告** | `docs/tenant-seo-audit-latest.json` · `docs/tenant-geo-audit-latest.json` |
| **统一 GEO 分** | `GET /api/v1/public/tenants/{domain}/geo-score`（schema `unified-geo-v1`） |
| **租户 llms.txt** | `http://127.0.0.1:3000/llms.txt?__tenant=dev.local` |

前提：Nuxt `:3000` + API `:8001` 已起；预览 URL 形如 `http://127.0.0.1:3000/tenant?__tenant=dev.local&lpro=1`。

跑租户 SEO 审计：`powershell -File scripts/run-tenant-seo-audit.ps1`，按 P0/P1 修 title/meta/visitor-context。

外部 GEO/商务方案对照（Medusa、GEO Optimizer、Edge Middleware 等）：[`docs/integrations/external-geo-commerce-alignment.md`](docs/integrations/external-geo-commerce-alignment.md)

## 硬锁：后端运行环境（ENV-LOCK-01，2026-09-08 起）

**改后端环境 / 连数据库 / 动 n8n 前，先读：**

| 文档 | 位置 |
|------|------|
| 强制索引（30 秒版，端口/env 铁律/红线） | `../../后端运行环境强制索引-必读.md`（工作区根） |
| 开发交接记录（完整断点快照） | `../../docs/开发交接记录-n8n接通与PostgreSQL切换_2026-09-08断点.md` |
| 实施方案 + 服务器部署清单 | `../../docs/n8n工作流与SQLite切PG-实施方案-2026-09-08.md` |

**速记铁律：** ① `backend/.env` 覆盖 `config/dev/.env`，改环境两份同步改；② `DB_TYPE` 与 `DATABASE_URL` 成对改；③ Redis 写 `127.0.0.1` 不写 `localhost`；④ 当前是原生 PG 15.8 @5433（229 表，head=105），不是 SQLite；⑤ n8n 两工作流已启用勿禁；⑥ 自检 `python scripts/orchestration_selfcheck.py` 应 14/14。
