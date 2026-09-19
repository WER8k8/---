---
feature: hermes-drive-chain-deep-dive
status: in-progress
updated: 2026-09-20
branch: feat/hermes-deep-dive
commits: 
---

# Hermes 驱动链路深挖（四轨完整体）

## Report

## [S1] Problem
Hermes 驱动链路已能 L1 派发且任务中心可读，但深挖仍有隔阂：① 节点级业务结果未系统分类（配置缺 vs 代码洞 vs 诚实降级），`knowledge_seo` 等场景节点质量不稳；② GP-B 仅有 API，社媒拓客功能域无「一键触达 · Hermes」；③ 询盘页 PI 仍走交互接口，未接任务面 GP-A；④ GoodJob/TradeAI 真桥与本地进程未收口，`GOODJOB_BASE_URL`/TradeAI:8010 缺失时应诚实 failed 且可本地验证。

## [S2] Design

### 双平面与黄金路径（不变）
- 交互 CRUD → 优丁 API 同步；多步/外发/单证 → Hermes L1（DSH 非必经）。
- GP-A：`POST /api/v1/orchestration/golden-path/fulfillment` → `_fulfillment_graph`。
- GP-B：`POST /api/v1/orchestration/golden-path/outreach` → `_social_outreach_graph`（trade_ai_agent 三能力）。
- 任务中心：`/client/tasks`；plan_id = TaskGraph.plan_id；详情兼容 `plan:{id}`。
- 无特权：菜单为业务功能域名；禁止附属第二登录/特权壳。

### 轨 A · L1 节点业务闭环
- 验收不只 `dispatched=true`：复跑 S1–S16，记录每节点 `status ∈ {succeeded, degraded, failed, skipped}` 与 error 语义。
- 允许：`degraded`+说明、`failed`+`not_configured`/`bridge_disabled`/明确业务错误。
- 禁止：5xx 裸崩、静默 success、死代码 except 吞掉真实错误路径。
- 代码契约：
  - `content_deep.seo_meta`：引擎不可用 → 模板 `degraded`（如实）；缺 product_name → `failed`；**移除不可达的第二 except**。
  - `content_deep.knowledge`：队列存储不可用 → `degraded` 摘要（pending=0 + note），不整图 failed。
  - `content_deep.acquisition`：缺 content_id/inquiry_id → `degraded` honest skip（已具备）。
  - 其余 drive-chain 执行器：沿用诚实 failed/degraded，不假成功。

### 轨 B · GP-B 功能域前端
- 落点：`frontend/admin/src/views/annex/AnnexEmbedPage.vue`（社媒拓客 `annexKey=trade-ai`）+ 可选获客作战台入口。
- 行为：按钮「一键触达 · Hermes」→ `POST /orchestration/golden-path/outreach`，payload 支持 keyword/country；成功后 `router.push(/client/tasks?plan=<plan_id>)`；失败展示后端 error（含 honest not_configured）。
- API 客户端：在 `api/orchestration.ts` 补 `goldenPathOutreach` / `goldenPathFulfillment`（与 GP-A 履约页同一 unwrap 语义）。

### 轨 C · 询盘第二路径（任务面 PI）
- 落点：`views/client/queues/inquiries.vue` 详情动作区。
- 保留交互「生成 PI」（inquiryProforma）；**新增**「Hermes 履约」→ `golden-path/fulfillment`，payload 含 `inquiry_id/name/message/country`，context=`{golden_path:GP-A, plane:task, inquiry_id}`。
- 提交成功 → 跳转 `/client/tasks?plan=`；失败 message 展示 honest 错误。

### 轨 D · 真桥与附属进程
- GoodJob：本地 `http://127.0.0.1:4188`；若进程在，backend 可配置 `GOODJOB_BASE_URL`（dev `.env` 同步）；未配置时执行器保持 `goodjob_bridge_disabled`/`not_configured` 诚实 failed。
- TradeAI：目标 `:8010`，启动需项目根 `.env.dev` SECRET_KEY + `START_MINIMAL=true`（`C:\Python312\python.exe -m uvicorn app.main:app --port 8010`）；login 仍 410（设计内）。
- 无外部 Key：禁止假 sent/假 PI；桥通则节点可 succeeded 或 bridge_error 诚实 failed。
- `_external` 剥身份改动不强制入主仓 commit；本特性以主仓配置/代码/门禁为准。

### 验证边界
- 后端：pytest hermes/annex 相关；`verify_annex_*`；`orchestration_selfcheck`；drive-chain e2e 脚本节点级摘要。
- 前端：typecheck/lint 或 vitest 相关；路由/登录硬锁 cert 不得破坏。
- Live：8001 派发 GP-A/B + from-intent 内容获客等；任务中心 API 可读节点。

## [S3] Out of Scope
- 生产外部 AI/WhatsApp/邮件 Key 真发；
- DSH 改为每单必经；
- 附属独立登录/管理台复活；
- `_external` 完整入库或 GoodJob Node→Python 重写；
- 远端 push/PR（Finish 阶段由主理人决定）。

## Tasks
- [ ] T1: 驱动链路基线复跑 + 节点状态分类 — acceptance: 脚本/接口跑通，输出各场景节点 status/error 分类表，标出代码洞 vs 配置缺（covers: S2 轨 A）
- [ ] T2: L1 执行器业务闭环修复 — acceptance: content_deep 去掉不可达 except；knowledge 不可用时 degraded；knowledge_seo 场景节点无 5xx/假成功；单测覆盖关键分支（covers: S2 轨 A; depends: T1）
- [ ] T3: GP-B 前端一键触达 — acceptance: 社媒拓客功能域按钮调用 golden-path/outreach，成功跳 /client/tasks?plan=；orchestration.ts 含 goldenPath* API（covers: S2 轨 B）
- [ ] T4: 询盘 Hermes 履约路径 — acceptance: inquiries 详情可提交 GP-A 并跳转任务中心；交互 PI 不回归（covers: S2 轨 C）
- [ ] T5: 本地真桥与进程收口 — acceptance: GoodJob 4188 在时可配 GOODJOB_BASE_URL；TradeAI 8010 可起或明确启动失败原因；未配置路径诚实 failed 有实测（covers: S2 轨 D）
- [ ] T6: 回归与 live 验证 — acceptance: pytest/verify/selfcheck + drive-chain e2e + 关键 API live 结果写入 Report；假成功扫描无新增 HIGH（covers: S2）
- [ ] T7: 独立 Review + Spec Finalize — acceptance: review 通过或 critical 已修；status=delivered + commits 范围（covers: S2; depends: T1–T6）
